#!/usr/bin/env python3
"""
Canvas Learning System - Backend Server Startup Script

This script starts the FastAPI backend server for the Canvas Learning System.
Can be used standalone or invoked by the Obsidian plugin.

Usage:
    python start_server.py [--port PORT] [--host HOST]

Default:
    Host: 127.0.0.1
    Port: 8001
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


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
        default=8001,
        help="Port to bind to (default: 8001)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    # Import uvicorn here to avoid import errors if not installed
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is not installed. Run: pip install uvicorn[standard]")
        sys.exit(1)

    print("Starting Canvas Learning System Backend...")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Reload: {args.reload}")
    print(f"  API Docs: http://{args.host}:{args.port}/docs")
    print()

    # Run the server
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
