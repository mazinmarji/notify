#!/usr/bin/env python3
"""Drift gate for NotifySvc (BRD G-5).

Uses Nornyx's full-output drift gate (`nornyx drift`), which compares EVERY
generated artifact by hash — not just AGENTS.md. (The earlier AGENTS.md-only
gate was blind to policy.yaml changes; this one is not — it's the same Gap-2
fix GovFlags adopted.) Also confirms the root AGENTS.md (the copy tools read)
matches the generated one.

Usage: python scripts/check_drift.py   (exit 0 = in sync, 1 = drift)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "notify.nyx"
GEN_DIR = ROOT / ".nyx-out"
ROOT_AGENTS = ROOT / "AGENTS.md"


def main() -> int:
    drift = subprocess.run(
        [sys.executable, "-m", "nornyx.cli", "drift", str(CONTRACT), "--out", str(GEN_DIR)],
        cwd=ROOT,
    )
    if drift.returncode != 0:
        return 1
    # The root AGENTS.md is a copy of the generated one; keep them identical.
    if ROOT_AGENTS.read_text(encoding="utf-8") != (GEN_DIR / "AGENTS.md").read_text(encoding="utf-8"):
        sys.stderr.write("Root AGENTS.md differs from .nyx-out/AGENTS.md; re-copy it.\n")
        return 1
    print("Drift gate OK: all generated artifacts and root AGENTS.md match notify.nyx.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
