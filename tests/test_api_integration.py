import json
import os
import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.session import session

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_full_user_workflow(self):
        # 1. Prepare sample Bitwarden export JSON
        sample_vault = {
            "encrypted": False,
            "folders": [
                {"id": "fld-1", "name": "Personal"},
                {"id": "fld-2", "name": "Work"}
            ],
            "items": [
                {
                    "id": "item-g1",
                    "type": 1,
                    "name": "Google Main",
                    "folderId": "fld-1",
                    "notes": "Note from item 1",
                    "login": {
                        "uris": [{"match": None, "uri": "https://accounts.google.com"}],
                        "username": "abc123",
                        "password": "PasswordOne",
                        "totp": None,
                        "fido2Credentials": [
                            {
                                "credentialId": "passkey-google-1",
                                "rpId": "google.com",
                                "userHandle": "handle1",
                                "creationDate": "2026-01-01T00:00:00Z"
                            }
                        ]
                    }
                },
                {
                    "id": "item-g2",
                    "type": 1,
                    "name": "Google Gmail",
                    "folderId": "fld-1",
                    "notes": "Note from item 2",
                    "login": {
                        "uris": [{"match": None, "uri": "https://mail.google.com"}],
                        "username": "abc123@gmail.com",
                        "password": "PasswordTwo",
                        "totp": "otpauth://totp/Google:abc123?secret=JBSWY3DPEHPK3PXP",
                        "fido2Credentials": []
                    }
                },
                {
                    "id": "item-g3",
                    "type": 1,
                    "name": "Google Second Account",
                    "folderId": "fld-2",
                    "login": {
                        "uris": [{"match": None, "uri": "https://google.com"}],
                        "username": "otherperson@gmail.com",
                        "password": "OtherPassword"
                    }
                },
                {
                    "id": "item-gh1",
                    "type": 1,
                    "name": "GitHub Unique",
                    "folderId": "fld-1",
                    "login": {
                        "uris": [{"match": None, "uri": "https://github.com"}],
                        "username": "octocat",
                        "password": "ghpassword"
                    }
                }
            ]
        }

        json_bytes = json.dumps(sample_vault).encode("utf-8")

        # 2. Upload file with passkey flag = True
        upload_resp = self.client.post(
            "/api/upload",
            files={"file": ("test_export.json", json_bytes, "application/json")},
            data={"hasPasskeys": "true"}
        )
        self.assertEqual(upload_resp.status_code, 200)
        data = upload_resp.json()
        self.assertTrue(data["success"])
        stats = data["stats"]
        self.assertEqual(stats["totalItems"], 4)
        self.assertEqual(stats["duplicateCount"], 2)
        self.assertEqual(stats["uniqueCount"], 2)
        self.assertEqual(stats["passkeyTotalCount"], 1)
        self.assertFalse(stats["hasWarning"])

        # 3. Check sidebar
        sidebar_resp = self.client.get("/api/sidebar")
        self.assertEqual(sidebar_resp.status_code, 200)
        s_data = sidebar_resp.json()
        self.assertEqual(len(s_data["domains"]), 1)
        self.assertEqual(s_data["domains"][0]["domain"], "google.com")
        self.assertEqual(s_data["domains"][0]["totalItems"], 2)
        self.assertEqual(s_data["uniqueCount"], 2)

        # 4. Check duplicate detail view
        dup_resp = self.client.get("/api/duplicates/google.com")
        self.assertEqual(dup_resp.status_code, 200)
        d_group = dup_resp.json()
        self.assertEqual(d_group["domain"], "google.com")
        self.assertEqual(len(d_group["accounts"]), 1)
        acc = d_group["accounts"][0]
        self.assertEqual(acc["itemCount"], 2)
        self.assertTrue(acc["hasPasskeys"])
        self.assertIn("password", acc["diffFields"])

        # 5. Push field value (e.g. push name from item-g1 to all)
        push_resp = self.client.post("/api/push", json={
            "domain": "google.com",
            "accountId": "abc123@gmail.com",
            "field": "name",
            "sourceItemId": "item-g1"
        })
        self.assertEqual(push_resp.status_code, 200)

        # 6. Merge account items into survivor item-g1
        merge_resp = self.client.post("/api/merge", json={
            "domain": "google.com",
            "accountId": "abc123@gmail.com",
            "survivorId": "item-g1"
        })
        self.assertEqual(merge_resp.status_code, 200)
        m_data = merge_resp.json()
        self.assertEqual(m_data["stats"]["duplicateCount"], 0)
        self.assertEqual(m_data["stats"]["deletedCount"], 1)
        self.assertEqual(m_data["stats"]["modifiedCount"], 1)

        # 7. Verify survivor item has:
        # - The passkey from item-g1
        # - The password history with PasswordTwo from item-g2
        # - The TOTP adopted from item-g2
        # - Combined notes
        survivor = session.active_items["item-g1"]
        self.assertEqual(len(survivor.login.fido2Credentials), 1)
        self.assertEqual(survivor.login.fido2Credentials[0].credentialId, "passkey-google-1")
        self.assertEqual(len(survivor.login.passwordHistory), 1)
        self.assertEqual(survivor.login.passwordHistory[0].password, "PasswordTwo")
        self.assertIn("JBSWY3DPEHPK3PXP", survivor.login.totp)
        self.assertIn("Note from item 2", survivor.notes)

        # 8. Test Deleted view and Restore
        del_resp = self.client.get("/api/deleted")
        self.assertEqual(del_resp.status_code, 200)
        del_items = del_resp.json()["items"]
        self.assertEqual(len(del_items), 1)
        self.assertEqual(del_items[0]["id"], "item-g2")

        # 9. Test Undo
        undo_resp = self.client.post("/api/undo")
        self.assertEqual(undo_resp.status_code, 200)
        self.assertTrue(undo_resp.json()["success"])
        # Now item-g2 should be back in active items
        self.assertIn("item-g2", session.active_items)

        # 10. Test Redo
        redo_resp = self.client.post("/api/redo")
        self.assertEqual(redo_resp.status_code, 200)
        self.assertTrue(redo_resp.json()["success"])
        self.assertNotIn("item-g2", session.active_items)

        # 11. Test Export Cleaned Vault
        export_resp = self.client.get("/api/export")
        self.assertEqual(export_resp.status_code, 200)
        exported_vault = export_resp.json()
        self.assertIn("items", exported_vault)
        self.assertIn("folders", exported_vault)
        # Should contain exactly 3 active items (item-g1, item-g3, item-gh1), item-g2 is excluded!
        exported_ids = {it["id"] for it in exported_vault["items"]}
        self.assertEqual(exported_ids, {"item-g1", "item-g3", "item-gh1"})

    def test_load_demo_vault_endpoint(self):
        # 1. Trigger POST /api/load-demo
        resp = self.client.post("/api/load-demo")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertTrue(os.path.exists(data["backupPath"]))
        stats = data["stats"]

        # Verify stats summary
        self.assertEqual(stats["totalItems"], 15)
        self.assertEqual(stats["duplicateCount"], 9)
        self.assertEqual(stats["uniqueCount"], 6)
        self.assertEqual(stats["passkeyTotalCount"], 3)
        self.assertEqual(stats["passkeyItemCount"], 2)
        self.assertFalse(stats["hasWarning"])

        # 2. Check sidebar domains
        side_resp = self.client.get("/api/sidebar")
        self.assertEqual(side_resp.status_code, 200)
        side_data = side_resp.json()
        domain_names = [d["domain"] for d in side_data["domains"]]
        self.assertIn("google.com", domain_names)
        self.assertIn("github.com", domain_names)
        self.assertIn("amazon.com", domain_names)
        self.assertEqual(side_data["uniqueCount"], 6)

        # 3. Check Google domain: 2 accounts (alexturner@gmail.com, alex.turner@acmecorp.com)
        google_resp = self.client.get("/api/duplicates/google.com")
        self.assertEqual(google_resp.status_code, 200)
        google_group = google_resp.json()
        self.assertEqual(google_group["totalAccounts"], 2)
        self.assertEqual(google_group["totalItems"], 5)
        self.assertTrue(google_group["hasPasskeys"])

        accounts = {a["normalizedUsername"]: a for a in google_group["accounts"]}
        self.assertIn("alexturner@gmail.com", accounts)
        self.assertIn("alex.turner@acmecorp.com", accounts)

        personal_acc = accounts["alexturner@gmail.com"]
        self.assertEqual(personal_acc["itemCount"], 3)
        self.assertTrue(personal_acc["hasPasskeys"])
        self.assertIn("passkeys", personal_acc["diffFields"])

        work_acc = accounts["alex.turner@acmecorp.com"]
        self.assertEqual(work_acc["itemCount"], 2)
        self.assertFalse(work_acc["hasPasskeys"])

        # 4. Check GitHub domain: 1 account with 2 items
        gh_resp = self.client.get("/api/duplicates/github.com")
        self.assertEqual(gh_resp.status_code, 200)
        gh_group = gh_resp.json()
        self.assertEqual(gh_group["totalAccounts"], 1)
        self.assertEqual(gh_group["totalItems"], 2)
        self.assertIn("password", gh_group["accounts"][0]["diffFields"])

        # 5. Check Amazon domain: 1 account across subdomains
        amz_resp = self.client.get("/api/duplicates/amazon.com")
        self.assertEqual(amz_resp.status_code, 200)
        amz_group = amz_resp.json()
        self.assertEqual(amz_group["totalAccounts"], 1)
        self.assertEqual(amz_group["totalItems"], 2)

        # 6. Check unique items: Netflix, Spotify, Bitwarden, Cloudflare (2 passkeys), Wi-Fi Router, Steam Guard
        unique_resp = self.client.get("/api/unique")
        self.assertEqual(unique_resp.status_code, 200)
        unique_items = unique_resp.json()["items"]
        self.assertEqual(len(unique_items), 6)
        unique_names = {u["name"] for u in unique_items}
        self.assertIn("Netflix", unique_names)
        self.assertIn("Spotify", unique_names)
        self.assertIn("Bitwarden Vault", unique_names)
        self.assertIn("Cloudflare Dashboard", unique_names)
        self.assertIn("Wi-Fi Router Admin", unique_names)
        self.assertIn("Steam Guard App", unique_names)

        # Verify Cloudflare has 2 passkeys
        cloudflare = next(u for u in unique_items if u["name"] == "Cloudflare Dashboard")
        self.assertEqual(cloudflare["passkeyCount"], 2)
        self.assertEqual(len(cloudflare["passkeyDetails"]), 2)

        # Verify Wi-Fi Router Admin has no URIs
        router = next(u for u in unique_items if u["name"] == "Wi-Fi Router Admin")
        self.assertEqual(len(router["uris"]), 0)

    def test_separate_and_regroup_items(self):
        # 1. Load demo vault
        resp = self.client.post("/api/load-demo")
        self.assertEqual(resp.status_code, 200)

        # 2. Get GitHub duplicate items
        gh_resp = self.client.get("/api/duplicates/github.com")
        self.assertEqual(gh_resp.status_code, 200)
        gh_data = gh_resp.json()
        gh_items = gh_data["accounts"][0]["items"]
        self.assertEqual(len(gh_items), 2)
        gh_item_id = gh_items[0]["id"]

        # 3. Separate first GitHub item as unique
        sep_resp = self.client.post(f"/api/item/{gh_item_id}/separate")
        self.assertEqual(sep_resp.status_code, 200)

        # Check duplicates for github.com: should now have 0 duplicates (the remaining item is now unique)
        sidebar_resp = self.client.get("/api/sidebar")
        domains = [d["domain"] for d in sidebar_resp.json()["domains"]]
        self.assertNotIn("github.com", domains)

        # Verify that both items are now in unique items
        unique_resp = self.client.get("/api/unique")
        unique_ids = [u["id"] for u in unique_resp.json()["items"]]
        self.assertIn(gh_item_id, unique_ids)

        # 4. Test move_items_domain to regroup them into a custom domain: "git-custom.com"
        other_gh_id = gh_items[1]["id"]
        move_resp = self.client.post(
            "/api/items/move_domain",
            json={"itemIds": [gh_item_id, other_gh_id], "domain": "git-custom.com"}
        )
        self.assertEqual(move_resp.status_code, 200)

        # Check duplicates for git-custom.com
        custom_resp = self.client.get("/api/duplicates/git-custom.com")
        self.assertEqual(custom_resp.status_code, 200)
        custom_group = custom_resp.json()
        self.assertEqual(custom_group["totalItems"], 2)

        # 5. Test undo: reverting the move
        undo_resp = self.client.post("/api/undo")
        self.assertEqual(undo_resp.status_code, 200)
        custom_resp2 = self.client.get("/api/duplicates/git-custom.com")
        self.assertEqual(custom_resp2.json()["totalItems"], 0)

        # Undo again: reverting the separation -> github.com duplicates restored!
        undo_resp2 = self.client.post("/api/undo")
        self.assertEqual(undo_resp2.status_code, 200)
        gh_restored = self.client.get("/api/duplicates/github.com").json()
        self.assertEqual(gh_restored["totalItems"], 2)


if __name__ == "__main__":
    unittest.main()
