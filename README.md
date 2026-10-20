# 🛡️ Bitwarden Duplicate Cleaner

<div align="center">

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-v4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-59%20Passed-brightgreen.svg)]()
[![Air-Gapped](https://img.shields.io/badge/Privacy-100%25%20Air--Gapped-indigo.svg)]()

**A 100% local, privacy-first, passkey-safe web application for deduplicating, diffing, and consolidating Bitwarden password vaults with absolute peace of mind.**

[Quick Start](#-quick-start) • [How to Export Passkeys](#-how-to-export-from-bitwarden-with-passkeys) • [Key Features](#-key-features) • [Workflow](#-interactive-workflow) • [Testing](#-comprehensive-test-suite)

</div>

---

## 🌟 Key Features

- **🔒 100% Local & Air-Gapped**: Runs entirely on `127.0.0.1:8765`. Zero internet access, zero telemetry, zero analytics, and zero cloud calls. All CSS, JavaScript, and fonts are bundled locally. Your credentials never touch the network.
- **🔑 Hardware Passkey Protection & Validation**:
  - Automatically parses and detects hardware passkeys (`fido2Credentials`).
  - Includes an import safety check: *"I use passkeys in my vault"*. If checked but no passkeys are found in the export, an alert warns you before proceeding.
  - When merging duplicate entries, all unique hardware passkeys across duplicate rows are unioned into the survivor so no passkeys are ever lost.
- **🧠 Account-Level Smart Normalization**:
  - Groups subdomains and endpoints to their root domain (`accounts.google.com`, `mail.google.com` $\to$ `google.com`).
  - Separates multiple distinct accounts under the same website (e.g. personal vs. work) into their own distinct comparison tables.
  - Recognizes provider username nuances: on Google, `abc123`, `abc123@gmail.com`, and `abc.123+tag@googlemail.com` are recognized as the same account and grouped into one table.
- **🔍 Visual Diffing & Column Sync**:
  - Highlights discrepant values (differing passwords, usernames, notes, TOTPs) in clear amber chips.
  - Direct plain-text password comparison in `font-mono` with one-click copy.
  - **Push Column Value (`⇄`)**: One-click sync button to propagate a chosen cell's value across all duplicate rows in that column.
  - **In-Place Row Editing**: Click `Edit` on any row to type or paste updated values with instant Save / Cancel.
- **🧹 Clean Dynamic Columns**:
  - Tables automatically hide empty columns if no duplicate row in that account possesses data for that field (e.g., if neither duplicate has TOTP, the TOTP column is omitted).
  - The **Unique Logins** page includes a **Three-Dots Menu (`⋮`)** allowing users to customize column visibility at any time.
- **🛡️ Survivor Consolidation & Password History**:
  - Pick your preferred master row.
  - Unions passkeys, appends non-empty URIs, merges notes, and automatically archives differing passwords to Bitwarden's `passwordHistory` so old credentials are never discarded.
  - Moves redundant entries to **Trash (Deleted Items)**.
- **↩️ Full Transactional Undo & Redo**:
  - Every action (merge, edit, push, delete, restore) is tracked in an in-memory transaction journal (`Ctrl+Z` / `Ctrl+Y`).
  - Inspect the **Deleted Items** tab at any time to restore soft-deleted items with 1 click before final export.
- **⚡ 1-Click Interactive Demo**:
  - Test out the application instantly without uploading your real vault using the built-in **"Load Demo Vault"** button.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+**
- Modern Web Browser (Chrome, Edge, Firefox, Brave, Safari)

### Installation & Launch

1. **Clone the repository:**
   ```bash
   git clone https://github.com/zunaidFarouque/Bitwarden-Duplicate-Cleaner.git
   cd Bitwarden-Duplicate-Cleaner
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Launch the application:**

   - **Windows:** Double-click `start.bat` or run:
     ```powershell
     python run.py
     ```

   - **macOS / Linux:**
     ```bash
     chmod +x start.sh
     ./start.sh
     ```

The local server will start on `http://127.0.0.1:8765` and automatically open your default browser.

---

## 📖 How to Export from Bitwarden with Passkeys

Passkeys are hardware-backed FIDO2 credentials. To ensure they are preserved in your export:

> [!CAUTION]
> **Never export as CSV if you use passkeys!**  
> Bitwarden CSV exports **strip all passkeys**, custom fields, and password history. You must export as **JSON**.

### Recommended Export Steps:
1. Log in to the [Bitwarden Web Vault](https://vault.bitwarden.com) in your browser.
2. Click **Tools** in the top navigation bar.
3. Select **Export Vault** from the left navigation panel.
4. Set **File Format** to:
   - **`.json` (Unencrypted)** — *Recommended for local processing.*
   - *(Or `.json (Password-Protected)` if preferred).*
5. Enter your Master Password and click **Export Vault**.
6. Save the downloaded `.json` file to your computer.

---

## 🖥️ Interactive Workflow

```mermaid
flowchart LR
    A["1. Import JSON<br/>(Passkey Check)"] --> B["2. Review Sidebar<br/>(Domains & Accounts)"]
    B --> C["3. Inspect Account Tables<br/>(Visual Diffing)"]
    C --> D["4. Edit / Push Values / Pick Survivor"]
    D --> E["5. Consolidate into Survivor"]
    E --> F["6. Export Cleaned JSON"]
```

### 1. Import
- Drag & drop your Bitwarden `.json` file.
- Check *"I use passkeys in my Bitwarden vault"*.
- If you don't have a vault file handy, click **"Load Demo Vault"** to explore with pre-loaded mock data.

### 2. Compare & Diff
- Navigate the left sidebar by website domain.
- Each unique account under a domain has its own dedicated comparison table.
- Passwords are shown in plain text for easy comparison. Discrepancies are highlighted in amber.
- Hover over any cell to see full text in a tooltip if truncated.
- Hover over a discrepant cell to click `⇄` and push its value to all other duplicate rows.

### 3. Consolidate
- Select your preferred survivor row with the radio button.
- Click **"Consolidate into Survivor"**:
  - Combines all unique passkeys (`fido2Credentials`).
  - Appends non-empty URIs and notes.
  - Archives differing passwords to `passwordHistory`.
  - Sends redundant duplicate rows to **Trash**.

### 4. Re-Import Safely into Bitwarden
1. Click **Export Clean JSON** in the top navigation bar.
2. In the Bitwarden Web Vault, navigate to **Tools $\to$ Import Data**.
3. Choose format: **Bitwarden (JSON)**.
4. Select your downloaded `bitwarden_cleaned_export.json`.
5. *(Tip: Because Bitwarden appends imports, you can purge your vault under `Settings` $\to$ `My Account` $\to$ `Purge Vault` before importing, or import into a dedicated test folder/organization first).*

---

## 🧪 Comprehensive Test Suite

The project includes an exhaustive automated test suite covering unit tests, domain normalization permutations, username heuristics, passkey unions, state machine stress chains, and schema compliance:

```bash
# Run all 59 automated tests
python -m unittest discover tests
```

### Test Suite Breakdown:
- **`tests/test_core.py`**: Base parsing, passkey detection, diff calculation, and session undo/redo.
- **`tests/test_permutations_core.py`**: Exhaustive combinatorial tests covering all 28 country-code second-level domains (ccSLDs), subdomains, IPv4/localhost, app URIs, username heuristics, and passkey unions.
- **`tests/test_state_permutations.py`**: 12-step mutation stress chains, multi-domain isolation, branching history, and mathematical invariant verification.
- **`tests/test_bitwarden_export_schema.py`**: Round-trip import/export idempotency and official Bitwarden JSON schema validation for Logins, Cards, Secure Notes, and Identities.
- **`tests/test_api_integration.py`**: End-to-end FastAPI endpoint workflows and demo vault loading.

---

## 📁 Repository Structure

```
Bitwarden-Duplicate-Cleaner/
├── backend/
│   ├── app/
│   │   ├── consolidator.py     # Survivor merging (passkeys, password history, URIs)
│   │   ├── deduplicator.py     # Domain/account grouping & cell diff detector
│   │   ├── main.py             # FastAPI REST endpoints & static file server
│   │   ├── models.py           # Bitwarden schemas & UI DTOs
│   │   ├── normalizer.py       # eTLD+1 & provider username normalization
│   │   ├── parser.py           # Bitwarden JSON validator & backup generator
│   │   ├── session.py          # Session state manager & undo/redo stack
│   │   └── static/             # Pre-built production React bundle
│   └── requirements.txt        # Python backend dependencies
├── frontend/                   # React + TypeScript + Tailwind source code
│   ├── src/
│   │   ├── components/         # Table, Sidebar, Modals, Diff highlighters
│   │   ├── api/client.ts       # Typed API client
│   │   ├── types/              # TypeScript definitions
│   │   └── App.tsx             # Application shell
│   ├── package.json
│   └── vite.config.ts
├── demo/
│   └── sample_bitwarden_vault.json # Comprehensive 15-item sample vault
├── tests/                      # 59 automated tests
│   ├── test_core.py
│   ├── test_permutations_core.py
│   ├── test_state_permutations.py
│   ├── test_bitwarden_export_schema.py
│   └── test_api_integration.py
├── run.py                      # One-click Python runner
├── start.bat                   # Windows double-click launcher
├── start.sh                    # macOS / Linux launcher
├── LICENSE                     # MIT License
└── README.md
```

---

## 🔒 Security & Privacy Guarantee

- **No Remote Telemetry**: The application connects to no remote servers whatsoever.
- **Localhost Only**: The backend strictly binds to `127.0.0.1`.
- **Automatic Backup**: Every uploaded vault file is automatically preserved in an untouched, timestamped copy in `backups/` before any mutations take place.

---

## 📄 License

Distributed under the [MIT License](LICENSE). Copyright &copy; 2026 Zunaid Farouque.
