import json
import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.session import session


class PermutationTestBase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def assert_stats_integrity(self, expected_initial_total=None):
        """Verifies mathematical consistency of vault statistics and sidebar across all states."""
        stats_resp = self.client.get("/api/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats_data = stats_resp.json()
        self.assertTrue(stats_data["initialized"])
        stats = stats_data["stats"]

        # Invariant 1: totalItems == duplicateCount + uniqueCount
        self.assertEqual(
            stats["totalItems"],
            stats["duplicateCount"] + stats["uniqueCount"],
            f"Invariant violation: totalItems ({stats['totalItems']}) != duplicateCount ({stats['duplicateCount']}) + uniqueCount ({stats['uniqueCount']})"
        )

        # Invariant 2: totalItems + deletedCount == expected_initial_total
        if expected_initial_total is not None:
            self.assertEqual(
                stats["totalItems"] + stats["deletedCount"],
                expected_initial_total,
                f"Invariant violation: totalItems ({stats['totalItems']}) + deletedCount ({stats['deletedCount']}) != initial ({expected_initial_total})"
            )

        # Invariant 3: Sidebar consistency
        sidebar_resp = self.client.get("/api/sidebar")
        self.assertEqual(sidebar_resp.status_code, 200)
        sidebar = sidebar_resp.json()

        self.assertEqual(sidebar["uniqueCount"], stats["uniqueCount"])
        self.assertEqual(sidebar["deletedCount"], stats["deletedCount"])
        self.assertEqual(sidebar["modifiedCount"], stats["modifiedCount"])
        self.assertEqual(sidebar["canUndo"], stats_data["canUndo"])
        self.assertEqual(sidebar["canRedo"], stats_data["canRedo"])

        # Invariant 4: Passkey total matches active items
        actual_passkeys = sum(
            len(it.login.fido2Credentials)
            for it in session.active_items.values()
            if it.login and it.login.fido2Credentials
        )
        self.assertEqual(stats["passkeyTotalCount"], actual_passkeys)

        # Invariant 5: Modified count matches active modified IDs
        active_modified = len(session.modified_ids.intersection(session.active_items.keys()))
        self.assertEqual(stats["modifiedCount"], active_modified)

        # Invariant 6: Export count matches total active items
        export_resp = self.client.get("/api/export")
        self.assertEqual(export_resp.status_code, 200)
        exported = export_resp.json()
        self.assertEqual(len(exported["items"]), stats["totalItems"])
        exported_ids = {it["id"] for it in exported["items"]}
        for deleted_id in session.deleted_items:
            self.assertNotIn(deleted_id, exported_ids)


class TestUndoRedoStressChains(PermutationTestBase):
    """
    1. Undo / Redo Stress Chains:
       - 10+ sequential actions: edit -> push -> merge -> delete -> restore -> edit -> push -> merge...
       - Stepping backward 5 undos, performing a new action (checking redo stack is properly cleared)
       - Stepping forward all redos
       - Reverting all the way back to initial state
    """

    def test_complex_stress_chain_and_branching(self):
        vault_data = {
            "encrypted": False,
            "folders": [{"id": "f1", "name": "Work"}],
            "items": [
                # Account A: 3 duplicates under acme.com
                {
                    "id": "acme-1",
                    "type": 1,
                    "name": "Acme Portal 1",
                    "folderId": "f1",
                    "notes": "Acme Note 1",
                    "login": {
                        "uris": [{"uri": "https://acme.com"}],
                        "username": "admin@acme.com",
                        "password": "InitialPassword1",
                        "totp": "otpauth://totp/Acme:admin?secret=JBSWY3DPEHPK3PXP",
                        "fido2Credentials": [{"credentialId": "cred-acme-1", "rpId": "acme.com"}]
                    }
                },
                {
                    "id": "acme-2",
                    "type": 1,
                    "name": "Acme Portal 2",
                    "folderId": "f1",
                    "notes": "Acme Note 2",
                    "login": {
                        "uris": [{"uri": "https://acme.com/login"}],
                        "username": "admin@acme.com",
                        "password": "InitialPassword2",
                        "totp": None,
                        "fido2Credentials": []
                    }
                },
                {
                    "id": "acme-3",
                    "type": 1,
                    "name": "Acme Portal 3",
                    "folderId": "f1",
                    "notes": "Acme Note 3",
                    "login": {
                        "uris": [{"uri": "https://auth.acme.com"}],
                        "username": "admin@acme.com",
                        "password": "InitialPassword3",
                        "totp": None,
                        "fido2Credentials": []
                    }
                },
                # Account B: 3 duplicates under beta.org
                {
                    "id": "beta-1",
                    "type": 1,
                    "name": "Beta Item 1",
                    "folderId": "f1",
                    "notes": "Beta Note 1",
                    "login": {
                        "uris": [{"uri": "https://beta.org"}],
                        "username": "user@beta.org",
                        "password": "BetaPass1",
                        "totp": None,
                        "fido2Credentials": []
                    }
                },
                {
                    "id": "beta-2",
                    "type": 1,
                    "name": "Beta Item 2",
                    "folderId": "f1",
                    "notes": "Beta Note 2",
                    "login": {
                        "uris": [{"uri": "https://beta.org/login"}],
                        "username": "user@beta.org",
                        "password": "BetaPass2",
                        "totp": None,
                        "fido2Credentials": []
                    }
                },
                {
                    "id": "beta-3",
                    "type": 1,
                    "name": "Beta Item 3",
                    "folderId": "f1",
                    "notes": "Beta Note 3",
                    "login": {
                        "uris": [{"uri": "https://beta.org/auth"}],
                        "username": "user@beta.org",
                        "password": "BetaPass3",
                        "totp": None,
                        "fido2Credentials": []
                    }
                },
                # Account C: 2 duplicates under corp.com
                {
                    "id": "corp-1",
                    "type": 1,
                    "name": "Corp 1",
                    "folderId": "f1",
                    "notes": "Corp Note 1",
                    "login": {
                        "uris": [{"uri": "https://corp.com"}],
                        "username": "staff@corp.com",
                        "password": "CorpPass1",
                        "totp": None,
                        "fido2Credentials": []
                    }
                },
                {
                    "id": "corp-2",
                    "type": 1,
                    "name": "Corp 2",
                    "folderId": "f1",
                    "notes": "Corp Note 2",
                    "login": {
                        "uris": [{"uri": "https://corp.com"}],
                        "username": "staff@corp.com",
                        "password": "CorpPass2",
                        "totp": None,
                        "fido2Credentials": []
                    }
                },
            ]
        }

        # Upload
        up_resp = self.client.post(
            "/api/upload",
            files={"file": ("vault.json", json.dumps(vault_data).encode("utf-8"), "application/json")},
            data={"hasPasskeys": "true"}
        )
        self.assertEqual(up_resp.status_code, 200)
        self.assert_stats_integrity(expected_initial_total=8)

        # Snapshot initial values
        initial_names = {k: v.name for k, v in session.active_items.items()}
        initial_passwords = {k: v.login.password for k, v in session.active_items.items()}
        initial_active_ids = set(session.active_items.keys())

        # Perform 12 sequential actions:
        # Action 1: edit acme-1 name
        resp = self.client.post("/api/edit", json={"itemId": "acme-1", "field": "name", "value": "Acme Master"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(session.active_items["acme-1"].name, "Acme Master")
        self.assert_stats_integrity(8)

        # Action 2: push name from acme-1
        resp = self.client.post("/api/push", json={
            "domain": "acme.com",
            "accountId": "admin@acme.com",
            "field": "name",
            "sourceItemId": "acme-1"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(session.active_items["acme-2"].name, "Acme Master")
        self.assertEqual(session.active_items["acme-3"].name, "Acme Master")
        self.assert_stats_integrity(8)

        # Action 3: edit acme-2 password
        resp = self.client.post("/api/edit", json={"itemId": "acme-2", "field": "password", "value": "NewStrongPass999!"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(session.active_items["acme-2"].login.password, "NewStrongPass999!")
        self.assert_stats_integrity(8)

        # Action 4: push password from acme-2
        resp = self.client.post("/api/push", json={
            "domain": "acme.com",
            "accountId": "admin@acme.com",
            "field": "password",
            "sourceItemId": "acme-2"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(session.active_items["acme-1"].login.password, "NewStrongPass999!")
        self.assertEqual(session.active_items["acme-3"].login.password, "NewStrongPass999!")
        self.assert_stats_integrity(8)

        # Action 5: delete acme-3
        resp = self.client.post("/api/delete/acme-3")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("acme-3", session.active_items)
        self.assertIn("acme-3", session.deleted_items)
        self.assert_stats_integrity(8)

        # Action 6: restore acme-3
        resp = self.client.post("/api/restore/acme-3")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("acme-3", session.active_items)
        self.assertNotIn("acme-3", session.deleted_items)
        self.assert_stats_integrity(8)

        # Action 7: edit beta-1 notes
        resp = self.client.post("/api/edit", json={"itemId": "beta-1", "field": "notes", "value": "Updated Beta Note"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(session.active_items["beta-1"].notes, "Updated Beta Note")
        self.assert_stats_integrity(8)

        # Action 8: merge beta account into survivor beta-1
        resp = self.client.post("/api/merge", json={
            "domain": "beta.org",
            "accountId": "user@beta.org",
            "survivorId": "beta-1"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("beta-1", session.active_items)
        self.assertNotIn("beta-2", session.active_items)
        self.assertNotIn("beta-3", session.active_items)
        self.assertIn("beta-2", session.deleted_items)
        self.assertIn("beta-3", session.deleted_items)
        self.assert_stats_integrity(8)

        # Action 9: edit corp-1 totp
        resp = self.client.post("/api/edit", json={
            "itemId": "corp-1",
            "field": "totp",
            "value": "otpauth://totp/Corp:staff?secret=HXDMVJECJJWSRB3H"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(session.active_items["corp-1"].login.totp, "otpauth://totp/Corp:staff?secret=HXDMVJECJJWSRB3H")
        self.assert_stats_integrity(8)

        # Action 10: delete corp-2
        resp = self.client.post("/api/delete/corp-2")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("corp-2", session.active_items)
        self.assert_stats_integrity(8)

        # Action 11: restore corp-2
        resp = self.client.post("/api/restore/corp-2")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("corp-2", session.active_items)
        self.assert_stats_integrity(8)

        # Action 12: push totp from corp-1 to corp-2
        resp = self.client.post("/api/push", json={
            "domain": "corp.com",
            "accountId": "staff@corp.com",
            "field": "totp",
            "sourceItemId": "corp-1"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(session.active_items["corp-2"].login.totp, "otpauth://totp/Corp:staff?secret=HXDMVJECJJWSRB3H")
        self.assert_stats_integrity(8)

        self.assertEqual(len(session.undo_stack), 12)
        self.assertEqual(len(session.redo_stack), 0)

        # --- STEP BACKWARD 5 UNDOS ---
        for i in range(5):
            undo_resp = self.client.post("/api/undo")
            self.assertEqual(undo_resp.status_code, 200)
            self.assertTrue(undo_resp.json()["success"])
            self.assert_stats_integrity(8)

        self.assertEqual(len(session.undo_stack), 7)
        self.assertEqual(len(session.redo_stack), 5)

        # Verify state after 5 undos:
        # Action 12, 11, 10, 9, 8 were undone:
        # beta-2 and beta-3 should now be restored back to active items!
        self.assertIn("beta-2", session.active_items)
        self.assertIn("beta-3", session.active_items)
        # corp-1 totp should be None again
        self.assertIsNone(session.active_items["corp-1"].login.totp)

        # --- PERFORM A NEW ACTION (BRANCHING) ---
        branch_resp = self.client.post("/api/edit", json={
            "itemId": "acme-1",
            "field": "name",
            "value": "Branched Action Acme"
        })
        self.assertEqual(branch_resp.status_code, 200)
        self.assertEqual(session.active_items["acme-1"].name, "Branched Action Acme")

        # Verify redo stack is completely cleared!
        self.assertEqual(len(session.redo_stack), 0)
        redo_fail = self.client.post("/api/redo")
        self.assertEqual(redo_fail.status_code, 200)
        self.assertFalse(redo_fail.json()["success"])
        self.assert_stats_integrity(8)

        # --- STEPPING FORWARD ALL REDOS TEST ---
        # First undo 3 actions
        for _ in range(3):
            self.client.post("/api/undo")
        self.assertEqual(len(session.redo_stack), 3)

        # Now step forward all 3 redos
        for _ in range(3):
            redo_ok = self.client.post("/api/redo")
            self.assertEqual(redo_ok.status_code, 200)
            self.assertTrue(redo_ok.json()["success"])
            self.assert_stats_integrity(8)

        self.assertEqual(len(session.redo_stack), 0)
        self.assertEqual(session.active_items["acme-1"].name, "Branched Action Acme")

        # --- REVERT ALL THE WAY BACK TO INITIAL STATE ---
        while len(session.undo_stack) > 0:
            undo_res = self.client.post("/api/undo")
            self.assertEqual(undo_res.status_code, 200)
            self.assertTrue(undo_res.json()["success"])
            self.assert_stats_integrity(8)

        # Check stack is exhausted
        self.assertEqual(len(session.undo_stack), 0)
        undo_exhausted = self.client.post("/api/undo")
        self.assertFalse(undo_exhausted.json()["success"])

        # Check vault is identical to initial loaded state
        self.assertEqual(set(session.active_items.keys()), initial_active_ids)
        self.assertEqual(len(session.deleted_items), 0)
        self.assertEqual(len(session.modified_ids), 0)
        for item_id, expected_name in initial_names.items():
            self.assertEqual(session.active_items[item_id].name, expected_name)
        for item_id, expected_pw in initial_passwords.items():
            self.assertEqual(session.active_items[item_id].login.password, expected_pw)
        self.assert_stats_integrity(8)


class TestMultiAccountMultiDomain(PermutationTestBase):
    """
    2. Multi-Account and Multi-Domain Edge Cases:
       - Vault with 5 different domains, each having 2 to 4 accounts, each account having 2 to 3 duplicates
       - Merging one account under Domain A does not affect other accounts under Domain A or accounts under Domain B
       - Deleting one duplicate row vs deleting the survivor
       - Restoring a deleted row from Trash: verify it reappears properly in the duplicate group / domain group
    """

    def setUp(self):
        super().setUp()
        # Build 5 domains with 2-4 accounts each, 2-3 duplicates per account:
        # Domain 1: google.com (3 accounts: a1=3, a2=2, a3=2 duplicates) -> 7 items
        # Domain 2: github.com (2 accounts: a1=2, a2=3 duplicates) -> 5 items
        # Domain 3: amazon.com (4 accounts: a1=2, a2=2, a3=2, a4=2 duplicates) -> 8 items
        # Domain 4: microsoft.com (2 accounts: a1=3, a2=2 duplicates) -> 5 items
        # Domain 5: dropbox.com (3 accounts: a1=2, a2=2, a3=2 duplicates) -> 6 items
        # Plus 2 unique items -> 2 items
        # Total items = 7 + 5 + 8 + 5 + 6 + 2 = 33 items.
        self.items = []

        # Domain 1: google.com
        for i in range(1, 4):
            self.items.append({
                "id": f"g_acct1_{i}",
                "name": f"Google Work {i}",
                "login": {
                    "uris": [{"uri": "https://accounts.google.com"}],
                    "username": "alice@gmail.com",
                    "password": f"PassG1_{i}",
                    "fido2Credentials": [{"credentialId": "passkey-g1", "rpId": "google.com"}] if i == 1 else []
                }
            })
        for i in range(1, 3):
            self.items.append({
                "id": f"g_acct2_{i}",
                "name": f"Google Personal {i}",
                "login": {
                    "uris": [{"uri": "https://accounts.google.com"}],
                    "username": "bob@gmail.com",
                    "password": f"PassG2_{i}"
                }
            })
        for i in range(1, 3):
            self.items.append({
                "id": f"g_acct3_{i}",
                "name": f"Google Dev {i}",
                "login": {
                    "uris": [{"uri": "https://mail.google.com"}],
                    "username": "charlie@gmail.com",
                    "password": f"PassG3_{i}"
                }
            })

        # Domain 2: github.com
        for i in range(1, 3):
            self.items.append({
                "id": f"gh_acct1_{i}",
                "name": f"GitHub Org {i}",
                "login": {
                    "uris": [{"uri": "https://github.com"}],
                    "username": "gh_octo",
                    "password": f"PassGH1_{i}"
                }
            })
        for i in range(1, 4):
            self.items.append({
                "id": f"gh_acct2_{i}",
                "name": f"GitHub Personal {i}",
                "login": {
                    "uris": [{"uri": "https://github.com/login"}],
                    "username": "gh_coder",
                    "password": f"PassGH2_{i}",
                    "fido2Credentials": [{"credentialId": "passkey-gh2", "rpId": "github.com"}] if i == 2 else []
                }
            })

        # Domain 3: amazon.com (4 accounts)
        for a_idx, acct_name in enumerate(["buyer1", "buyer2", "buyer3", "buyer4"], start=1):
            for i in range(1, 3):
                self.items.append({
                    "id": f"amz_a{a_idx}_{i}",
                    "name": f"Amazon {acct_name} {i}",
                    "login": {
                        "uris": [{"uri": "https://amazon.com"}],
                        "username": f"{acct_name}@amazon.com",
                        "password": f"PassAmz_{a_idx}_{i}"
                    }
                })

        # Domain 4: microsoft.com (2 accounts: 3 duplicates and 2 duplicates)
        for i in range(1, 4):
            self.items.append({
                "id": f"ms_acct1_{i}",
                "name": f"MS Azure {i}",
                "login": {
                    "uris": [{"uri": "https://portal.microsoft.com"}],
                    "username": "dev@microsoft.com",
                    "password": f"PassMS1_{i}"
                }
            })
        for i in range(1, 3):
            self.items.append({
                "id": f"ms_acct2_{i}",
                "name": f"MS Office {i}",
                "login": {
                    "uris": [{"uri": "https://login.microsoft.com"}],
                    "username": "ops@microsoft.com",
                    "password": f"PassMS2_{i}"
                }
            })

        # Domain 5: dropbox.com (3 accounts: 2, 2, 2)
        for a_idx, acct_name in enumerate(["dp_user1", "dp_user2", "dp_user3"], start=1):
            for i in range(1, 3):
                self.items.append({
                    "id": f"dp_a{a_idx}_{i}",
                    "name": f"Dropbox {acct_name} {i}",
                    "login": {
                        "uris": [{"uri": "https://dropbox.com"}],
                        "username": f"{acct_name}@dropbox.com",
                        "password": f"PassDP_{a_idx}_{i}"
                    }
                })

        # 2 Unique Items
        self.items.append({
            "id": "unique-slack",
            "name": "Slack Unique",
            "login": {"uris": [{"uri": "https://slack.com"}], "username": "slackuser", "password": "SlackPassword!"}
        })
        self.items.append({
            "id": "unique-netflix",
            "name": "Netflix Unique",
            "login": {"uris": [{"uri": "https://netflix.com"}], "username": "streamer", "password": "NetflixPassword!"}
        })

        self.vault = {
            "encrypted": False,
            "folders": [{"id": "fld-main", "name": "Main"}],
            "items": self.items
        }

        # Upload
        up = self.client.post(
            "/api/upload",
            files={"file": ("vault.json", json.dumps(self.vault).encode("utf-8"), "application/json")},
            data={"hasPasskeys": "true"}
        )
        self.assertEqual(up.status_code, 200)

    def test_multi_domain_isolation_and_stats(self):
        self.assert_stats_integrity(expected_initial_total=33)

        sidebar_resp = self.client.get("/api/sidebar")
        domains_list = [d["domain"] for d in sidebar_resp.json()["domains"]]
        self.assertEqual(len(domains_list), 5)
        self.assertIn("google.com", domains_list)
        self.assertIn("github.com", domains_list)
        self.assertIn("amazon.com", domains_list)
        self.assertIn("microsoft.com", domains_list)
        self.assertIn("dropbox.com", domains_list)

        # Snapshot github and amazon state before merging google
        gh_before = self.client.get("/api/duplicates/github.com").json()
        amz_before = self.client.get("/api/duplicates/amazon.com").json()
        g_before = self.client.get("/api/duplicates/google.com").json()

        # Merge account 1 in google.com (alice@gmail.com into g_acct1_1)
        merge_resp = self.client.post("/api/merge", json={
            "domain": "google.com",
            "accountId": "alice@gmail.com",
            "survivorId": "g_acct1_1"
        })
        self.assertEqual(merge_resp.status_code, 200)
        self.assert_stats_integrity(33)

        # Verify Google Domain State:
        # alice@gmail.com is consolidated: g_acct1_2 and g_acct1_3 are deleted!
        self.assertIn("g_acct1_1", session.active_items)
        self.assertIn("g_acct1_2", session.deleted_items)
        self.assertIn("g_acct1_3", session.deleted_items)

        # alice is no longer in duplicate accounts of google.com
        g_after = self.client.get("/api/duplicates/google.com").json()
        acct_ids = [a["accountId"] for a in g_after["accounts"]]
        self.assertNotIn("alice@gmail.com", acct_ids)
        # bob and charlie are STILL in google.com duplicate accounts with unchanged items
        self.assertIn("bob@gmail.com", acct_ids)
        self.assertIn("charlie@gmail.com", acct_ids)
        bob_items = next(a["items"] for a in g_after["accounts"] if a["accountId"] == "bob@gmail.com")
        self.assertEqual(len(bob_items), 2)

        # Verify Other Domains are 100% UNTOUCHED
        gh_after = self.client.get("/api/duplicates/github.com").json()
        amz_after = self.client.get("/api/duplicates/amazon.com").json()
        self.assertEqual(gh_before, gh_after)
        self.assertEqual(amz_before, amz_after)

    def test_delete_duplicate_row_vs_survivor_and_restore(self):
        # In github.com, account gh_coder has 3 duplicates: gh_acct2_1, gh_acct2_2, gh_acct2_3
        # gh_acct2_2 has the passkey
        gh_group = self.client.get("/api/duplicates/github.com").json()
        coder_acct = next(a for a in gh_group["accounts"] if a["accountId"] == "gh_coder")
        self.assertEqual(coder_acct["itemCount"], 3)

        # 1. Delete one duplicate row (gh_acct2_3)
        del_resp = self.client.post("/api/delete/gh_acct2_3")
        self.assertEqual(del_resp.status_code, 200)
        self.assert_stats_integrity(33)

        gh_group = self.client.get("/api/duplicates/github.com").json()
        coder_acct = next(a for a in gh_group["accounts"] if a["accountId"] == "gh_coder")
        self.assertEqual(coder_acct["itemCount"], 2)
        coder_item_ids = [it["id"] for it in coder_acct["items"]]
        self.assertEqual(set(coder_item_ids), {"gh_acct2_1", "gh_acct2_2"})

        # 2. Delete another duplicate row (gh_acct2_1)
        # Now only gh_acct2_2 remains! It is no longer a duplicate -> becomes UNIQUE!
        del_resp2 = self.client.post("/api/delete/gh_acct2_1")
        self.assertEqual(del_resp2.status_code, 200)
        self.assert_stats_integrity(33)

        gh_group = self.client.get("/api/duplicates/github.com").json()
        coder_accts = [a for a in gh_group["accounts"] if a["accountId"] == "gh_coder"]
        self.assertEqual(len(coder_accts), 0, "Account with 1 item should drop out of duplicate groups")

        # gh_acct2_2 should now appear in /api/unique
        unique_resp = self.client.get("/api/unique")
        unique_ids = [u["id"] for u in unique_resp.json()["items"]]
        self.assertIn("gh_acct2_2", unique_ids)

        # 3. Restore gh_acct2_1 from Trash
        res_resp = self.client.post("/api/restore/gh_acct2_1")
        self.assertEqual(res_resp.status_code, 200)
        self.assert_stats_integrity(33)

        # gh_coder should automatically reappear in duplicate groups with 2 items!
        gh_group = self.client.get("/api/duplicates/github.com").json()
        coder_acct = next(a for a in gh_group["accounts"] if a["accountId"] == "gh_coder")
        self.assertEqual(coder_acct["itemCount"], 2)
        self.assertNotIn("gh_acct2_2", [u["id"] for u in self.client.get("/api/unique").json()["items"]])

        # 4. Now restore gh_acct2_3 as well -> back to 3 items
        self.client.post("/api/restore/gh_acct2_3")
        self.assert_stats_integrity(33)

        # 5. Delete the survivor/passkey-holding item (gh_acct2_2)
        del_surv = self.client.post("/api/delete/gh_acct2_2")
        self.assertEqual(del_surv.status_code, 200)
        self.assert_stats_integrity(33)

        # Remaining items gh_acct2_1 and gh_acct2_3 still form a valid duplicate group
        gh_group = self.client.get("/api/duplicates/github.com").json()
        coder_acct = next(a for a in gh_group["accounts"] if a["accountId"] == "gh_coder")
        self.assertEqual(coder_acct["itemCount"], 2)
        self.assertFalse(coder_acct["hasPasskeys"])  # Passkey was on gh_acct2_2 which is currently deleted!

        # Restore gh_acct2_2 back
        self.client.post("/api/restore/gh_acct2_2")
        self.assert_stats_integrity(33)
        gh_group = self.client.get("/api/duplicates/github.com").json()
        coder_acct = next(a for a in gh_group["accounts"] if a["accountId"] == "gh_coder")
        self.assertTrue(coder_acct["hasPasskeys"])


class TestPushColumnValueCombinations(PermutationTestBase):
    """
    3. Push Column Value Combinations:
       - Push name, username, password, totp, notes across 4 duplicate items
       - Verify only that field changes while passkeys and other fields remain intact
    """

    def setUp(self):
        super().setUp()
        self.vault = {
            "encrypted": False,
            "folders": [{"id": "fld-1", "name": "Main"}],
            "items": [
                {
                    "id": "neo-1",
                    "name": "Google Item Alpha",
                    "notes": "Alpha Note 1",
                    "login": {
                        "uris": [{"uri": "https://accounts.google.com"}],
                        "username": "neo@gmail.com",
                        "password": "PasswordAlpha!111",
                        "totp": "otpauth://totp/Google:neo?secret=JBSWY3DPEHPK3PXP",
                        "fido2Credentials": [
                            {"credentialId": "passkey-neo-1", "rpId": "google.com", "creationDate": "2026-01-01T00:00:00Z"}
                        ]
                    }
                },
                {
                    "id": "neo-2",
                    "name": "Google Item Beta",
                    "notes": "Beta Note 2",
                    "login": {
                        "uris": [{"uri": "https://mail.google.com"}],
                        "username": "neo",
                        "password": "PasswordBeta!222",
                        "totp": "otpauth://totp/Google:neo2?secret=HXDMVJECJJWSRB3H",
                        "fido2Credentials": [
                            {"credentialId": "passkey-neo-2", "rpId": "google.com", "creationDate": "2026-02-02T00:00:00Z"}
                        ]
                    }
                },
                {
                    "id": "neo-3",
                    "name": "Google Item Gamma",
                    "notes": "Gamma Note 3",
                    "login": {
                        "uris": [{"uri": "https://google.com"}],
                        "username": "neo+work@gmail.com",
                        "password": "PasswordGamma!333",
                        "totp": None,
                        "fido2Credentials": []
                    }
                },
                {
                    "id": "neo-4",
                    "name": "Google Item Delta",
                    "notes": None,
                    "login": {
                        "uris": [{"uri": "https://myaccount.google.com"}],
                        "username": "neo@gmail.com",
                        "password": "PasswordDelta!444",
                        "totp": None,
                        "fido2Credentials": []
                    }
                }
            ]
        }

        up = self.client.post(
            "/api/upload",
            files={"file": ("vault.json", json.dumps(self.vault).encode("utf-8"), "application/json")},
            data={"hasPasskeys": "true"}
        )
        self.assertEqual(up.status_code, 200)

    def test_push_each_field_preserves_other_fields_and_passkeys(self):
        self.assert_stats_integrity(4)

        # 1. PUSH NAME from neo-1 ("Google Item Alpha")
        resp = self.client.post("/api/push", json={
            "domain": "google.com",
            "accountId": "neo@gmail.com",
            "field": "name",
            "sourceItemId": "neo-1"
        })
        self.assertEqual(resp.status_code, 200)
        self.assert_stats_integrity(4)

        # Verify only name changed to "Google Item Alpha"
        for item_id in ["neo-1", "neo-2", "neo-3", "neo-4"]:
            item = session.active_items[item_id]
            self.assertEqual(item.name, "Google Item Alpha")

        # Verify passwords, totps, notes, passkeys remain UNTOUCHED
        self.assertEqual(session.active_items["neo-1"].login.password, "PasswordAlpha!111")
        self.assertEqual(session.active_items["neo-2"].login.password, "PasswordBeta!222")
        self.assertEqual(session.active_items["neo-3"].login.password, "PasswordGamma!333")
        self.assertEqual(session.active_items["neo-4"].login.password, "PasswordDelta!444")

        self.assertEqual(len(session.active_items["neo-1"].login.fido2Credentials), 1)
        self.assertEqual(session.active_items["neo-1"].login.fido2Credentials[0].credentialId, "passkey-neo-1")
        self.assertEqual(len(session.active_items["neo-2"].login.fido2Credentials), 1)
        self.assertEqual(session.active_items["neo-2"].login.fido2Credentials[0].credentialId, "passkey-neo-2")
        self.assertEqual(len(session.active_items["neo-3"].login.fido2Credentials), 0)

        # 2. PUSH PASSWORD from neo-2 ("PasswordBeta!222")
        resp = self.client.post("/api/push", json={
            "domain": "google.com",
            "accountId": "neo@gmail.com",
            "field": "password",
            "sourceItemId": "neo-2"
        })
        self.assertEqual(resp.status_code, 200)
        self.assert_stats_integrity(4)

        for item_id in ["neo-1", "neo-2", "neo-3", "neo-4"]:
            self.assertEqual(session.active_items[item_id].login.password, "PasswordBeta!222")
            # Name and passkeys still intact
            self.assertEqual(session.active_items[item_id].name, "Google Item Alpha")
        self.assertEqual(len(session.active_items["neo-1"].login.fido2Credentials), 1)
        self.assertEqual(len(session.active_items["neo-2"].login.fido2Credentials), 1)

        # 3. PUSH TOTP from neo-1 ("otpauth://totp/Google:neo?secret=JBSWY3DPEHPK3PXP")
        resp = self.client.post("/api/push", json={
            "domain": "google.com",
            "accountId": "neo@gmail.com",
            "field": "totp",
            "sourceItemId": "neo-1"
        })
        self.assertEqual(resp.status_code, 200)
        self.assert_stats_integrity(4)

        for item_id in ["neo-1", "neo-2", "neo-3", "neo-4"]:
            self.assertIn("JBSWY3DPEHPK3PXP", session.active_items[item_id].login.totp)
            self.assertEqual(session.active_items[item_id].login.password, "PasswordBeta!222")

        # 4. PUSH NOTES from neo-1 ("Alpha Note 1")
        resp = self.client.post("/api/push", json={
            "domain": "google.com",
            "accountId": "neo@gmail.com",
            "field": "notes",
            "sourceItemId": "neo-1"
        })
        self.assertEqual(resp.status_code, 200)
        self.assert_stats_integrity(4)

        for item_id in ["neo-1", "neo-2", "neo-3", "neo-4"]:
            self.assertEqual(session.active_items[item_id].notes, "Alpha Note 1")

        # 5. PUSH USERNAME from neo-1 ("neo@gmail.com") across the group
        # Initially, neo-2 was "neo" and neo-3 was "neo+work@gmail.com"
        self.assertEqual(session.active_items["neo-2"].login.username, "neo")
        self.assertEqual(session.active_items["neo-3"].login.username, "neo+work@gmail.com")

        push_user_resp = self.client.post("/api/push", json={
            "domain": "google.com",
            "accountId": "neo@gmail.com",
            "field": "username",
            "sourceItemId": "neo-1"
        })
        self.assertEqual(push_user_resp.status_code, 200)
        self.assert_stats_integrity(4)

        for item_id in ["neo-1", "neo-2", "neo-3", "neo-4"]:
            self.assertEqual(session.active_items[item_id].login.username, "neo@gmail.com")
            # All passkeys, notes, passwords, totp still completely intact!
            self.assertEqual(session.active_items[item_id].notes, "Alpha Note 1")
            self.assertEqual(session.active_items[item_id].login.password, "PasswordBeta!222")

        self.assertEqual(len(session.active_items["neo-1"].login.fido2Credentials), 1)
        self.assertEqual(session.active_items["neo-1"].login.fido2Credentials[0].credentialId, "passkey-neo-1")
        self.assertEqual(len(session.active_items["neo-2"].login.fido2Credentials), 1)
        self.assertEqual(session.active_items["neo-2"].login.fido2Credentials[0].credentialId, "passkey-neo-2")


class TestRobustnessAndErrorHandling(PermutationTestBase):
    """
    4. Robustness & Error Handling:
       - Corrupted JSON upload (malformed JSON, missing items key, null fields)
       - Merging with non-existent survivorId, non-existent domain, non-existent accountId
       - Editing non-existent itemId
       - Restoring an itemId not in deleted items
       - Deleting an already deleted itemId
    """

    def test_corrupted_json_upload_cases(self):
        # 1. Malformed JSON syntax
        resp = self.client.post(
            "/api/upload",
            files={"file": ("corrupted.json", b"{malformed json, missing quote", "application/json")},
            data={"hasPasskeys": "false"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid JSON file", resp.json()["detail"])

        # 2. Non-dict root
        resp = self.client.post(
            "/api/upload",
            files={"file": ("list_root.json", b"[1, 2, 3]", "application/json")},
            data={"hasPasskeys": "false"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Root must be a JSON object", resp.json()["detail"])

        # 3. Missing items key
        resp = self.client.post(
            "/api/upload",
            files={"file": ("no_items.json", b'{"folders": []}', "application/json")},
            data={"hasPasskeys": "false"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Missing 'items' array", resp.json()["detail"])

        # 4. Items is null or string
        resp = self.client.post(
            "/api/upload",
            files={"file": ("bad_items.json", b'{"items": "not a list"}', "application/json")},
            data={"hasPasskeys": "false"}
        )
        self.assertEqual(resp.status_code, 400)

        # 5. Item missing mandatory id
        resp = self.client.post(
            "/api/upload",
            files={"file": ("missing_id.json", b'{"items": [{"name": "No ID Item"}]}', "application/json")},
            data={"hasPasskeys": "false"}
        )
        self.assertEqual(resp.status_code, 400)

        # 6. Null fields handling (should successfully parse and load without crashes)
        null_fields_vault = {
            "encrypted": False,
            "folders": None,  # folders is null
            "items": [
                {
                    "id": "null-item-1",
                    "name": None,  # null name
                    "folderId": None,
                    "notes": None,
                    "type": 1,
                    "login": None,  # null login
                    "fields": None
                },
                {
                    "id": "null-item-2",
                    "name": None,
                    "folderId": None,
                    "notes": None,
                    "type": 1,
                    "login": {
                        "uris": None,
                        "username": None,
                        "password": None,
                        "totp": None,
                        "fido2Credentials": None
                    }
                }
            ]
        }
        resp = self.client.post(
            "/api/upload",
            files={"file": ("null_fields.json", json.dumps(null_fields_vault).encode("utf-8"), "application/json")},
            data={"hasPasskeys": "false"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assert_stats_integrity(2)

    def test_merge_error_cases(self):
        # Load a valid vault
        valid_vault = {
            "encrypted": False,
            "items": [
                {
                    "id": "m1",
                    "name": "Item M1",
                    "login": {"uris": [{"uri": "https://service.com"}], "username": "user1", "password": "p1"}
                },
                {
                    "id": "m2",
                    "name": "Item M2",
                    "login": {"uris": [{"uri": "https://service.com"}], "username": "user1", "password": "p2"}
                },
                {
                    "id": "other-item",
                    "name": "Other Item",
                    "login": {"uris": [{"uri": "https://other.com"}], "username": "other", "password": "p3"}
                }
            ]
        }
        self.client.post(
            "/api/upload",
            files={"file": ("v.json", json.dumps(valid_vault).encode("utf-8"), "application/json")},
            data={"hasPasskeys": "false"}
        )

        # 1. Non-existent domain
        resp = self.client.post("/api/merge", json={
            "domain": "non-existent.com",
            "accountId": "user1",
            "survivorId": "m1"
        })
        self.assertEqual(resp.status_code, 400)

        # 2. Non-existent accountId
        resp = self.client.post("/api/merge", json={
            "domain": "service.com",
            "accountId": "ghost-account",
            "survivorId": "m1"
        })
        self.assertEqual(resp.status_code, 400)

        # 3. Non-existent survivorId
        resp = self.client.post("/api/merge", json={
            "domain": "service.com",
            "accountId": "user1",
            "survivorId": "ghost-item-id"
        })
        self.assertEqual(resp.status_code, 400)

        # 4. SurvivorId belonging to a different domain/account
        resp = self.client.post("/api/merge", json={
            "domain": "service.com",
            "accountId": "user1",
            "survivorId": "other-item"
        })
        self.assertEqual(resp.status_code, 400)

    def test_edit_restore_delete_push_error_cases(self):
        valid_vault = {
            "encrypted": False,
            "items": [
                {
                    "id": "e1",
                    "name": "Item E1",
                    "login": {"uris": [{"uri": "https://edit.com"}], "username": "user_e", "password": "pe1"}
                },
                {
                    "id": "e2",
                    "name": "Item E2",
                    "login": {"uris": [{"uri": "https://edit.com"}], "username": "user_e", "password": "pe2"}
                }
            ]
        }
        self.client.post(
            "/api/upload",
            files={"file": ("v.json", json.dumps(valid_vault).encode("utf-8"), "application/json")},
            data={"hasPasskeys": "false"}
        )

        # 1. Editing non-existent itemId
        resp = self.client.post("/api/edit", json={"itemId": "ghost-item", "field": "name", "value": "New"})
        self.assertEqual(resp.status_code, 400)

        # 2. Restoring an itemId not in deleted items
        resp = self.client.post("/api/restore/e1")
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post("/api/restore/completely-random-id")
        self.assertEqual(resp.status_code, 400)

        # 3. Deleting non-existent itemId
        resp = self.client.post("/api/delete/non-existent-id")
        self.assertEqual(resp.status_code, 400)

        # 4. Deleting an already deleted itemId
        resp = self.client.post("/api/delete/e1")
        self.assertEqual(resp.status_code, 200)
        # Second delete of e1 must fail
        resp2 = self.client.post("/api/delete/e1")
        self.assertEqual(resp2.status_code, 400)

        # 5. Push with non-existent sourceItemId
        resp = self.client.post("/api/push", json={
            "domain": "edit.com",
            "accountId": "user_e",
            "field": "password",
            "sourceItemId": "ghost-source"
        })
        self.assertEqual(resp.status_code, 400)

        # 6. Push with non-existent domain
        resp = self.client.post("/api/push", json={
            "domain": "ghost-domain.com",
            "accountId": "user_e",
            "field": "password",
            "sourceItemId": "e2"
        })
        self.assertEqual(resp.status_code, 400)


class TestVaultStatsIntegrity(PermutationTestBase):
    """
    5. Vault Stats Integrity Check:
       - Verify stats (totalItems, duplicateCount, uniqueCount, modifiedCount, deletedCount, passkeyTotalCount)
         maintain mathematical consistency across every action, undo, redo, and export.
    """

    def test_continuous_mathematical_consistency(self):
        vault = {
            "encrypted": False,
            "folders": [{"id": "f1", "name": "Work"}],
            "items": [
                {
                    "id": f"s_item_{i}",
                    "name": f"Stats Test {i}",
                    "login": {
                        "uris": [{"uri": "https://stats.test.com"}],
                        "username": "tester@test.com",
                        "password": f"Pass_{i}",
                        "fido2Credentials": [{"credentialId": f"cred-{i}", "rpId": "stats.test.com"}] if i <= 2 else []
                    }
                }
                for i in range(1, 6)
            ] + [
                {
                    "id": "s_unique_1",
                    "name": "Unique One",
                    "login": {"uris": [{"uri": "https://unique1.com"}], "username": "u1", "password": "pu1"}
                },
                {
                    "id": "s_unique_2",
                    "name": "Unique Two",
                    "login": {"uris": [{"uri": "https://unique2.com"}], "username": "u2", "password": "pu2"}
                }
            ]
        }
        # 5 duplicates + 2 uniques = 7 items.
        up = self.client.post(
            "/api/upload",
            files={"file": ("v.json", json.dumps(vault).encode("utf-8"), "application/json")},
            data={"hasPasskeys": "true"}
        )
        self.assertEqual(up.status_code, 200)
        self.assert_stats_integrity(7)

        # Initial check
        stats = self.client.get("/api/stats").json()["stats"]
        self.assertEqual(stats["totalItems"], 7)
        self.assertEqual(stats["duplicateCount"], 5)
        self.assertEqual(stats["uniqueCount"], 2)
        self.assertEqual(stats["modifiedCount"], 0)
        self.assertEqual(stats["deletedCount"], 0)
        self.assertEqual(stats["passkeyTotalCount"], 2)

        # Edit unique item
        self.client.post("/api/edit", json={"itemId": "s_unique_1", "field": "name", "value": "Unique Modified"})
        self.assert_stats_integrity(7)
        stats = self.client.get("/api/stats").json()["stats"]
        self.assertEqual(stats["modifiedCount"], 1)

        # Delete an item with passkey (s_item_1)
        self.client.post("/api/delete/s_item_1")
        self.assert_stats_integrity(7)
        stats = self.client.get("/api/stats").json()["stats"]
        self.assertEqual(stats["totalItems"], 6)
        self.assertEqual(stats["deletedCount"], 1)
        self.assertEqual(stats["passkeyTotalCount"], 1)  # Dropped from 2 to 1

        # Delete another item (s_item_5)
        self.client.post("/api/delete/s_item_5")
        self.assert_stats_integrity(7)
        stats = self.client.get("/api/stats").json()["stats"]
        self.assertEqual(stats["totalItems"], 5)
        self.assertEqual(stats["deletedCount"], 2)

        # Restore s_item_1 (passkey returns)
        self.client.post("/api/restore/s_item_1")
        self.assert_stats_integrity(7)
        stats = self.client.get("/api/stats").json()["stats"]
        self.assertEqual(stats["totalItems"], 6)
        self.assertEqual(stats["deletedCount"], 1)
        self.assertEqual(stats["passkeyTotalCount"], 2)

        # Merge account into s_item_1 (survivor)
        # Active duplicates remaining in tester@test.com are s_item_1, s_item_2, s_item_3, s_item_4
        merge_res = self.client.post("/api/merge", json={
            "domain": "test.com",
            "accountId": "tester@test.com",
            "survivorId": "s_item_1"
        })
        self.assertEqual(merge_res.status_code, 200)
        self.assert_stats_integrity(7)

        stats = self.client.get("/api/stats").json()["stats"]
        # s_item_2, s_item_3, s_item_4 soft deleted (+3 deleted)
        # s_item_5 was already deleted
        # Total deleted = 4
        # Total active = 3 (s_item_1, s_unique_1, s_unique_2)
        # Since s_item_1 is now alone in its account, duplicateCount is 0, uniqueCount is 3!
        self.assertEqual(stats["totalItems"], 3)
        self.assertEqual(stats["duplicateCount"], 0)
        self.assertEqual(stats["uniqueCount"], 3)
        self.assertEqual(stats["deletedCount"], 4)
        # Survivor s_item_1 merged passkeys from s_item_2, so passkey count is still 2!
        self.assertEqual(stats["passkeyTotalCount"], 2)

        # Export and verify clean vault
        exp = self.client.get("/api/export").json()
        self.assertEqual(len(exp["items"]), 3)
        survivor_export = next(it for it in exp["items"] if it["id"] == "s_item_1")
        self.assertEqual(len(survivor_export["login"]["fido2Credentials"]), 2)

        # Undo the merge
        self.client.post("/api/undo")
        self.assert_stats_integrity(7)
        stats_undone = self.client.get("/api/stats").json()["stats"]
        self.assertEqual(stats_undone["totalItems"], 6)
        self.assertEqual(stats_undone["deletedCount"], 1)

        # Redo the merge
        self.client.post("/api/redo")
        self.assert_stats_integrity(7)
        stats_redone = self.client.get("/api/stats").json()["stats"]
        self.assertEqual(stats_redone["totalItems"], 3)
        self.assertEqual(stats_redone["deletedCount"], 4)


if __name__ == "__main__":
    unittest.main()
