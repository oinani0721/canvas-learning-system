#!/usr/bin/env python3
"""
Canvas Learning System - Backend Server Startup Script

This script starts the FastAPI backend server for the Canvas Learning System.
Can be used standalone or invoked by the Obsidian plugin.

Features:
    - Auto-detects DEBUG mode from .env → enables hot-reload automatically
    - Detects and kills stale processes on the target port before starting
    - Watches .env file changes when reload is enabled

Usage:
    python start_server.py [--port PORT] [--host HOST] [--no-reload]

Default:
    Host: 127.0.0.1
    Port: 8001
"""

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def _read_debug_from_env() -> bool:
    """Read DEBUG flag from .env file without importing the full app."""
    env_file = backend_dir / ".env"
    if not env_file.exists():
        return False
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DEBUG="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'").lower()
            return val in ("true", "1", "yes")
    return False


def _is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _kill_stale_process(port: int) -> bool:
    """Find and kill the process occupying the given port. Returns True if killed."""
    if sys.platform == "win32":
        try:
            # netstat -ano | findstr :PORT
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, timeout=5
            )
            pids = set()
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) != os.getpid():
                            pids.add(pid)

            if not pids:
                return False

            for pid in pids:
                print(f"  Killing stale process PID {pid} on port {port}...")
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid],
                    capture_output=True, timeout=5
                )
            return True
        except Exception as e:
            print(f"  Warning: Failed to kill stale process: {e}")
            return False
    else:
        # Unix: lsof + kill
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True, timeout=5
            )
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid.strip().isdigit():
                    print(f"  Killing stale process PID {pid} on port {port}...")
                    subprocess.run(["kill", "-9", pid], timeout=5)
            return bool(pids and pids[0].strip())
        except Exception:
            return False


def main():
    """Main entry point for the server startup script."""
    parser = argparse.ArgumentParser(
        description="Canvas Learning System Backend Server"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (auto-enabled when DEBUG=True in .env)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Force disable auto-reload even in DEBUG mode"
    )

    args = parser.parse_args()

    # Import uvicorn here to avoid import errors if not installed
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is not installed. Run: pip install uvicorn[standard]")
        sys.exit(1)

    # Auto-enable reload in DEBUG mode (unless --no-reload)
    is_debug = _read_debug_from_env()
    use_reload = (args.reload or is_debug) and not args.no_reload

    # --- Port conflict resolution ---
    if _is_port_in_use(args.port):
        print(f"[!] Port {args.port} is already in use.")
        if _kill_stale_process(args.port):
            print(f"[OK] Stale process cleared. Proceeding with startup.")
            import time
            time.sleep(1)  # Brief pause for port release
        else:
            print(f"[!] Could not clear port {args.port}. Server may fail to bind.")

    print("Starting Canvas Learning System Backend...")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Reload: {use_reload}" + (" (auto: DEBUG=True)" if is_debug and not args.reload else ""))
    print(f"  API Docs: http://{args.host}:{args.port}/docs")
    print()

    # Build uvicorn config
    uvicorn_kwargs = {
        "host": args.host,
        "port": args.port,
        "reload": use_reload,
        "log_level": "info",
    }

    if use_reload:
        # Watch .py files (default) + .env for config changes
        uvicorn_kwargs["reload_includes"] = ["*.py", ".env"]

    # Run the server
    uvicorn.run("app.main:app", **uvicorn_kwargs)


if __name__ == "__main__":
    main()
