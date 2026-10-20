from typing import Dict, List, Tuple
from collections import defaultdict
from backend.app.models import (
    BitwardenItem,
    BitwardenFolder,
    ItemSummary,
    AccountGroup,
    DomainGroup,
    DomainSummary,
)
from backend.app.normalizer import get_item_primary_domain, normalize_username


def item_to_summary(
    item: BitwardenItem,
    folder_map: Dict[str, str],
    diff_flags: Dict[str, bool] = None
) -> ItemSummary:
    """Converts a BitwardenItem to a UI-friendly ItemSummary."""
    login = item.login
    uris = [u.uri for u in login.uris if u.uri] if (login and login.uris) else []
    
    passkeys = login.fido2Credentials if (login and login.fido2Credentials) else []
    passkey_details = []
    for p in passkeys:
        passkey_details.append({
            "credentialId": p.credentialId,
            "rpId": p.rpId,
            "userName": p.userName or (login.username if login else None),
            "creationDate": p.creationDate,
            "keyType": p.keyType
        })

    folder_name = folder_map.get(item.folderId) if item.folderId else None

    return ItemSummary(
        id=item.id,
        name=item.name or "(Untitled)",
        type=item.type,
        folderId=item.folderId,
        folderName=folder_name,
        username=login.username if login else None,
        password=login.password if login else None,
        totp=login.totp if login else None,
        notes=item.notes,
        uris=uris,
        passkeyCount=len(passkeys),
        passkeyDetails=passkey_details,
        fieldsCount=len(item.fields) if item.fields else 0,
        revisionDate=item.revisionDate,
        creationDate=item.creationDate,
        diffFlags=diff_flags or {},
    )


def compute_group_diffs(items: List[BitwardenItem]) -> Tuple[List[str], List[Dict[str, bool]]]:
    """
    Computes which fields differ across a group of duplicate items.
    Returns (differing_field_names, list_of_diff_flags_per_item).
    """
    if len(items) <= 1:
        return [], [{}] * len(items)

    diff_fields = set()

    # Compare fields across items
    first = items[0]
    first_login = first.login
    
    first_name = (first.name or "").strip()
    first_user = (first_login.username if first_login else "") or ""
    first_pass = (first_login.password if first_login else "") or ""
    first_totp = (first_login.totp if first_login else "") or ""
    first_notes = (first.notes or "").strip()
    first_uris = set(u.uri for u in first_login.uris if u.uri) if (first_login and first_login.uris) else set()
    first_passkeys = len(first_login.fido2Credentials) if (first_login and first_login.fido2Credentials) else 0

    for item in items[1:]:
        login = item.login
        curr_name = (item.name or "").strip()
        curr_user = (login.username if login else "") or ""
        curr_pass = (login.password if login else "") or ""
        curr_totp = (login.totp if login else "") or ""
        curr_notes = (item.notes or "").strip()
        curr_uris = set(u.uri for u in login.uris if u.uri) if (login and login.uris) else set()
        curr_passkeys = len(login.fido2Credentials) if (login and login.fido2Credentials) else 0

        if curr_name != first_name:
            diff_fields.add("name")
        if curr_user != first_user:
            diff_fields.add("username")
        if curr_pass != first_pass:
            diff_fields.add("password")
        if curr_totp != first_totp:
            diff_fields.add("totp")
        if curr_notes != first_notes:
            diff_fields.add("notes")
        if curr_uris != first_uris:
            diff_fields.add("uris")
        if curr_passkeys != first_passkeys:
            diff_fields.add("passkeys")

    # Generate row flags
    diff_list = sorted(list(diff_fields))
    row_flags = []
    for _ in items:
        row_flags.append({f: True for f in diff_list})

    return diff_list, row_flags


def analyze_vault(
    items: List[BitwardenItem],
    folders: List[BitwardenFolder]
) -> Tuple[Dict[str, DomainGroup], List[ItemSummary], List[DomainSummary]]:
    """
    Groups items by domain and normalized account.
    Returns:
      - duplicate_domains: Dict[domain_name, DomainGroup] (only domains with duplicates)
      - unique_items: List[ItemSummary] (items with zero duplicates)
      - domain_summaries: List[DomainSummary] (for sidebar quick list)
    """
    folder_map = {f.id: f.name for f in folders if f.id and f.name}

    # Grouping structure: domain -> normalized_username -> list of items
    grouped: Dict[str, Dict[str, List[BitwardenItem]]] = defaultdict(lambda: defaultdict(list))

    for item in items:
        # Determine domain
        item_uris = [u.uri for u in item.login.uris if u.uri] if (item.login and item.login.uris) else []
        domain = get_item_primary_domain(item_uris, item.name)

        # Determine normalized username
        raw_user = item.login.username if item.login else None
        norm_user = normalize_username(raw_user, domain)
        if not norm_user:
            # If item has no username, use item name or '(no-username)'
            norm_user = f"_no_username_{item.name.strip().lower()}"

        grouped[domain][norm_user].append(item)

    duplicate_domains: Dict[str, DomainGroup] = {}
    unique_items: List[ItemSummary] = []
    domain_summaries: List[DomainSummary] = []

    for domain, accounts_dict in grouped.items():
        duplicate_account_groups: List[AccountGroup] = []
        domain_total_items = 0
        domain_has_passkeys = False

        for norm_user, item_list in accounts_dict.items():
            if len(item_list) > 1:
                # This account has duplicates!
                diff_fields, row_flags = compute_group_diffs(item_list)
                summaries = [
                    item_to_summary(it, folder_map, diff_flags=row_flags[idx])
                    for idx, it in enumerate(item_list)
                ]
                acct_has_passkey = any(s.passkeyCount > 0 for s in summaries)
                if acct_has_passkey:
                    domain_has_passkeys = True

                display_user = item_list[0].login.username if (item_list[0].login and item_list[0].login.username) else "(No Username)"
                
                account_group = AccountGroup(
                    accountId=norm_user,
                    normalizedUsername=norm_user,
                    displayUsername=display_user,
                    itemCount=len(item_list),
                    hasPasskeys=acct_has_passkey,
                    diffFields=diff_fields,
                    items=summaries,
                )
                duplicate_account_groups.append(account_group)
                domain_total_items += len(item_list)
            else:
                # Unique item
                unique_item = item_list[0]
                summary = item_to_summary(unique_item, folder_map)
                unique_items.append(summary)

        if duplicate_account_groups:
            # Sort accounts by item count desc
            duplicate_account_groups.sort(key=lambda a: a.itemCount, reverse=True)
            domain_group = DomainGroup(
                domain=domain,
                totalAccounts=len(duplicate_account_groups),
                totalItems=domain_total_items,
                hasPasskeys=domain_has_passkeys,
                accounts=duplicate_account_groups,
            )
            duplicate_domains[domain] = domain_group
            domain_summaries.append(DomainSummary(
                domain=domain,
                totalAccounts=len(duplicate_account_groups),
                totalItems=domain_total_items,
                hasPasskeys=domain_has_passkeys,
            ))

    # Sort domain summaries by totalItems descending
    domain_summaries.sort(key=lambda d: d.totalItems, reverse=True)

    return duplicate_domains, unique_items, domain_summaries
