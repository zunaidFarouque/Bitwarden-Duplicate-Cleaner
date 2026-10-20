from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from backend.app.models import (
    BitwardenItem,
    Fido2Credential,
    PasswordHistoryItem,
    CustomField,
    URI,
)


def merge_into_survivor(
    survivor: BitwardenItem,
    duplicates: List[BitwardenItem]
) -> BitwardenItem:
    """
    Intelligently consolidates all duplicates into the survivor item:
    - Unions passkeys (fido2Credentials) without losing any hardware keys
    - Saves differing passwords to survivor's passwordHistory
    - Unions unique URIs
    - Unions custom fields
    - Appends differing notes
    """
    merged_survivor = survivor.model_copy(deep=True)

    if not merged_survivor.login:
        return merged_survivor

    # 1. Consolidate Passkeys (fido2Credentials)
    existing_passkeys = merged_survivor.login.fido2Credentials or []
    seen_cred_ids = set()
    deduped_passkeys: List[Fido2Credential] = []

    for p in existing_passkeys:
        key = p.credentialId or f"{p.rpId}:{p.userHandle}"
        if key not in seen_cred_ids:
            seen_cred_ids.add(key)
            deduped_passkeys.append(p)

    for dup in duplicates:
        if dup.id == survivor.id:
            continue
        if dup.login and dup.login.fido2Credentials:
            for p in dup.login.fido2Credentials:
                key = p.credentialId or f"{p.rpId}:{p.userHandle}"
                if key not in seen_cred_ids:
                    seen_cred_ids.add(key)
                    deduped_passkeys.append(p.model_copy(deep=True))

    merged_survivor.login.fido2Credentials = deduped_passkeys

    # 2. Consolidate Passwords & Password History
    current_pw = merged_survivor.login.password or ""
    pw_history = list(merged_survivor.login.passwordHistory or [])
    known_passwords = {current_pw} | {h.password for h in pw_history if h.password}

    for dup in duplicates:
        if dup.id == survivor.id:
            continue
        dup_pw = (dup.login.password if dup.login else "") or ""
        if dup_pw and dup_pw not in known_passwords:
            known_passwords.add(dup_pw)
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            pw_history.append(PasswordHistoryItem(
                password=dup_pw,
                lastUsedDate=now_iso
            ))
        
        # Also adopt any existing password history from duplicates
        if dup.login and dup.login.passwordHistory:
            for h in dup.login.passwordHistory:
                if h.password and h.password not in known_passwords:
                    known_passwords.add(h.password)
                    pw_history.append(h.model_copy(deep=True))

    merged_survivor.login.passwordHistory = pw_history

    # 3. Consolidate URIs: Append all valid URIs from duplicates
    existing_uris = list(merged_survivor.login.uris or [])
    final_uris = list(existing_uris)

    for dup in duplicates:
        if dup.id == survivor.id:
            continue
        if dup.login and dup.login.uris:
            for u in dup.login.uris:
                if u.uri and u.uri.strip():
                    final_uris.append(u.model_copy(deep=True))

    merged_survivor.login.uris = final_uris

    # 4. Consolidate TOTP
    if not merged_survivor.login.totp:
        for dup in duplicates:
            if dup.id == survivor.id:
                continue
            if dup.login and dup.login.totp:
                merged_survivor.login.totp = dup.login.totp
                break

    # 5. Consolidate Custom Fields
    existing_fields = merged_survivor.fields or []
    existing_field_names = {(f.name or "").strip().lower() for f in existing_fields if f.name}
    final_fields = list(existing_fields)

    for dup in duplicates:
        if dup.id == survivor.id:
            continue
        if dup.fields:
            for f in dup.fields:
                fname = (f.name or "").strip().lower()
                if fname and fname not in existing_field_names:
                    existing_field_names.add(fname)
                    final_fields.append(f.model_copy(deep=True))

    merged_survivor.fields = final_fields

    # 6. Consolidate Notes
    current_notes = (merged_survivor.notes or "").strip()
    notes_parts = [current_notes] if current_notes else []

    for dup in duplicates:
        if dup.id == survivor.id:
            continue
        dup_notes = (dup.notes or "").strip()
        if dup_notes and dup_notes not in current_notes:
            notes_parts.append(f"--- Merged Note from [{dup.name}] ---\n{dup_notes}")

    merged_survivor.notes = "\n\n".join(notes_parts) if notes_parts else None

    # Update revision date
    merged_survivor.revisionDate = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    return merged_survivor


def push_field_value_to_items(
    items: List[BitwardenItem],
    source_item_id: str,
    field: str
) -> List[BitwardenItem]:
    """
    Pushes a specific field's value from source_item to all other items in the group.
    """
    source_item = next((it for it in items if it.id == source_item_id), None)
    if not source_item:
        return items

    target_value = None
    if field == "name":
        target_value = source_item.name
    elif field == "notes":
        target_value = source_item.notes
    elif source_item.login:
        if field == "username":
            target_value = source_item.login.username
        elif field == "password":
            target_value = source_item.login.password
        elif field == "totp":
            target_value = source_item.login.totp

    updated_items = []
    for it in items:
        new_it = it.model_copy(deep=True)
        if field == "name":
            new_it.name = target_value
        elif field == "notes":
            new_it.notes = target_value
        elif new_it.login:
            if field == "username":
                new_it.login.username = target_value
            elif field == "password":
                new_it.login.password = target_value
            elif field == "totp":
                new_it.login.totp = target_value
        new_it.revisionDate = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        updated_items.append(new_it)

    return updated_items
