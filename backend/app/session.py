import copy
from typing import Dict, List, Optional, Set, Any
from backend.app.models import (
    BitwardenVault,
    BitwardenItem,
    BitwardenFolder,
    VaultStats,
    DomainGroup,
    DomainSummary,
    ItemSummary,
)
from backend.app.deduplicator import analyze_vault, item_to_summary
from backend.app.consolidator import merge_into_survivor, push_field_value_to_items


class SessionSnapshot:
    """Snapshot of active and deleted items for undo/redo."""
    def __init__(
        self,
        active_items: Dict[str, BitwardenItem],
        deleted_items: Dict[str, BitwardenItem],
        modified_ids: Set[str],
        description: str = "",
    ):
        self.active_items = {k: v.model_copy(deep=True) for k, v in active_items.items()}
        self.deleted_items = {k: v.model_copy(deep=True) for k, v in deleted_items.items()}
        self.modified_ids = set(modified_ids)
        self.description = description


class VaultSession:
    def __init__(self):
        self.initialized: bool = False
        self.encrypted: bool = False
        self.folders: List[BitwardenFolder] = []
        self.active_items: Dict[str, BitwardenItem] = {}
        self.deleted_items: Dict[str, BitwardenItem] = {}
        self.modified_ids: Set[str] = set()
        self.user_claimed_passkeys: bool = False
        self.backup_path: Optional[str] = None
        self.warning_message: Optional[str] = None

        # Undo / Redo stacks
        self.undo_stack: List[SessionSnapshot] = []
        self.redo_stack: List[SessionSnapshot] = []

    def load_vault(
        self,
        vault: BitwardenVault,
        user_claimed_passkeys: bool,
        backup_path: Optional[str] = None
    ) -> VaultStats:
        self.initialized = True
        self.encrypted = vault.encrypted
        self.folders = [f.model_copy(deep=True) for f in (vault.folders or [])]
        self.active_items = {item.id: item.model_copy(deep=True) for item in vault.items}
        self.deleted_items = {}
        self.modified_ids = set()
        self.user_claimed_passkeys = user_claimed_passkeys
        self.backup_path = backup_path
        self.undo_stack.clear()
        self.redo_stack.clear()

        # Check passkeys
        stats = self.get_stats()
        if user_claimed_passkeys and stats.passkeyTotalCount == 0:
            self.warning_message = (
                "⚠️ Warning: You marked that your vault contains passkeys, "
                "but 0 passkeys were found in this export! If your vault has passkeys, "
                "please ensure you exported as unencrypted JSON from Bitwarden Web Vault."
            )
        else:
            self.warning_message = None

        return self.get_stats()

    def _save_snapshot(self, description: str):
        snapshot = SessionSnapshot(
            self.active_items,
            self.deleted_items,
            self.modified_ids,
            description=description,
        )
        self.undo_stack.append(snapshot)
        self.redo_stack.clear()
        # Cap undo stack at 50 steps
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        # Save current to redo stack
        current = SessionSnapshot(
            self.active_items,
            self.deleted_items,
            self.modified_ids,
            description="redo point",
        )
        self.redo_stack.append(current)

        # Restore from undo
        prev = self.undo_stack.pop()
        self.active_items = {k: v.model_copy(deep=True) for k, v in prev.active_items.items()}
        self.deleted_items = {k: v.model_copy(deep=True) for k, v in prev.deleted_items.items()}
        self.modified_ids = set(prev.modified_ids)
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        # Save current to undo
        current = SessionSnapshot(
            self.active_items,
            self.deleted_items,
            self.modified_ids,
            description="undo point",
        )
        self.undo_stack.append(current)

        # Restore from redo
        next_snap = self.redo_stack.pop()
        self.active_items = {k: v.model_copy(deep=True) for k, v in next_snap.active_items.items()}
        self.deleted_items = {k: v.model_copy(deep=True) for k, v in next_snap.deleted_items.items()}
        self.modified_ids = set(next_snap.modified_ids)
        return True

    def get_analysis(self):
        items_list = list(self.active_items.values())
        return analyze_vault(items_list, self.folders)

    def get_stats(self) -> VaultStats:
        duplicate_domains, unique_items, _ = self.get_analysis()

        total_duplicates = sum(d.totalItems for d in duplicate_domains.values())
        unique_count = len(unique_items)

        passkey_items = 0
        total_passkeys = 0
        for it in self.active_items.values():
            if it.login and it.login.fido2Credentials:
                creds = it.login.fido2Credentials
                if len(creds) > 0:
                    passkey_items += 1
                    total_passkeys += len(creds)

        active_modified_count = len(self.modified_ids.intersection(self.active_items.keys()))

        return VaultStats(
            totalItems=len(self.active_items),
            duplicateCount=total_duplicates,
            uniqueCount=unique_count,
            modifiedCount=active_modified_count,
            deletedCount=len(self.deleted_items),
            passkeyItemCount=passkey_items,
            passkeyTotalCount=total_passkeys,
            hasWarning=self.warning_message is not None,
            warningMessage=self.warning_message,
            userClaimedPasskeys=self.user_claimed_passkeys,
        )

    def get_domain_group(self, domain: str) -> Optional[DomainGroup]:
        dup_domains, _, _ = self.get_analysis()
        return dup_domains.get(domain)

    def merge_account(self, domain: str, account_id: str, survivor_id: str) -> bool:
        dup_domains, _, _ = self.get_analysis()
        group = dup_domains.get(domain)
        if not group:
            return False

        target_acct = next((a for a in group.accounts if a.accountId == account_id), None)
        if not target_acct:
            return False

        survivor_item = self.active_items.get(survivor_id)
        if not survivor_item:
            return False

        # Gather duplicate item objects
        duplicate_items = [
            self.active_items[it_summary.id]
            for it_summary in target_acct.items
            if it_summary.id in self.active_items
        ]

        if len(duplicate_items) <= 1:
            return False

        if survivor_id not in [it.id for it in duplicate_items]:
            return False

        self._save_snapshot(f"Merge into {survivor_item.name} for {domain}")

        # Consolidate survivor
        merged_survivor = merge_into_survivor(survivor_item, duplicate_items)
        self.active_items[survivor_id] = merged_survivor
        self.modified_ids.add(survivor_id)

        # Soft delete the other items
        for dup in duplicate_items:
            if dup.id != survivor_id:
                self.modified_ids.discard(dup.id)
                self.deleted_items[dup.id] = self.active_items.pop(dup.id)

        return True

    def edit_field(self, item_id: str, field: str, value: Any) -> bool:
        item = self.active_items.get(item_id)
        if not item:
            return False

        self._save_snapshot(f"Edit {field} on item {item.name}")

        new_item = item.model_copy(deep=True)
        if field == "name":
            new_item.name = str(value) if value is not None else ""
        elif field == "notes":
            new_item.notes = str(value) if value is not None else None
        elif new_item.login:
            if field == "username":
                new_item.login.username = str(value) if value is not None else None
            elif field == "password":
                new_item.login.password = str(value) if value is not None else None
            elif field == "totp":
                new_item.login.totp = str(value) if value is not None else None
        elif field in ("username", "password", "totp"):
            from backend.app.models import LoginInfo
            new_item.login = LoginInfo(**{field: str(value) if value is not None else None})

        self.active_items[item_id] = new_item
        self.modified_ids.add(item_id)
        return True

    def push_value(self, domain: str, account_id: str, field: str, source_item_id: str) -> bool:
        dup_domains, _, _ = self.get_analysis()
        group = dup_domains.get(domain)
        if not group:
            return False

        target_acct = next((a for a in group.accounts if a.accountId == account_id), None)
        if not target_acct:
            return False

        items_to_update = [
            self.active_items[it.id]
            for it in target_acct.items
            if it.id in self.active_items
        ]

        if source_item_id not in [it.id for it in items_to_update]:
            return False

        self._save_snapshot(f"Push {field} from {source_item_id}")

        updated_items = push_field_value_to_items(items_to_update, source_item_id, field)
        for it in updated_items:
            self.active_items[it.id] = it
            self.modified_ids.add(it.id)

        return True

    def delete_item(self, item_id: str) -> bool:
        if item_id not in self.active_items:
            return False

        item = self.active_items[item_id]
        self._save_snapshot(f"Delete item {item.name}")

        self.deleted_items[item_id] = self.active_items.pop(item_id)
        return True

    def restore_item(self, item_id: str) -> bool:
        if item_id not in self.deleted_items:
            return False

        item = self.deleted_items[item_id]
        self._save_snapshot(f"Restore item {item.name}")

        self.active_items[item_id] = self.deleted_items.pop(item_id)
        return True

    def get_deleted_summaries(self) -> List[ItemSummary]:
        folder_map = {f.id: f.name for f in self.folders if f.id and f.name}
        return [item_to_summary(it, folder_map) for it in self.deleted_items.values()]

    def get_modified_summaries(self) -> List[ItemSummary]:
        folder_map = {f.id: f.name for f in self.folders if f.id and f.name}
        return [
            item_to_summary(self.active_items[mid], folder_map)
            for mid in self.modified_ids
            if mid in self.active_items
        ]

    def export_vault(self) -> BitwardenVault:
        """Constructs a clean Bitwarden export excluding deleted items."""
        return BitwardenVault(
            encrypted=self.encrypted,
            folders=[f.model_copy(deep=True) for f in self.folders],
            items=[item.model_copy(deep=True) for item in self.active_items.values()],
        )


# Global singleton session instance
session = VaultSession()
