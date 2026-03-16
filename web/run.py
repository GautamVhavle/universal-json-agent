#!/usr/bin/env python
"""
Entry point — start the FastAPI JSON Agent server.

Usage:
    python -m web.run              # default: 127.0.0.1:8000
    python -m web.run --port 3000  # custom port
"""

from __future__ import annotations

import argparse
import logging
import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="JSON Agent Web Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (use 0.0.0.0 for LAN access)",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on changes")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:     %(name)s - %(message)s",
    )

    uvicorn.run(
        "web.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
