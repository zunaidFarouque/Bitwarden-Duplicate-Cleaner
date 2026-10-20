"""
Exhaustive Permutations & Combinations Test Suite for Bitwarden Duplicate Cleaner.

Covers:
1. Domain Normalization Combinations
2. Username Normalization Permutations & Combinations
3. Consolidator Combinations & Permutations
4. Grouping & Diff Matrix Permutations
"""

import unittest
from datetime import datetime, timezone
from backend.app.models import (
    BitwardenItem,
    BitwardenVault,
    BitwardenFolder,
    LoginInfo,
    URI,
    Fido2Credential,
    CustomField,
    PasswordHistoryItem,
)
from backend.app.normalizer import (
    COMMON_DOUBLE_TLDS,
    extract_domain_from_uri,
    get_item_primary_domain,
    normalize_username,
)
from backend.app.consolidator import (
    merge_into_survivor,
    push_field_value_to_items,
)
from backend.app.deduplicator import (
    compute_group_diffs,
    item_to_summary,
    analyze_vault,
)


class TestDomainNormalizationCombinations(unittest.TestCase):
    """Exhaustive tests for domain normalization across TLDs, schemes, and edge cases."""

    def test_all_registered_common_double_tlds(self):
        """Verify that every single TLD registered in COMMON_DOUBLE_TLDS resolves correctly."""
        for double_tld in sorted(COMMON_DOUBLE_TLDS):
            uri = f"https://service.portal.company.{double_tld}/login"
            expected = f"company.{double_tld}"
            extracted = extract_domain_from_uri(uri)
            self.assertEqual(
                extracted,
                expected,
                f"Failed for double TLD '{double_tld}' in uri: {uri}",
            )

    def test_country_code_second_level_domains_deep_nesting(self):
        """Test deep subdomains on various country code second-level domains."""
        cases = [
            ("https://a.b.c.d.bbc.co.uk/news/world", "bbc.co.uk"),
            ("https://login.auth.services.gov.uk/dashboard", "services.gov.uk"),
            ("https://student.library.portal.oxford.ac.uk/", "oxford.ac.uk"),
            ("http://sub1.sub2.sub3.firm.co.nz", "firm.co.nz"),
            ("https://portal.my.gov.au/home", "my.gov.au"),
            ("https://store.rakuten.co.jp/search?q=test", "rakuten.co.jp"),
            ("https://netbanking.hdfcbank.co.in/netbanking/", "hdfcbank.co.in"),
            ("https://app.corp.globo.com.br/stream", "globo.com.br"),
            ("https://admin.portal.standardbank.co.za", "standardbank.co.za"),
            ("https://mymail.nus.edu.sg/owa", "nus.edu.sg"),
            ("https://sub.portal.gov.tr/giris", "portal.gov.tr"),
            ("https://campus.unam.edu.mx/alumnos", "unam.edu.mx"),
            ("https://shop.books.com.tw/item/123", "books.com.tw"),
        ]
        for uri, expected in cases:
            with self.subTest(uri=uri):
                self.assertEqual(extract_domain_from_uri(uri), expected)

    def test_standard_etld_plus_one(self):
        """Test regular domains with single-part TLDs and various subdomain depths."""
        cases = [
            ("https://accounts.google.com/signin", "google.com"),
            ("https://mail.google.com", "google.com"),
            ("https://a.b.c.d.e.example.com/test", "example.com"),
            ("https://portal.login.microsoft.com", "microsoft.com"),
            ("https://dev.internal.corp.net", "corp.net"),
            ("http://sub.company.org/path?q=1#hash", "company.org"),
            ("https://cloud.subdomain.service.io:8443", "service.io"),
            ("https://login.xyz.co/auth", "xyz.co"),
            ("https://vault.bitwarden.eu", "bitwarden.eu"),
            ("https://web.telegram.org/a/", "telegram.org"),
        ]
        for uri, expected in cases:
            with self.subTest(uri=uri):
                self.assertEqual(extract_domain_from_uri(uri), expected)

    def test_complex_subdomains_ports_queries_fragments(self):
        """Test complex subdomains containing ports, query strings, and fragments."""
        cases = [
            ("https://portal.sub.accounts.google.com/auth/login?ref=123:8080", "google.com"),
            ("https://portal.sub.accounts.google.com:8080/auth/login?ref=123", "google.com"),
            ("http://sub.domain.co.uk:3000/path/to/resource?param1=val&param2=other#section", "domain.co.uk"),
            ("https://sub.example.com.:8443/login", "example.com"),  # Trailing dot in host
            ("https://deeply.nested.subdomain.with-hyphens.corp.co.in:9000/?foo=bar#id", "corp.co.in"),
        ]
        for uri, expected in cases:
            with self.subTest(uri=uri):
                self.assertEqual(extract_domain_from_uri(uri), expected)

    def test_app_uris(self):
        """Test Android and iOS app URI schemes."""
        cases = [
            ("androidapp://com.google.android.youtube", "google.com"),
            ("androidapp://com.google.android.apps.docs", "google.com"),
            ("androidapp://com.google.android.gm", "google.com"),
            ("androidapp://com.amazon.mShop.android.shopping", "shopping.com"),
            ("androidapp://org.mozilla.firefox", "firefox.com"),
            ("androidapp://com.spotify.music", "music.com"),
            ("androidapp://com.reddit.frontpage", "frontpage.com"),
            ("androidapp://singlepackage", "singlepackage"),
            ("androidapp://com.google.android.keep/some/path", "google.com"),
        ]
        for uri, expected in cases:
            with self.subTest(uri=uri):
                self.assertEqual(extract_domain_from_uri(uri), expected)

    def test_bare_hostnames_and_ip_addresses(self):
        """Test bare hostnames, IPv4 addresses, and localhost."""
        cases = [
            ("192.168.1.1", "192.168.1.1"),
            ("http://192.168.1.1:8080/admin", "192.168.1.1"),
            ("https://10.0.0.1:8443", "10.0.0.1"),
            ("127.0.0.1", "127.0.0.1"),
            ("http://127.0.0.1:3000", "127.0.0.1"),
            ("localhost", "localhost"),
            ("http://localhost:8000/api/docs", "localhost"),
            ("localhost:5000", "localhost"),
            ("myrouter", "myrouter"),
            ("http://myrouter/setup", "myrouter"),
            ("nas-server", "nas-server"),
            ("http://nas-server:5000/webman/index.cgi", "nas-server"),
        ]
        for uri, expected in cases:
            with self.subTest(uri=uri):
                self.assertEqual(extract_domain_from_uri(uri), expected)

    def test_urls_without_scheme_and_various_protocols(self):
        """Test URLs with missing schemes or non-http schemes."""
        cases = [
            ("accounts.google.com", "google.com"),
            ("sub.portal.amazon.co.uk/orders", "amazon.co.uk"),
            ("github.com/login", "github.com"),
            ("ftp://ftp.example.org/files", "example.org"),
            ("sftp://storage.backup.corp.com:22/data", "corp.com"),
            ("http://example.com/", "example.com"),
            ("https://example.com///", "example.com"),
        ]
        for uri, expected in cases:
            with self.subTest(uri=uri):
                self.assertEqual(extract_domain_from_uri(uri), expected)

    def test_empty_none_whitespace_uris(self):
        """Test handling of None, empty strings, whitespace, and malformed URIs."""
        self.assertIsNone(extract_domain_from_uri(None))
        self.assertIsNone(extract_domain_from_uri(""))
        self.assertIsNone(extract_domain_from_uri("   "))
        self.assertIsNone(extract_domain_from_uri("\t\r\n"))
        self.assertIsNone(extract_domain_from_uri("://broken"))
        self.assertIsNone(extract_domain_from_uri("http://[invalid_ipv6]/"))

    def test_get_item_primary_domain_fallbacks(self):
        """Test fallback heuristics when URIs are missing or invalid."""
        # Valid URIs present
        self.assertEqual(
            get_item_primary_domain(["https://login.microsoftonline.com"], "Work Login"),
            "microsoftonline.com",
        )
        # Empty URI list with name that looks like a domain
        self.assertEqual(
            get_item_primary_domain([], "github.com"),
            "github.com",
        )
        self.assertEqual(
            get_item_primary_domain(None, "sub.domain.co.uk"),
            "domain.co.uk",
        )
        # Name with spaces even if contains dot
        self.assertEqual(
            get_item_primary_domain([], "Company App v1.0"),
            "Company App v1.0 (No Website)",
        )
        # Regular item name without domain format
        self.assertEqual(
            get_item_primary_domain(None, "Personal Banking"),
            "Personal Banking (No Website)",
        )
        # Empty name and empty URIs
        self.assertEqual(
            get_item_primary_domain(None, ""),
            "Uncategorized Logins",
        )
        self.assertEqual(
            get_item_primary_domain([], "   "),
            "Uncategorized Logins",
        )
        # First URI invalid, second URI valid
        self.assertEqual(
            get_item_primary_domain(["   ", "https://valid.site.com"], "Fallback Name"),
            "site.com",
        )


