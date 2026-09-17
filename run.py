"""
ROADSense AI — Unified Local Execution Script
Runs FastAPI Backend (Port 8000) and Vite Frontend (Port 5173) concurrently.
"""
import subprocess
import sys
import os
import time
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_API_DIR = ROOT_DIR / "backend" / "api"
FRONTEND_DIR = ROOT_DIR / "frontend"

def main():
    print("=" * 70)
    print(" 🚀 ROADSense AI — Autonomous Road Infrastructure Intelligence")
    print(" PARAKRAM 1.0 (PK01PS001)")
    print("=" * 70)
    
    # Check Python executable
    python_cmd = sys.executable
    print(f"[*] Using Python: {python_cmd}")
    
    # 1. Start FastAPI Backend via uvicorn
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{BACKEND_API_DIR}{os.pathsep}{env.get('PYTHONPATH', '')}"
    
    backend_cmd = [
        python_cmd, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ]
    print(f"[*] Starting Backend at http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(ROOT_DIR), env=env)

    time.sleep(1.5)

    # 2. Start Vite Frontend
    print(f"[*] Starting Frontend Dev Server at http://localhost:5173 ...")
    npx_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_proc = subprocess.Popen([npx_cmd, "run", "dev"], cwd=str(FRONTEND_DIR))

    print("-" * 70)
    print(" ✅ All Services Running Successfully!")
    print(" 🌐 Frontend UI : http://localhost:5173")
    print(" 🔌 Backend API : http://127.0.0.1:8000")
    print(" 📖 API Docs    : http://127.0.0.1:8000/docs")
    print(" Press Ctrl+C to stop all services.")
    print("-" * 70)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n[!] Shutting down all services...")
    finally:
        try:
            backend_proc.terminate()
        except Exception:
            pass
        try:
            frontend_proc.terminate()
        except Exception:
            pass
        print("[+] Done.")

if __name__ == "__main__":
    main()
