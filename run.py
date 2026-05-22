"""
run.py — Single launcher for backend + client streamer + optional frontend dev server.
Usage:
  python run.py                  # backend + mic client
  python run.py --frontend       # backend + frontend dev server (no mic client)
  python run.py --session test-1 # backend + mic client with custom session
"""
import subprocess
import sys
import time
import argparse
import signal
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_CMD  = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CLIENT_CMD   = [sys.executable, "client_streamer.py"]
FRONTEND_DIR = os.path.join(ROOT, "frontend")
FRONTEND_CMD = ["npm", "run", "dev"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="test-1")
    parser.add_argument("--frontend", action="store_true", help="Start Vite dev server instead of mic client")
    args = parser.parse_args()

    procs = []

    print("[launcher] Starting backend...")
    backend = subprocess.Popen(BACKEND_CMD, cwd=ROOT)
    procs.append(backend)

    print("[launcher] Waiting for backend to start (5s)...")
    time.sleep(5)

    if args.frontend:
        print("[launcher] Starting frontend dev server on http://localhost:5173 ...")
        frontend = subprocess.Popen(FRONTEND_CMD, cwd=FRONTEND_DIR, shell=True)
        procs.append(frontend)
        print("[launcher] Open http://localhost:5173 in your browser.")
    else:
        print("[launcher] Starting client streamer...")
        client = subprocess.Popen(CLIENT_CMD + ["--session", args.session], cwd=ROOT)
        procs.append(client)

    def _shutdown(sig, frame):
        print("\n[launcher] Shutting down...")
        for p in procs:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        for p in procs:
            if p.poll() is not None:
                print("[launcher] A process exited. Stopping all...")
                for q in procs:
                    q.terminate()
                return
        time.sleep(1)

if __name__ == "__main__":
    main()