class TestUsernameNormalizationPermutations(unittest.TestCase):
    """Exhaustive tests for username normalization across Google, Workspace, generic emails, and raw usernames."""

    def test_google_casing_dots_and_tags_permutations(self):
        """Test Google email permutations: dots, tags, casing, googlemail vs gmail."""
        google_variations = [
            "John.Doe@Gmail.com",
            "johndoe",
            "johndoe@gmail.com",
            "JOHNDOE+news@googlemail.com",
            "john.doe.123+tag.sub@gmail.com",
            "J.O.H.N.D.O.E@gmail.com",
            "  john.doe@gmail.com  ",
            "johndoe+alias1+alias2@gmail.com",
            "JOHN.DOE@GOOGLEMAIL.COM",
            "john.doe",  # Bare username with dot on google.com
            "johndoe+marketing",  # Bare username with tag on google.com
        ]
        # All of the base 'johndoe' variations should normalize to 'johndoe@gmail.com'
        base_variations = [
            "John.Doe@Gmail.com",
            "johndoe",
            "johndoe@gmail.com",
            "JOHNDOE+news@googlemail.com",
            "J.O.H.N.D.O.E@gmail.com",
            "  john.doe@gmail.com  ",
            "johndoe+alias1+alias2@gmail.com",
            "JOHN.DOE@GOOGLEMAIL.COM",
            "john.doe",
            "johndoe+marketing",
        ]
        for v in base_variations:
            with self.subTest(username=v):
                self.assertEqual(
                    normalize_username(v, "google.com"),
                    "johndoe@gmail.com",
                    f"Failed for Google username variation: {v}",
                )

        # Numbered variation with multiple dots and subtag
        self.assertEqual(
            normalize_username("john.doe.123+tag.sub@gmail.com", "google.com"),
            "johndoe123@gmail.com",
        )

    def test_google_subdomain_matching(self):
        """Test that Google normalization triggers for any google.com subdomains."""
        for domain in ["google.com", "accounts.google.com", "mail.google.com", "GOOGLE.COM"]:
            self.assertEqual(
                normalize_username("Alice.Smith+test@gmail.com", domain),
                "alicesmith@gmail.com",
            )

    def test_google_workspace_custom_domains(self):
        """Test Google Workspace accounts with custom company domains."""
        cases = [
            ("user@mycompany.com", "google.com", "user@mycompany.com"),
            ("user+tag@mycompany.com", "google.com", "user@mycompany.com"),
            ("User.Name+marketing@acme-corp.com", "google.com", "user.name@acme-corp.com"),
            ("ADMIN+alerts@CORP.ORG", "google.com", "admin@corp.org"),
            ("  finance+reports@enterprise.co.uk  ", "google.com", "finance@enterprise.co.uk"),
        ]
        for username, domain, expected in cases:
            with self.subTest(username=username):
                self.assertEqual(normalize_username(username, domain), expected)

    def test_generic_email_domains_permutations(self):
        """Test normalization on non-Google generic domains."""
        cases = [
            # Standard email lowercasing and trimming
            ("User@Example.com", "example.com", "user@example.com"),
            ("  user@example.com  ", "example.com", "user@example.com"),
            ("User.Name@company.org", "company.org", "user.name@company.org"),
            # Tag is preserved on generic domains
            ("user+tag@example.com", "example.com", "user+tag@example.com"),
            ("User+Service.Alert@domain.co.uk", "domain.co.uk", "user+service.alert@domain.co.uk"),
            ("  user+newsletter@proton.me  ", "proton.me", "user+newsletter@proton.me"),
            # Special symbols in email local parts
            ("user_name-123+tag@sub.domain.net", "domain.net", "user_name-123+tag@sub.domain.net"),
            ("first.middle.last@yahoo.com", "yahoo.com", "first.middle.last@yahoo.com"),
        ]
        for username, domain, expected in cases:
            with self.subTest(username=username):
                self.assertEqual(normalize_username(username, domain), expected)

    def test_non_email_usernames_permutations(self):
        """Test non-email username inputs: strings, phone numbers, symbols, empty values."""
        cases = [
            ("Admin", "myrouter", "admin"),
            ("  SuperUser123  ", "github.com", "superuser123"),
            ("John Doe", "nas-server", "john doe"),
            ("+1 (555) 019-2834", "bank.com", "+1 (555) 019-2834"),
            ("+15550192834", "uber.com", "+15550192834"),
            ("dev_ops-lead.01", "internal.net", "dev_ops-lead.01"),
            ("root", "192.168.1.1", "root"),
            ("", "example.com", ""),
            ("   ", "example.com", ""),
            (None, "example.com", ""),
        ]
        for username, domain, expected in cases:
            with self.subTest(username=username):
                self.assertEqual(normalize_username(username, domain), expected)


