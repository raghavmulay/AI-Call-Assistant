"""
run.py — Single launcher for backend + client streamer.
Usage: python run.py [--session test-1]
"""
import subprocess
import sys
import time
import argparse
import signal
import os

BACKEND_CMD = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CLIENT_CMD  = [sys.executable, "client_streamer.py"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="test-1")
    args = parser.parse_args()

    client_cmd = CLIENT_CMD + ["--session", args.session]

    print("[launcher] Starting backend...")
    backend = subprocess.Popen(BACKEND_CMD, cwd=os.path.dirname(os.path.abspath(__file__)))

    # Wait for backend to be ready
    print("[launcher] Waiting for backend to start (5s)...")
    time.sleep(5)

    print("[launcher] Starting client streamer...")
    client = subprocess.Popen(client_cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    def _shutdown(sig, frame):
        print("\n[launcher] Shutting down...")
        client.terminate()
        backend.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Wait for either process to exit
    while True:
        if backend.poll() is not None:
            print("[launcher] Backend exited. Stopping client...")
            client.terminate()
            break
        if client.poll() is not None:
            print("[launcher] Client exited. Stopping backend...")
            backend.terminate()
            break
        time.sleep(1)

if __name__ == "__main__":
    main()
