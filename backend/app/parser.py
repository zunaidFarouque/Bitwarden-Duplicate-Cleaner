import json
import os
from datetime import datetime
from typing import Dict, Any, Tuple
from backend.app.models import BitwardenVault, BitwardenItem


def parse_and_validate_vault(raw_content: str) -> Tuple[BitwardenVault, Dict[str, Any]]:
    """
    Parses raw JSON string into BitwardenVault and computes initial metadata & passkey stats.
    Returns (vault, stats_summary).
    """
    try:
        data = json.loads(raw_content)
    except Exception as e:
        raise ValueError(f"Invalid JSON file: {str(e)}")

    if not isinstance(data, dict):
        raise ValueError("Invalid Bitwarden export: Root must be a JSON object.")

    if "items" not in data or not isinstance(data["items"], list):
        raise ValueError("Invalid Bitwarden export: Missing 'items' array.")

    # Parse using Pydantic model
    vault = BitwardenVault.model_validate(data)

    # Calculate passkey metrics
    items_with_passkeys = 0
    total_passkeys = 0

    for item in vault.items:
        if item.login and item.login.fido2Credentials:
            creds = item.login.fido2Credentials
            if len(creds) > 0:
                items_with_passkeys += 1
                total_passkeys += len(creds)

    stats = {
        "totalItems": len(vault.items),
        "encrypted": vault.encrypted,
        "folderCount": len(vault.folders or []),
        "passkeyItemCount": items_with_passkeys,
        "passkeyTotalCount": total_passkeys,
    }

    return vault, stats


def create_vault_backup(raw_content: str, backup_dir: str = "backups") -> str:
    """
    Saves an untouched copy of the original uploaded vault with timestamp.
    Returns the absolute path to the backup file.
    """
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bitwarden_original_backup_{timestamp}.json"
    filepath = os.path.join(backup_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(raw_content)

    return os.path.abspath(filepath)
