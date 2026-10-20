import os
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.app.models import (
    VaultStats,
    MergeRequest,
    EditCellRequest,
    PushValueRequest,
    DomainGroup,
)
from backend.app.parser import parse_and_validate_vault, create_vault_backup
from backend.app.session import session

app = FastAPI(
    title="Bitwarden Duplicate Cleaner",
    description="Privacy-first, local Bitwarden vault deduplication & consolidation tool.",
    version="1.0.0",
)

# Enable CORS for local development (FastAPI backend + Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload")
async def upload_vault(
    file: UploadFile = File(...),
    hasPasskeys: bool = Form(False)
):
    try:
        content_bytes = await file.read()
        raw_content = content_bytes.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    try:
        vault, _ = parse_and_validate_vault(raw_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create safety backup in backups/
    backup_path = create_vault_backup(raw_content)

    # Load into session
    stats = session.load_vault(
        vault=vault,
        user_claimed_passkeys=hasPasskeys,
        backup_path=backup_path
    )

    return {
        "success": True,
        "backupPath": backup_path,
        "stats": stats,
    }


@app.get("/api/stats")
async def get_stats():
    if not session.initialized:
        return {"initialized": False}
    stats = session.get_stats()
    return {
        "initialized": True,
        "stats": stats,
        "canUndo": len(session.undo_stack) > 0,
        "canRedo": len(session.redo_stack) > 0,
    }


@app.get("/api/sidebar")
async def get_sidebar():
    if not session.initialized:
        return {"domains": [], "uniqueCount": 0, "modifiedCount": 0, "deletedCount": 0}
    _, unique_items, domain_summaries = session.get_analysis()
    return {
        "domains": domain_summaries,
        "uniqueCount": len(unique_items),
        "modifiedCount": len(session.modified_ids),
        "deletedCount": len(session.deleted_items),
        "canUndo": len(session.undo_stack) > 0,
        "canRedo": len(session.redo_stack) > 0,
    }


@app.get("/api/duplicates/{domain}")
async def get_duplicates_by_domain(domain: str):
    if not session.initialized:
        raise HTTPException(status_code=400, detail="Vault not loaded")
    domain_group = session.get_domain_group(domain)
    if not domain_group:
        return {"domain": domain, "totalAccounts": 0, "totalItems": 0, "accounts": []}
    return domain_group


@app.get("/api/unique")
async def get_unique_items():
    if not session.initialized:
        return {"items": []}
    _, unique_items, _ = session.get_analysis()
    return {"items": unique_items}


@app.get("/api/modified")
async def get_modified_items():
    if not session.initialized:
        return {"items": []}
    return {"items": session.get_modified_summaries()}


@app.get("/api/deleted")
async def get_deleted_items():
    if not session.initialized:
        return {"items": []}
    return {"items": session.get_deleted_summaries()}


@app.post("/api/merge")
async def merge_account(req: MergeRequest):
    success = session.merge_account(req.domain, req.accountId, req.survivorId)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to merge account items")
    return {"success": True, "stats": session.get_stats()}


@app.post("/api/edit")
async def edit_cell(req: EditCellRequest):
    success = session.edit_field(req.itemId, req.field, req.value)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to edit item field")
    return {"success": True}


@app.post("/api/push")
async def push_value(req: PushValueRequest):
    success = session.push_value(req.domain, req.accountId, req.field, req.sourceItemId)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to push column value")
    return {"success": True}


@app.post("/api/delete/{item_id}")
async def delete_item(item_id: str):
    success = session.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=400, detail="Item not found")
    return {"success": True, "stats": session.get_stats()}


@app.post("/api/restore/{item_id}")
async def restore_item(item_id: str):
    success = session.restore_item(item_id)
    if not success:
        raise HTTPException(status_code=400, detail="Item not in deleted list")
    return {"success": True, "stats": session.get_stats()}


@app.post("/api/undo")
async def undo():
    success = session.undo()
    return {"success": success, "stats": session.get_stats()}


@app.post("/api/redo")
async def redo():
    success = session.redo()
    return {"success": success, "stats": session.get_stats()}


@app.get("/api/export")
async def export_vault():
    if not session.initialized:
        raise HTTPException(status_code=400, detail="No vault currently loaded")
    vault = session.export_vault()
    content = vault.model_dump_json(indent=2, exclude_none=True)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="bitwarden_cleaned_export.json"'
        }
    )


# Serve built frontend if static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
