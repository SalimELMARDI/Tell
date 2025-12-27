#!/usr/bin/env python3
"""Backwards-compatible entrypoint for tell."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from tell.cli import app


if __name__ == "__main__":
    app()
