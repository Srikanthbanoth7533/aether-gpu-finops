"""
AetherFin GPU Ops: 24/7 Keep-Alive & Health Monitoring Daemon
Pings the Render backend and Vercel frontend periodically to prevent
Render free tier spin-down and ensure zero-latency 24/7 responsiveness.
"""

import time
import datetime
import urllib.request
import urllib.error
import sys

BACKEND_URLS = [
    "https://aetherfin-gpu-ops-backend.onrender.com/",
    "https://aetherfin-gpu-ops-backend.onrender.com/api/nodes"
]
FRONTEND_URL = "https://frontend-sandy-seven-n9m6mrso9h.vercel.app"
INTERVAL_SECONDS = 600  # 10 minutes (well under Render's 15-minute sleep threshold)

def ping(url: str, timeout: int = 25) -> tuple[bool, int, float, str]:
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AetherFin-FinOps-KeepAlive/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            elapsed = round((time.time() - start) * 1000, 1)
            return True, res.status, elapsed, "OK"
    except urllib.error.HTTPError as e:
        elapsed = round((time.time() - start) * 1000, 1)
        return False, e.code, elapsed, str(e.reason)
    except Exception as e:
        elapsed = round((time.time() - start) * 1000, 1)
        return False, 0, elapsed, str(e)

def run_single_check() -> dict:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results = {"timestamp": timestamp, "checks": []}
    
    print(f"\n[{timestamp}] Running 24/7 Keep-Alive Health Probe:")
    
    # 1. Probe Backend Endpoints
    for url in BACKEND_URLS:
        success, status, latency, reason = ping(url)
        tag = "[BACKEND OK]" if success else "[BACKEND FAILED]"
        print(f"  {tag:16} {url} | Status: {status} | Latency: {latency}ms")
        results["checks"].append({
            "target": "backend",
            "url": url,
            "success": success,
            "status": status,
            "latency_ms": latency
        })
        
    # 2. Probe Frontend Endpoint
    success, status, latency, reason = ping(FRONTEND_URL)
    tag = "[FRONTEND OK]" if success else "[FRONTEND FAILED]"
    print(f"  {tag:16} {FRONTEND_URL} | Status: {status} | Latency: {latency}ms")
    results["checks"].append({
        "target": "frontend",
        "url": FRONTEND_URL,
        "success": success,
        "status": status,
        "latency_ms": latency
    })
    
    return results

def start_daemon():
    print(f"=== Starting AetherFin 24/7 Keep-Alive Daemon ===")
    print(f"Interval: Every {INTERVAL_SECONDS // 60} minutes")
    print(f"Target Backend : {BACKEND_URLS[0]}")
    print(f"Target Frontend: {FRONTEND_URL}")
    print(f"Press Ctrl+C to terminate.\n")
    
    try:
        while True:
            run_single_check()
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nDaemon terminated by user.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_single_check()
    else:
        start_daemon()
