import sys
import time
import webbrowser
import threading
import uvicorn

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"


def open_browser():
    time.sleep(1.2)
    print(f"\n[+] Opening Bitwarden Duplicate Cleaner in your browser: {URL}\n")
    try:
        webbrowser.open(URL)
    except Exception as e:
        print(f"Could not automatically open browser: {e}")


def main():
    print("=" * 65)
    print("      Bitwarden Duplicate Cleaner - Privacy First & Local")
    print("=" * 65)
    print(f"[*] Offline Mode: Binding strictly to {HOST}:{PORT}")
    print("[*] No data leaves your machine. 100% air-gapped security.")
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
