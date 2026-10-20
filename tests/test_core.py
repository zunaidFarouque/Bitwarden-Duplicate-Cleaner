import unittest
from backend.app.models import (
    BitwardenVault,
    BitwardenItem,
    LoginInfo,
    URI,
    Fido2Credential,
    CustomField,
)
from backend.app.normalizer import extract_domain_from_uri, normalize_username
from backend.app.deduplicator import analyze_vault
from backend.app.consolidator import merge_into_survivor, push_field_value_to_items
from backend.app.session import VaultSession


class TestBitwardenCleanerCore(unittest.TestCase):

    def test_domain_extraction(self):
        self.assertEqual(extract_domain_from_uri("https://accounts.google.com/signin"), "google.com")
        self.assertEqual(extract_domain_from_uri("https://mail.google.com"), "google.com")
        self.assertEqual(extract_domain_from_uri("https://sub.portal.amazon.co.uk/ap/signin"), "amazon.co.uk")
        self.assertEqual(extract_domain_from_uri("androidapp://com.google.android.youtube"), "google.com")
        self.assertEqual(extract_domain_from_uri("https://github.com/login"), "github.com")

    def test_google_username_normalization(self):
        # All of these should normalize to the exact same identifier for Google
        u1 = normalize_username("john.doe@gmail.com", "google.com")
        u2 = normalize_username("johndoe", "google.com")
        u3 = normalize_username("John.Doe+updates@googlemail.com", "google.com")
        self.assertEqual(u1, "johndoe@gmail.com")
        self.assertEqual(u2, "johndoe@gmail.com")
        self.assertEqual(u3, "johndoe@gmail.com")

    def test_deduplication_grouping(self):
        # Create 2 google items with matching normalized username, 1 different google account, 1 github item
        item1 = BitwardenItem(
            id="item-1",
            name="Google Account",
            login=LoginInfo(
                uris=[URI(uri="https://accounts.google.com")],
                username="abc123",
                password="pass1",
            ),
        )
        item2 = BitwardenItem(
            id="item-2",
            name="Gmail Login",
            login=LoginInfo(
                uris=[URI(uri="https://mail.google.com")],
                username="abc123@gmail.com",
                password="pass2",
            ),
        )
        item3 = BitwardenItem(
            id="item-3",
            name="Google Work",
            login=LoginInfo(
                uris=[URI(uri="https://google.com")],
                username="work_user@example.com",
                password="pass3",
            ),
        )
        item4 = BitwardenItem(
            id="item-4",
            name="GitHub",
            login=LoginInfo(
                uris=[URI(uri="https://github.com")],
                username="coder",
                password="pass4",
            ),
        )

        dup_domains, unique_items, summaries = analyze_vault([item1, item2, item3, item4], [])

        # Google should be in duplicate_domains
        self.assertIn("google.com", dup_domains)
        google_group = dup_domains["google.com"]
        # Exactly 1 duplicate account (abc123)
        self.assertEqual(google_group.totalAccounts, 1)
        self.assertEqual(len(google_group.accounts[0].items), 2)
        # item3 and item4 should be in unique_items
        unique_ids = {u.id for u in unique_items}
        self.assertIn("item-3", unique_ids)
        self.assertIn("item-4", unique_ids)

    def test_passkey_union_and_password_history(self):
        item1 = BitwardenItem(
            id="it-1",
            name="Master Google",
            login=LoginInfo(
                uris=[URI(uri="https://accounts.google.com")],
                username="alice@gmail.com",
                password="primary_password",
                fido2Credentials=[
                    Fido2Credential(credentialId="key-1", rpId="google.com", userHandle="alice-1")
                ],
            ),
        )
        item2 = BitwardenItem(
            id="it-2",
            name="Old Google",
            notes="Important secret note",
            login=LoginInfo(
                uris=[URI(uri="https://google.com")],
                username="alice@gmail.com",
                password="older_password",
                fido2Credentials=[
                    Fido2Credential(credentialId="key-2", rpId="google.com", userHandle="alice-2")
                ],
            ),
            fields=[CustomField(name="PIN", value="9988")],
        )

        merged = merge_into_survivor(item1, [item1, item2])

        # Both passkeys must be preserved
        self.assertEqual(len(merged.login.fido2Credentials), 2)
        cred_ids = {p.credentialId for p in merged.login.fido2Credentials}
        self.assertEqual(cred_ids, {"key-1", "key-2"})

        # The older password must be archived into passwordHistory
        self.assertEqual(len(merged.login.passwordHistory), 1)
        self.assertEqual(merged.login.passwordHistory[0].password, "older_password")

        # Custom field preserved
        self.assertEqual(len(merged.fields), 1)
        self.assertEqual(merged.fields[0].name, "PIN")

        # Note merged
        self.assertIn("Important secret note", merged.notes)

    def test_session_undo_redo(self):
        session = VaultSession()
        item1 = BitwardenItem(
            id="i1",
            name="Acc 1",
            login=LoginInfo(uris=[URI(uri="https://test.com")], username="user1", password="pw1"),
        )
        item2 = BitwardenItem(
            id="i2",
            name="Acc 2",
            login=LoginInfo(uris=[URI(uri="https://test.com")], username="user1", password="pw2"),
        )
        vault = BitwardenVault(items=[item1, item2])
        session.load_vault(vault, user_claimed_passkeys=False)

        # Merge
        self.assertTrue(session.merge_account("test.com", "user1", "i1"))
        self.assertEqual(len(session.active_items), 1)
        self.assertEqual(len(session.deleted_items), 1)

        # Undo
        self.assertTrue(session.undo())
        self.assertEqual(len(session.active_items), 2)
        self.assertEqual(len(session.deleted_items), 0)

        # Redo
        self.assertTrue(session.redo())
        self.assertEqual(len(session.active_items), 1)
        self.assertEqual(len(session.deleted_items), 1)


if __name__ == "__main__":
    unittest.main()