class TestConsolidatorPermutations(unittest.TestCase):
    """Exhaustive permutations for item consolidation: passkeys, passwords, custom fields, notes, URIs, TOTP."""

    def _create_item(
        self,
        item_id: str,
        name: str = "Test Item",
        username: str = "user@example.com",
        password: str = "password123",
        totp: str = None,
        notes: str = None,
        uris: list = None,
        passkeys: list = None,
        fields: list = None,
        password_history: list = None,
    ) -> BitwardenItem:
        uri_objs = [URI(uri=u) for u in uris] if uris else [URI(uri="https://example.com")]
        passkey_objs = [
            Fido2Credential(
                credentialId=p.get("credentialId"),
                rpId=p.get("rpId", "example.com"),
                userHandle=p.get("userHandle", "handle"),
                userName=p.get("userName", username),
                creationDate=p.get("creationDate", "2026-01-01T00:00:00.000Z"),
            )
            for p in (passkeys or [])
        ]
        field_objs = [
            CustomField(name=f.get("name"), value=f.get("value"), type=f.get("type", 0))
            for f in (fields or [])
        ]
        history_objs = [
            PasswordHistoryItem(password=h.get("password"), lastUsedDate=h.get("lastUsedDate"))
            for h in (password_history or [])
        ]
        return BitwardenItem(
            id=item_id,
            name=name,
            notes=notes,
            login=LoginInfo(
                username=username,
                password=password,
                totp=totp,
                uris=uri_objs,
                fido2Credentials=passkey_objs,
                passwordHistory=history_objs,
            ),
            fields=field_objs,
        )

    # ------------------ Passkey Permutations ------------------

    def test_passkeys_zero_on_all(self):
        """Duplicates with 0 passkeys on survivor and duplicates."""
        survivor = self._create_item("s1", passkeys=[])
        dup1 = self._create_item("d1", passkeys=[])
        dup2 = self._create_item("d2", passkeys=[])

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2])
        self.assertEqual(len(merged.login.fido2Credentials), 0)

    def test_passkeys_survivor_has_passkey_duplicate_does_not(self):
        """Survivor has passkey, duplicates do not."""
        survivor = self._create_item("s1", passkeys=[{"credentialId": "cred-survivor"}])
        dup1 = self._create_item("d1", passkeys=[])
        dup2 = self._create_item("d2", passkeys=[])

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2])
        self.assertEqual(len(merged.login.fido2Credentials), 1)
        self.assertEqual(merged.login.fido2Credentials[0].credentialId, "cred-survivor")

    def test_passkeys_duplicate_has_passkey_survivor_does_not(self):
        """Duplicate has passkey, survivor has none."""
        survivor = self._create_item("s1", passkeys=[])
        dup1 = self._create_item("d1", passkeys=[{"credentialId": "cred-dup1"}])
        dup2 = self._create_item("d2", passkeys=[{"credentialId": "cred-dup2"}])

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2])
        self.assertEqual(len(merged.login.fido2Credentials), 2)
        cred_ids = {p.credentialId for p in merged.login.fido2Credentials}
        self.assertEqual(cred_ids, {"cred-dup1", "cred-dup2"})

    def test_passkeys_both_have_disjoint_passkeys(self):
        """Survivor and multiple duplicates all have disjoint passkeys."""
        survivor = self._create_item("s1", passkeys=[{"credentialId": "cred-s"}])
        dup1 = self._create_item("d1", passkeys=[{"credentialId": "cred-d1"}])
        dup2 = self._create_item("d2", passkeys=[{"credentialId": "cred-d2"}])
        dup3 = self._create_item("d3", passkeys=[{"credentialId": "cred-d3"}])

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2, dup3])
        self.assertEqual(len(merged.login.fido2Credentials), 4)
        cred_ids = [p.credentialId for p in merged.login.fido2Credentials]
        self.assertEqual(cred_ids, ["cred-s", "cred-d1", "cred-d2", "cred-d3"])

    def test_passkeys_overlapping_credential_ids(self):
        """Duplicates contain overlapping/identical credential IDs (no duplicates should be added)."""
        survivor = self._create_item("s1", passkeys=[
            {"credentialId": "cred-shared-1"},
            {"credentialId": "cred-survivor-unique"},
        ])
        dup1 = self._create_item("d1", passkeys=[
            {"credentialId": "cred-shared-1"},  # Overlaps with survivor
            {"credentialId": "cred-dup1-unique"},
        ])
        dup2 = self._create_item("d2", passkeys=[
            {"credentialId": "cred-dup1-unique"},  # Overlaps with dup1
            {"credentialId": "cred-shared-1"},  # Overlaps with survivor
            {"credentialId": "cred-dup2-unique"},
        ])

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2])
        self.assertEqual(len(merged.login.fido2Credentials), 4)
        cred_ids = [p.credentialId for p in merged.login.fido2Credentials]
        self.assertEqual(
            cred_ids,
            ["cred-shared-1", "cred-survivor-unique", "cred-dup1-unique", "cred-dup2-unique"],
        )

    def test_passkeys_deduplication_via_rpid_userhandle_fallback(self):
        """Passkeys without credentialId deduplicate using rpId:userHandle."""
        survivor = self._create_item("s1", passkeys=[
            {"credentialId": None, "rpId": "example.com", "userHandle": "handle1"}
        ])
        dup1 = self._create_item("d1", passkeys=[
            {"credentialId": None, "rpId": "example.com", "userHandle": "handle1"},  # Duplicate
            {"credentialId": None, "rpId": "example.com", "userHandle": "handle2"},  # Unique
        ])

        merged = merge_into_survivor(survivor, [survivor, dup1])
        self.assertEqual(len(merged.login.fido2Credentials), 2)
        handles = [p.userHandle for p in merged.login.fido2Credentials]
        self.assertEqual(handles, ["handle1", "handle2"])

    # ------------------ Discrepant Password Permutations ------------------

    def test_discrepant_passwords_2_duplicates(self):
        """2 duplicates with differing passwords."""
        survivor = self._create_item("s1", password="survivor_pw")
        dup1 = self._create_item("d1", password="dup1_pw")

        merged = merge_into_survivor(survivor, [survivor, dup1])
        self.assertEqual(merged.login.password, "survivor_pw")
        self.assertEqual(len(merged.login.passwordHistory), 1)
        self.assertEqual(merged.login.passwordHistory[0].password, "dup1_pw")

    def test_discrepant_passwords_3_duplicates(self):
        """3 duplicates with 3 distinct passwords."""
        survivor = self._create_item("s1", password="pw_0")
        dup1 = self._create_item("d1", password="pw_1")
        dup2 = self._create_item("d2", password="pw_2")

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2])
        self.assertEqual(merged.login.password, "pw_0")
        history_pws = [h.password for h in merged.login.passwordHistory]
        self.assertEqual(history_pws, ["pw_1", "pw_2"])

    def test_discrepant_passwords_4_duplicates(self):
        """4 duplicates all with distinct passwords."""
        survivor = self._create_item("s1", password="alpha")
        dup1 = self._create_item("d1", password="bravo")
        dup2 = self._create_item("d2", password="charlie")
        dup3 = self._create_item("d3", password="delta")

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2, dup3])
        self.assertEqual(merged.login.password, "alpha")
        history_pws = [h.password for h in merged.login.passwordHistory]
        self.assertEqual(history_pws, ["bravo", "charlie", "delta"])

    def test_discrepant_passwords_with_repeated_passwords_and_empty(self):
        """Duplicates having repeated passwords or empty passwords should avoid duplicate entries."""
        survivor = self._create_item("s1", password="pass_main")
        dup1 = self._create_item("d1", password="pass_main")  # Same as survivor
        dup2 = self._create_item("d2", password="pass_other")
        dup3 = self._create_item("d3", password="pass_other")  # Same as dup2
        dup4 = self._create_item("d4", password="")            # Empty
        dup5 = self._create_item("d5", password=None)          # None

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2, dup3, dup4, dup5])
        self.assertEqual(merged.login.password, "pass_main")
        self.assertEqual(len(merged.login.passwordHistory), 1)
        self.assertEqual(merged.login.passwordHistory[0].password, "pass_other")

    def test_password_history_preservation_and_merging(self):
        """Pre-existing passwordHistory on duplicates is adopted without duplication."""
        survivor = self._create_item(
            "s1",
            password="curr_s",
            password_history=[{"password": "hist_s_old", "lastUsedDate": "2025-01-01T00:00:00.000Z"}],
        )
        dup1 = self._create_item(
            "d1",
            password="curr_d1",
            password_history=[
                {"password": "hist_s_old", "lastUsedDate": "2025-01-01T00:00:00.000Z"},  # Duplicate
                {"password": "hist_d1_old", "lastUsedDate": "2025-02-01T00:00:00.000Z"},
            ],
        )
        dup2 = self._create_item(
            "d2",
            password="curr_d2",
            password_history=[
                {"password": "curr_s", "lastUsedDate": "2025-03-01T00:00:00.000Z"},  # Matches current pw
                {"password": "hist_d2_old", "lastUsedDate": "2025-04-01T00:00:00.000Z"},
            ],
        )

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2])
        self.assertEqual(merged.login.password, "curr_s")
        history_pws = [h.password for h in merged.login.passwordHistory]
        # Order: existing history -> dup1 curr -> dup1 history -> dup2 curr -> dup2 history
        expected = ["hist_s_old", "curr_d1", "hist_d1_old", "curr_d2", "hist_d2_old"]
        self.assertEqual(history_pws, expected)

    # ------------------ Custom Fields Permutations ------------------

    def test_custom_fields_union_permutations(self):
        """Test custom fields union with same field name vs distinct field names."""
        survivor = self._create_item("s1", fields=[
            {"name": "PIN", "value": "1111"},
            {"name": "SecurityQuestion1", "value": "Fluffy"},
        ])
        dup1 = self._create_item("d1", fields=[
            {"name": "pin", "value": "2222"},             # Case-insensitive duplicate (should be skipped)
            {"name": "RecoveryKey", "value": "REC-999"},  # Distinct
        ])
        dup2 = self._create_item("d2", fields=[
            {"name": "SECURITYQUESTION1", "value": "Other"},  # Duplicate
            {"name": "BackupPhone", "value": "+15551234"},    # Distinct
            {"name": None, "value": "invalid"},               # None name
            {"name": "   ", "value": "whitespace"},           # Whitespace name
        ])

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2])
        field_dict = {f.name: f.value for f in merged.fields}
        self.assertEqual(len(merged.fields), 4)
        self.assertEqual(field_dict["PIN"], "1111")  # Survivor value preserved
        self.assertEqual(field_dict["SecurityQuestion1"], "Fluffy")
        self.assertEqual(field_dict["RecoveryKey"], "REC-999")
        self.assertEqual(field_dict["BackupPhone"], "+15551234")

    # ------------------ Note Merging Permutations ------------------

    def test_notes_merging_permutations(self):
        """Test note merging across empty notes, whitespace, duplicates, and distinct notes."""
        # Case 1: Survivor empty, duplicate has note
        survivor1 = self._create_item("s1", name="Master", notes=None)
        dup1 = self._create_item("d1", name="Backup", notes="My backup secret note")
        merged1 = merge_into_survivor(survivor1, [survivor1, dup1])
        self.assertIn("My backup secret note", merged1.notes)
        self.assertIn("Merged Note from [Backup]", merged1.notes)

        # Case 2: Survivor has note, duplicates have None or whitespace
        survivor2 = self._create_item("s2", notes="Original note")
        dup2a = self._create_item("d2a", notes=None)
        dup2b = self._create_item("d2b", notes="   ")
        merged2 = merge_into_survivor(survivor2, [survivor2, dup2a, dup2b])
        self.assertEqual(merged2.notes, "Original note")

        # Case 3: Survivor has note, duplicate has identical note
        survivor3 = self._create_item("s3", notes="Shared secret")
        dup3 = self._create_item("d3", notes="Shared secret")
        merged3 = merge_into_survivor(survivor3, [survivor3, dup3])
        self.assertEqual(merged3.notes, "Shared secret")

        # Case 4: Survivor and 2 duplicates each have distinct notes
        survivor4 = self._create_item("s4", name="Surv", notes="Note Surv")
        dup4a = self._create_item("d4a", name="DupA", notes="Note DupA")
        dup4b = self._create_item("d4b", name="DupB", notes="Note DupB")
        merged4 = merge_into_survivor(survivor4, [survivor4, dup4a, dup4b])
        self.assertIn("Note Surv", merged4.notes)
        self.assertIn("--- Merged Note from [DupA] ---\nNote DupA", merged4.notes)
        self.assertIn("--- Merged Note from [DupB] ---\nNote DupB", merged4.notes)

        # Case 5: All have empty notes
        survivor5 = self._create_item("s5", notes=None)
        dup5 = self._create_item("d5", notes="   ")
        merged5 = merge_into_survivor(survivor5, [survivor5, dup5])
        self.assertIsNone(merged5.notes)

    # ------------------ Multiple URI Unions ------------------

    def test_uri_append_consolidation(self):
        """Test that duplicate item URIs are appended to survivor URIs."""
        survivor = self._create_item("s1", uris=["https://example.com/login"])
        dup1 = self._create_item("d1", uris=[
            "https://sub.example.com",
            "https://app.example.com",
        ])
        dup2 = self._create_item("d2", uris=[
            "https://api.example.com",
            "",
            "https://sub.example.com",
        ])

        merged = merge_into_survivor(survivor, [survivor, dup1, dup2])
        merged_uris = [u.uri for u in merged.login.uris]
        self.assertEqual(len(merged_uris), 5)
        self.assertEqual(
            merged_uris,
            [
                "https://example.com/login",
                "https://sub.example.com",
                "https://app.example.com",
                "https://api.example.com",
                "https://sub.example.com",
            ],
        )

    # ------------------ TOTP Consolidation ------------------

    def test_totp_consolidation(self):
        """Test TOTP preservation and adoption."""
        # Survivor already has TOTP -> keep survivor's
        s1 = self._create_item("s1", totp="TOTP_SURVIVOR")
        d1 = self._create_item("d1", totp="TOTP_DUP")
        m1 = merge_into_survivor(s1, [s1, d1])
        self.assertEqual(m1.login.totp, "TOTP_SURVIVOR")

        # Survivor has no TOTP -> adopt first available from duplicates
        s2 = self._create_item("s2", totp=None)
        d2a = self._create_item("d2a", totp=None)
        d2b = self._create_item("d2b", totp="TOTP_DUP_B")
        d2c = self._create_item("d2c", totp="TOTP_DUP_C")
        m2 = merge_into_survivor(s2, [s2, d2a, d2b, d2c])
        self.assertEqual(m2.login.totp, "TOTP_DUP_B")

    # ------------------ Field Value Push ------------------

    def test_push_field_value_to_items(self):
        """Test pushing individual fields (name, username, password, totp, notes) across group items."""
        item1 = self._create_item("i1", name="N1", username="u1", password="p1", totp="t1", notes="not1")
        item2 = self._create_item("i2", name="N2", username="u2", password="p2", totp="t2", notes="not2")
        item3 = self._create_item("i3", name="N3", username="u3", password="p3", totp="t3", notes="not3")
        group = [item1, item2, item3]

        # Push password from i1 to all
        updated_pw = push_field_value_to_items(group, "i1", "password")
        for it in updated_pw:
            self.assertEqual(it.login.password, "p1")

        # Push totp from i2 to all
        updated_totp = push_field_value_to_items(group, "i2", "totp")
        for it in updated_totp:
            self.assertEqual(it.login.totp, "t2")

        # Push notes from i3 to all
        updated_notes = push_field_value_to_items(group, "i3", "notes")
        for it in updated_notes:
            self.assertEqual(it.notes, "not3")

        # Push name from i2 to all
        updated_name = push_field_value_to_items(group, "i2", "name")
        for it in updated_name:
            self.assertEqual(it.name, "N2")

        # Push username from i1 to all
        updated_user = push_field_value_to_items(group, "i1", "username")
        for it in updated_user:
            self.assertEqual(it.login.username, "u1")

        # Push with non-existent source item id
        same_group = push_field_value_to_items(group, "non-existent-id", "password")
        self.assertEqual([it.id for it in same_group], ["i1", "i2", "i3"])

    def test_merge_into_survivor_without_login(self):
        """Item without login payload returns unchanged when merged."""
        survivor = BitwardenItem(id="no-login-surv", name="Secure Note Item", login=None)
        dup = self._create_item("d1")
        merged = merge_into_survivor(survivor, [survivor, dup])
        self.assertIsNone(merged.login)
        self.assertEqual(merged.id, "no-login-surv")


