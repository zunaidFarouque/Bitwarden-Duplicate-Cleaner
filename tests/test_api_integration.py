import json
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
        sb_data = sidebar_resp.json()
        self.assertEqual(len(sb_data["domains"]), 1)
        self.assertEqual(sb_data["domains"][0]["domain"], "google.com")
        self.assertEqual(sb_data["uniqueCount"], 2)

        # 4. Check domain duplicates
        dup_resp = self.client.get("/api/duplicates/google.com")
        self.assertEqual(dup_resp.status_code, 200)
        group = dup_resp.json()
        self.assertEqual(group["domain"], "google.com")
        self.assertEqual(group["totalAccounts"], 1)
        self.assertEqual(len(group["accounts"][0]["items"]), 2)
        # Verify diff fields detected password and totp
        self.assertIn("password", group["accounts"][0]["diffFields"])
        self.assertIn("totp", group["accounts"][0]["diffFields"])

        # 5. Push value across account duplicates (e.g. push name)
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


if __name__ == "__main__":
    unittest.main()
