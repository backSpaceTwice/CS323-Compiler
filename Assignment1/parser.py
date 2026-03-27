"""
Assignment 2 parser launcher from inside Assignment1.

Usage:
  python parser.py <input_file> <output_file>

This forwards to the root-level parser implementation.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT_PARSER = Path(__file__).resolve().parent.parent / "parser.py"
_spec = importlib.util.spec_from_file_location("root_parser", ROOT_PARSER)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load parser from {ROOT_PARSER}")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python parser.py <input_file> <output_file>")
        sys.exit(1)

    ok = _mod.parse_file(sys.argv[1], sys.argv[2], print_switch=_mod.print_switch)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
