#!/usr/bin/env python3
"""Backward-compatible entrypoint for visa text corruption checks.

Delegates to scripts/check_visa_data_text_integrity.py.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    target = Path(__file__).with_name("check_visa_data_text_integrity.py")
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
