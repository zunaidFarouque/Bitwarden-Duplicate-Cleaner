import os
import sys
import time
import subprocess
import webbrowser
import threading

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"


def switch_to_venv_if_available():
    """If running outside a virtualenv but .venv exists, seamlessly switch to it."""
    if sys.prefix == sys.base_prefix:
        venv_dir = os.path.join(os.path.dirname(__file__), ".venv")
        if sys.platform == "win32":
            venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            venv_python = os.path.join(venv_dir, "bin", "python")

        if os.path.isfile(venv_python) and os.path.abspath(sys.executable) != os.path.abspath(venv_python):
            print("[*] Re-launching inside isolated virtual environment (.venv)...")
            try:
                # Use subprocess to run within venv and exit
                ret = subprocess.call([venv_python] + sys.argv)
                sys.exit(ret)
            except Exception as e:
                print(f"[!] Could not switch to .venv automatically: {e}")


def ensure_dependencies():
    """Checks if dependencies are installed; installs them automatically if missing."""
    packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("multipart", "python-multipart"),
    ]
    needs_install = False
    for mod, _ in packages:
        try:
            __import__(mod)
        except ImportError:
            needs_install = True
            break

    if needs_install:
        print("=" * 65)
        print("  [*] First-time setup: Installing dependencies into virtual environment...")
        print("=" * 65)
        req_path = os.path.join(os.path.dirname(__file__), "backend", "requirements.txt")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
            print("\n[+] Dependencies successfully installed!\n")
        except Exception as e:
            print(f"\n[!] Automatic dependency installation failed: {e}")
            print("    Please run: pip install -r backend/requirements.txt")
            sys.exit(1)


def open_browser():
    time.sleep(1.2)
    print(f"\n[+] Opening Bitwarden Duplicate Cleaner in your browser: {URL}\n")
    try:
        webbrowser.open(URL)
    except Exception as e:
        print(f"Could not automatically open browser: {e}")


def main():
    switch_to_venv_if_available()
    ensure_dependencies()

    import uvicorn

    print("=" * 65)
    print("      Bitwarden Duplicate Cleaner - Privacy First & Local")
    print("=" * 65)
    print(f"[*] Offline Mode: Binding strictly to {HOST}:{PORT}")
    print("[*] No data leaves your machine. 100% air-gapped security.")
    if sys.prefix != sys.base_prefix:
        print(f"[*] Running in isolated virtual environment: {sys.prefix}")
    print("[*] Press Ctrl+C at any time to shut down the server.")
    print("=" * 65)

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        "backend.app.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
