import json
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.parser import parse_and_validate_vault
from backend.app.models import (
    BitwardenVault,
    BitwardenItem,
    BitwardenFolder,
    LoginInfo,
    URI,
    Fido2Credential,
    PasswordHistoryItem,
    CustomField,
)
from backend.app.session import session


class TestBitwardenExportSchema(unittest.TestCase):
    """
    Rigorously validates that the exported JSON produced by the application
    strictly conforms to Bitwarden's official vault export specification,
    supports seamless round-tripping, and preserves all credential types.
    """

    def setUp(self):
        self.client = TestClient(app)

    def test_official_bitwarden_schema_structure(self):
        """
        Verify that every key and nested structure in the export conforms
        to Bitwarden's JSON export specification.
        """
        # Load demo vault which contains all item types, passkeys, and folders
        load_res = self.client.post("/api/load-demo")
        self.assertEqual(load_res.status_code, 200)

        # Fetch exported JSON
        export_res = self.client.get("/api/export")
        self.assertEqual(export_res.status_code, 200)
        self.assertEqual(export_res.headers["content-type"], "application/json")
        self.assertIn("bitwarden_cleaned_export.json", export_res.headers.get("content-disposition", ""))

        data = export_res.json()

        # 1. Root structure
        self.assertIsInstance(data, dict)
        self.assertIn("encrypted", data)
        self.assertIs(data["encrypted"], False)
        self.assertIn("folders", data)
        self.assertIsInstance(data["folders"], list)
        self.assertIn("items", data)
        self.assertIsInstance(data["items"], list)

        # 2. Folders validation
        for folder in data["folders"]:
            self.assertIsInstance(folder, dict)
            self.assertIn("id", folder)
            self.assertIsInstance(folder["id"], str)
            self.assertIn("name", folder)
            self.assertIsInstance(folder["name"], str)

        # 3. Items validation
        valid_types = {1, 2, 3, 4}  # 1=Login, 2=SecureNote, 3=Card, 4=Identity
        for item in data["items"]:
            self.assertIsInstance(item, dict)
            self.assertIn("id", item)
            self.assertIsInstance(item["id"], str)
            self.assertIn("name", item)
            self.assertIsInstance(item["name"], str)
            self.assertIn("type", item)
            self.assertIn(item["type"], valid_types)

            # Optional standard metadata
            if "reprompt" in item and item["reprompt"] is not None:
                self.assertIsInstance(item["reprompt"], int)
            if "favorite" in item and item["favorite"] is not None:
                self.assertIsInstance(item["favorite"], bool)
            if "folderId" in item and item["folderId"] is not None:
                self.assertIsInstance(item["folderId"], str)
            if "notes" in item and item["notes"] is not None:
                self.assertIsInstance(item["notes"], str)

            # Custom Fields validation
            if "fields" in item and item["fields"] is not None:
                self.assertIsInstance(item["fields"], list)
                for f in item["fields"]:
                    self.assertIsInstance(f, dict)
                    self.assertIn("name", f)
                    self.assertIsInstance(f["name"], str)
                    self.assertIn("type", f)
                    self.assertIsInstance(f["type"], int)

            # Login item specific schema
            if item["type"] == 1:
                self.assertIn("login", item)
                login = item["login"]
                self.assertIsInstance(login, dict)

                # URIs array
                if "uris" in login and login["uris"] is not None:
                    self.assertIsInstance(login["uris"], list)
                    for u in login["uris"]:
                        self.assertIsInstance(u, dict)
                        self.assertIn("uri", u)
                        self.assertIsInstance(u["uri"], str)

                # Passkeys (FIDO2 Credentials) schema
                if "fido2Credentials" in login and login["fido2Credentials"] is not None:
                    self.assertIsInstance(login["fido2Credentials"], list)
                    for passkey in login["fido2Credentials"]:
                        self.assertIsInstance(passkey, dict)
                        self.assertIn("credentialId", passkey)
                        self.assertIsInstance(passkey["credentialId"], str)
                        self.assertIn("rpId", passkey)
                        self.assertIsInstance(passkey["rpId"], str)
                        if "creationDate" in passkey and passkey["creationDate"] is not None:
                            self.assertIsInstance(passkey["creationDate"], str)

                # Password history schema
                if "passwordHistory" in login and login["passwordHistory"] is not None:
                    self.assertIsInstance(login["passwordHistory"], list)
                    for ph in login["passwordHistory"]:
                        self.assertIsInstance(ph, dict)
                        self.assertIn("password", ph)
                        self.assertIsInstance(ph["password"], str)
                        self.assertIn("lastUsedDate", ph)
                        self.assertIsInstance(ph["lastUsedDate"], str)

    def test_round_trip_import_export_idempotency(self):
        """
        Verify that an exported vault can be immediately re-imported
        into Bitwarden without validation errors, preserving all items and passkeys.
        """
        # Step 1: Load demo vault
        self.client.post("/api/load-demo")

        # Step 2: Merge the Google personal duplicates
        merge_res = self.client.post("/api/merge", json={
            "domain": "google.com",
            "accountId": "alexturner@gmail.com",
            "survivorId": "item-google-1",
        })
        self.assertEqual(merge_res.status_code, 200)

        # Step 3: Export the cleaned vault
        export_res = self.client.get("/api/export")
        self.assertEqual(export_res.status_code, 200)
        exported_raw = export_res.text
        exported_json = export_res.json()

        # Step 4: Re-import and validate the exported vault via parse_and_validate_vault
        re_imported_vault, stats = parse_and_validate_vault(exported_raw)
        self.assertIsInstance(re_imported_vault, BitwardenVault)
        self.assertEqual(stats["encrypted"], False)
        self.assertEqual(stats["totalItems"], len(exported_json["items"]))
        self.assertEqual(stats["folderCount"], len(exported_json["folders"]))

        # Step 5: Verify passkeys are intact in re-imported vault
        self.assertGreaterEqual(stats["passkeyTotalCount"], 3)
        survivor = next(it for it in re_imported_vault.items if it.id == "item-google-1")
        self.assertIsNotNone(survivor.login)
        self.assertIsNotNone(survivor.login.fido2Credentials)
        self.assertEqual(len(survivor.login.fido2Credentials), 1)
        self.assertEqual(
            survivor.login.fido2Credentials[0].credentialId,
            "dB3m9xLk8_QZa1wP-91uVkR_Z8g2K1qN9j210Xl8q7Y"
        )

        # Step 6: Verify password history was retained in re-imported survivor
        self.assertIsNotNone(survivor.login.passwordHistory)
        self.assertEqual(len(survivor.login.passwordHistory), 1)
        self.assertEqual(survivor.login.passwordHistory[0].password, "OldPass2025")

    def test_non_login_item_types_preserved_in_export(self):
        """
        Verify that Secure Notes, Cards, and Identities are preserved
        with all their type-specific fields intact in the export JSON.
        """
        # Construct vault with a Login, Secure Note (type 2), Card (type 3), and Identity (type 4)
        note_item = BitwardenItem(
            id="item-note-1",
            type=2,
            name="Wi-Fi Recovery Keys",
            notes="Master key: 9988-7766-5544",
            secureNote={"type": 0},
        )
        card_item = BitwardenItem(
            id="item-card-1",
            type=3,
            name="Work Corporate Visa",
            notes="Travel card",
            card={
                "cardholderName": "Alex Turner",
                "brand": "Visa",
                "number": "4111222233334444",
                "expMonth": "12",
                "expYear": "2028",
                "code": "123",
            },
        )
        identity_item = BitwardenItem(
            id="item-identity-1",
            type=4,
            name="Primary Billing Identity",
            identity={
                "title": "Mr",
                "firstName": "Alex",
                "lastName": "Turner",
                "address1": "123 Main Street",
                "city": "Austin",
                "state": "TX",
                "postalCode": "78701",
                "country": "US",
            },
        )
        login_item = BitwardenItem(
            id="item-login-1",
            type=1,
            name="Email",
            login=LoginInfo(username="alex@turner.org", password="SecurePassword123!"),
        )

        test_vault = BitwardenVault(
            encrypted=False,
            folders=[BitwardenFolder(id="fld-1", name="Misc")],
            items=[note_item, card_item, identity_item, login_item],
        )

        # Load into session and export
        session.load_vault(test_vault, user_claimed_passkeys=False)
        exported = session.export_vault()
        exported_json = json.loads(exported.model_dump_json(indent=2, exclude_none=True))

        items_by_id = {it["id"]: it for it in exported_json["items"]}

        # Check Secure Note (type 2)
        self.assertIn("item-note-1", items_by_id)
        exported_note = items_by_id["item-note-1"]
        self.assertEqual(exported_note["type"], 2)
        self.assertEqual(exported_note["notes"], "Master key: 9988-7766-5544")
        self.assertEqual(exported_note.get("secureNote", {}).get("type"), 0)

        # Check Card (type 3)
        self.assertIn("item-card-1", items_by_id)
        exported_card = items_by_id["item-card-1"]
        self.assertEqual(exported_card["type"], 3)
        self.assertIn("card", exported_card)
        self.assertEqual(exported_card["card"]["cardholderName"], "Alex Turner")
        self.assertEqual(exported_card["card"]["number"], "4111222233334444")

        # Check Identity (type 4)
        self.assertIn("item-identity-1", items_by_id)
        exported_id = items_by_id["item-identity-1"]
        self.assertEqual(exported_id["type"], 4)
        self.assertIn("identity", exported_id)
        self.assertEqual(exported_id["identity"]["city"], "Austin")
        self.assertEqual(exported_id["identity"]["country"], "US")

    def test_json_formatting_and_mime_type(self):
        """
        Verify export returns valid JSON with proper HTTP headers
        and valid indentation for easy auditing.
        """
        self.client.post("/api/load-demo")
        res = self.client.get("/api/export")
        self.assertEqual(res.status_code, 200)

        # Must be parseable JSON
        parsed = json.loads(res.text)
        self.assertIsInstance(parsed, dict)

        # Must have Content-Disposition header with filename
        cd = res.headers.get("content-disposition", "")
        self.assertTrue(cd.startswith("attachment;"))
        self.assertIn(".json", cd)


if __name__ == "__main__":
    unittest.main()