class TestDiffMatrixAndGroupingPermutations(unittest.TestCase):
    """Exhaustive tests for compute_group_diffs across all individual and combined field differences."""

    def _make_item(
        self,
        item_id: str,
        name: str = "Common Name",
        username: str = "common@example.com",
        password: str = "CommonPass123!",
        totp: str = "COMMON_TOTP",
        notes: str = "Common note text",
        uris: list = None,
        passkeys: list = None,
    ) -> BitwardenItem:
        uri_objs = [URI(uri=u) for u in uris] if uris is not None else [URI(uri="https://example.com")]
        passkey_objs = [
            Fido2Credential(credentialId=p, rpId="example.com", userHandle="h")
            for p in (passkeys or [])
        ]
        return BitwardenItem(
            id=item_id,
            name=name,
            notes=notes,
            login=LoginInfo(
                username=username,
                password=password,
                totp=totp,
                uris=uri_objs,
                fido2Credentials=passkey_objs,
            ),
        )

    def test_diff_matrix_empty_and_single_item(self):
        """0 and 1 item groups should produce empty diff lists."""
        diffs_0, flags_0 = compute_group_diffs([])
        self.assertEqual(diffs_0, [])
        self.assertEqual(flags_0, [])

        diffs_1, flags_1 = compute_group_diffs([self._make_item("i1")])
        self.assertEqual(diffs_1, [])
        self.assertEqual(flags_1, [{}])

    def test_diff_matrix_identical_items(self):
        """2 and 3 identical items should produce no differences."""
        i1 = self._make_item("i1")
        i2 = self._make_item("i2")
        i3 = self._make_item("i3")

        diffs, flags = compute_group_diffs([i1, i2, i3])
        self.assertEqual(diffs, [])
        self.assertEqual(flags, [{}, {}, {}])

    def test_diff_matrix_each_single_field_in_isolation(self):
        """Test each of the 7 tracked fields differing individually between 2 items."""
        fields_to_test = [
            ("name", {"name": "Different Name"}, "name"),
            ("username", {"username": "different@example.com"}, "username"),
            ("password", {"password": "DifferentPass456!"}, "password"),
            ("totp", {"totp": "DIFFERENT_TOTP"}, "totp"),
            ("notes", {"notes": "Different note text"}, "notes"),
            ("uris", {"uris": ["https://different.com"]}, "uris"),
            ("passkeys", {"passkeys": ["key-1"]}, "passkeys"),
        ]

        for field_name, kwargs, expected_diff in fields_to_test:
            with self.subTest(differing_field=field_name):
                base = self._make_item("base")
                modified = self._make_item("modified", **kwargs)

                diffs, flags = compute_group_diffs([base, modified])
                self.assertEqual(
                    diffs,
                    [expected_diff],
                    f"Expected diff '{expected_diff}' for field '{field_name}', got {diffs}",
                )
                self.assertEqual(flags[0], {expected_diff: True})
                self.assertEqual(flags[1], {expected_diff: True})

    def test_diff_matrix_all_fields_differing(self):
        """When all 7 fields differ simultaneously, all should be flagged."""
        i1 = self._make_item(
            "i1",
            name="Name A",
            username="user_a@test.com",
            password="pass_a",
            totp="totp_a",
            notes="note_a",
            uris=["https://a.test.com"],
            passkeys=[],
        )
        i2 = self._make_item(
            "i2",
            name="Name B",
            username="user_b@test.com",
            password="pass_b",
            totp="totp_b",
            notes="note_b",
            uris=["https://b.test.com"],
            passkeys=["key-b"],
        )

        diffs, flags = compute_group_diffs([i1, i2])
        expected = ["name", "notes", "passkeys", "password", "totp", "uris", "username"]
        self.assertEqual(diffs, expected)
        self.assertEqual(len(flags), 2)
        for flag_dict in flags:
            self.assertEqual(sorted(flag_dict.keys()), expected)

    def test_diff_matrix_3_rows_permutations(self):
        """Test combinations across 3 items where differences appear in only one duplicate."""
        # Row 0 and 1 have same password, row 2 has different
        i0 = self._make_item("i0", password="pass_common")
        i1 = self._make_item("i1", password="pass_common")
        i2 = self._make_item("i2", password="pass_divergent")
        diffs, flags = compute_group_diffs([i0, i1, i2])
        self.assertEqual(diffs, ["password"])
        self.assertEqual(len(flags), 3)

        # Row 0 has 1 passkey, row 1 has 1 passkey, row 2 has 0 passkeys
        i0_pk = self._make_item("i0", passkeys=["pk1"])
        i1_pk = self._make_item("i1", passkeys=["pk1"])
        i2_pk = self._make_item("i2", passkeys=[])
        diffs_pk, flags_pk = compute_group_diffs([i0_pk, i1_pk, i2_pk])
        self.assertEqual(diffs_pk, ["passkeys"])

        # Row 1 differs in name, row 2 differs in totp
        i0_combo = self._make_item("i0", name="N0", totp="T0")
        i1_combo = self._make_item("i1", name="N1", totp="T0")
        i2_combo = self._make_item("i2", name="N0", totp="T2")
        diffs_combo, flags_combo = compute_group_diffs([i0_combo, i1_combo, i2_combo])
        self.assertEqual(diffs_combo, ["name", "totp"])

    def test_diff_matrix_5_rows_permutations(self):
        """Test permutations across 5 duplicate rows."""
        # 5 items where:
        # - name is identical for rows 0..3, different for row 4
        # - password alternates: pw1, pw1, pw2, pw2, pw3
        # - passkey counts: row 0 has 2, rows 1..4 have 2, row 3 has 1
        # - notes: whitespace-only difference between rows 0 and 1, real difference on row 4
        items = [
            self._make_item("r0", name="App", password="p1", passkeys=["k1", "k2"], notes="note test"),
            self._make_item("r1", name="App", password="p1", passkeys=["k1", "k2"], notes="  note test  "),
            self._make_item("r2", name="App", password="p2", passkeys=["k1", "k2"], notes="note test"),
            self._make_item("r3", name="App", password="p2", passkeys=["k1"],       notes="note test"),
            self._make_item("r4", name="App Alternate", password="p3", passkeys=["k1", "k2"], notes="completely different note"),
        ]

        diffs, flags = compute_group_diffs(items)
        # Note: 'note test' stripped matches '  note test  ' stripped, but row 4 has completely different note
        expected_diffs = ["name", "notes", "passkeys", "password"]
        self.assertEqual(diffs, expected_diffs)
        self.assertEqual(len(flags), 5)
        for f in flags:
            self.assertEqual(sorted(f.keys()), expected_diffs)

    def test_analyze_vault_grouping_and_summaries(self):
        """End-to-end integration test of analyze_vault with multiple domains, passkeys, and singletons."""
        items = [
            # Google domain - account 1 (2 duplicates)
            self._make_item("g1", name="Google 1", username="alice@gmail.com", uris=["https://accounts.google.com"], passkeys=["pk-g1"]),
            self._make_item("g2", name="Google 2", username="Alice+work@googlemail.com", uris=["https://google.com"]),

            # Google domain - account 2 (singleton / unique item)
            self._make_item("g3", name="Google Dev", username="developer@company.com", uris=["https://google.com"]),

            # Amazon UK domain - account 1 (3 duplicates)
            self._make_item("a1", name="Amazon 1", username="shopper", password="pwA", uris=["https://amazon.co.uk"]),
            self._make_item("a2", name="Amazon 2", username="shopper", password="pwB", uris=["https://sub.amazon.co.uk"]),
            self._make_item("a3", name="Amazon 3", username="shopper", password="pwC", uris=["https://portal.amazon.co.uk"]),

            # GitHub domain - unique singleton
            self._make_item("gh1", name="GitHub", username="octocat", uris=["https://github.com"]),

            # Bare item with no URIs
            self._make_item("bare1", name="Router Admin", username="admin", uris=[]),
        ]

        folders = [BitwardenFolder(id="f1", name="Personal")]

        duplicate_domains, unique_items, domain_summaries = analyze_vault(items, folders)

        # duplicate_domains should contain google.com and amazon.co.uk
        self.assertIn("google.com", duplicate_domains)
        self.assertIn("amazon.co.uk", duplicate_domains)
        self.assertNotIn("github.com", duplicate_domains)

        # Google domain properties
        g_group = duplicate_domains["google.com"]
        self.assertEqual(g_group.totalAccounts, 1)
        self.assertEqual(g_group.totalItems, 2)
        self.assertTrue(g_group.hasPasskeys)
        self.assertEqual(g_group.accounts[0].normalizedUsername, "alice@gmail.com")
        self.assertTrue(g_group.accounts[0].hasPasskeys)

        # Amazon UK domain properties
        a_group = duplicate_domains["amazon.co.uk"]
        self.assertEqual(a_group.totalAccounts, 1)
        self.assertEqual(a_group.totalItems, 3)
        self.assertFalse(a_group.hasPasskeys)
        self.assertIn("password", a_group.accounts[0].diffFields)

        # Unique items count: g3, gh1, bare1 = 3 unique items
        unique_ids = {u.id for u in unique_items}
        self.assertEqual(unique_ids, {"g3", "gh1", "bare1"})

        # Domain summaries: sorted by totalItems desc (amazon.co.uk has 3, google.com has 2)
        self.assertEqual(len(domain_summaries), 2)
        self.assertEqual(domain_summaries[0].domain, "amazon.co.uk")
        self.assertEqual(domain_summaries[1].domain, "google.com")

    def test_analyze_vault_items_with_no_username(self):
        """Test grouping duplicate items that have empty or None username."""
        item1 = BitwardenItem(
            id="nw1",
            name="Office Wi-Fi",
            login=LoginInfo(uris=[URI(uri="https://router.local")], username=None, password="p1"),
        )
        item2 = BitwardenItem(
            id="nw2",
            name="Office Wi-Fi",
            login=LoginInfo(uris=[URI(uri="https://router.local")], username="   ", password="p2"),
        )
        dup_domains, unique_items, summaries = analyze_vault([item1, item2], [])
        self.assertIn("router.local", dup_domains)
        acct = dup_domains["router.local"].accounts[0]
        self.assertTrue(acct.normalizedUsername.startswith("_no_username_"))
        self.assertEqual(acct.displayUsername, "(No Username)")

    def test_compute_group_diffs_items_without_login(self):
        """Test compute_group_diffs handling items where login is None."""
        it1 = BitwardenItem(id="n1", name="Note 1", notes="Same note", login=None)
        it2 = BitwardenItem(id="n2", name="Note 2", notes="Same note", login=None)
        diffs, flags = compute_group_diffs([it1, it2])
        self.assertEqual(diffs, ["name"])
        self.assertEqual(flags[0], {"name": True})


if __name__ == "__main__":
    unittest.main()
