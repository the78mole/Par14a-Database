"""Gemeinsame Hilfen: scripts/ importierbar machen, CSV-Dateien lesen."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

JAHRE = sorted(p.name for p in (ROOT / "data").iterdir() if p.is_dir() and p.name.isdigit())


def lies(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
