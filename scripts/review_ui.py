#!/usr/bin/env python3
"""Step E: local table UI for human review and publish."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    p = argparse.ArgumentParser(description="Launch staging review UI (Step E only)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()

    from generator.review.web_app import create_app

    app = create_app(ROOT)
    print(f"Review UI → http://{args.host}:{args.port}/")
    print("Step D 过滤请仍用: python scripts/filter_candidates.py --batch <id>")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
