#!/usr/bin/env python3
"""Org-policy conformance for a single service repo.

Fetches the canonical workspace manifest from the AgenticNetworks governance repo
(the single source of truth for `SafeDeliveryPolicy`), builds a one-member
manifest pointing at THIS repo's contract, and runs `nornyx workspace-check`.

- verify (default): exit nonzero if this repo's policy diverges from canonical.
- `--write` (sync): propagate the canonical policy into the contract, then
  regenerate the control artifacts so the within-repo drift gate stays green.

The canonical policy lives in ONE place (the governance repo); this repo never
stores a second copy — it fetches it fresh each run, so there is nothing here to
drift. Uses only this repo's own permissions (no cross-repo token needed).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANONICAL = (
    "https://raw.githubusercontent.com/mazinmarji/"
    "agenticnetworks-governance/main/nornyx.workspace.yaml"
)
MANIFEST_NAME = ".policy-conformance.yaml"


def _load(src: str) -> str:
    if src.startswith(("http://", "https://")):
        with urllib.request.urlopen(src, timeout=30) as resp:  # noqa: S310 (trusted gov repo)
            return resp.read().decode("utf-8")
    return Path(src).read_text(encoding="utf-8")


def _detect_contract() -> Path:
    candidates = sorted(ROOT.glob("*.nyx"))
    if len(candidates) != 1:
        sys.exit(f"expected exactly one top-level .nyx, found {[p.name for p in candidates]}")
    return candidates[0]


def main() -> int:
    ap = argparse.ArgumentParser(description="Check this repo's policy against the org standard.")
    ap.add_argument("--canonical", default=DEFAULT_CANONICAL, help="URL or path to the canonical manifest")
    ap.add_argument("--write", action="store_true", help="Sync the canonical policy into the contract")
    ap.add_argument("--contract", help="Path to this repo's .nyx (default: auto-detect)")
    args = ap.parse_args()

    contract = Path(args.contract) if args.contract else _detect_contract()
    canonical = yaml.safe_load(_load(args.canonical))
    manifest = {
        "workspace": canonical.get("workspace", "AgenticNetworks"),
        "policies": canonical["policies"],
        "members": [{"path": contract.name}],
    }
    man_path = ROOT / MANIFEST_NAME
    man_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    try:
        cmd = [sys.executable, "-m", "nornyx.cli", "workspace-check", "--manifest", MANIFEST_NAME]
        if args.write:
            cmd.append("--write")
        rc = subprocess.run(cmd, cwd=ROOT).returncode
    finally:
        man_path.unlink(missing_ok=True)

    if rc != 0:
        return rc
    if args.write:
        # Policy may have changed in the contract; refresh the generated artifacts
        # so the within-repo drift gate stays consistent.
        subprocess.run(
            [sys.executable, "-m", "nornyx.cli", "generate", contract.name, "--out", ".nyx-out"],
            cwd=ROOT,
            check=True,
        )
        (ROOT / "AGENTS.md").write_text(
            (ROOT / ".nyx-out" / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
