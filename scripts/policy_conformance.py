#!/usr/bin/env python3
"""Org-policy conformance for a single service repo (policy-ref model).

The contract (`*.nyx`) references the org `SafeDeliveryPolicy` with Nornyx's
`ref:` instead of copying its rules — the canonical rules are vendored in
`org-policy.yaml`, which this contract points at. So there is no copy of the
policy in the contract to drift.

- verify (default): fetch the canonical policy from the governance repo, then run
  `nornyx workspace-check`. workspace-check resolves the contract's `ref` (from the
  vendored file) and fails if the resolved policy diverges from canonical — i.e.
  if the vendored file is stale.
- `--write` (sync): refresh the vendored `org-policy.yaml` from canonical and
  regenerate the control artifacts so the within-repo drift gate stays green.

Uses only this repo's own permissions (no cross-repo token needed). Requires
Nornyx >= 1.3.0 (policy `ref`).
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
VENDORED_POLICY = "org-policy.yaml"  # the canonical policy this contract `ref`s
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
    ap.add_argument("--write", action="store_true", help="Refresh the vendored policy from canonical")
    ap.add_argument("--contract", help="Path to this repo's .nyx (default: auto-detect)")
    args = ap.parse_args()

    contract = Path(args.contract) if args.contract else _detect_contract()
    canonical = yaml.safe_load(_load(args.canonical))

    if args.write:
        # Refresh the single vendored file the contract references; regenerate so
        # the resolved rules flow into the committed artifacts.
        vendored = {
            "workspace": canonical.get("workspace", "AgenticNetworks"),
            "policies": canonical["policies"],
        }
        (ROOT / VENDORED_POLICY).write_text(
            yaml.safe_dump(vendored, sort_keys=False), encoding="utf-8"
        )
        subprocess.run(
            [sys.executable, "-m", "nornyx.cli", "generate", contract.name, "--out", ".nyx-out"],
            cwd=ROOT,
            check=True,
        )
        (ROOT / "AGENTS.md").write_text(
            (ROOT / ".nyx-out" / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
        return 0

    # verify: workspace-check resolves the contract's `ref` and compares to canonical.
    manifest = {
        "workspace": canonical.get("workspace", "AgenticNetworks"),
        "policies": canonical["policies"],
        "members": [{"path": contract.name}],
    }
    man_path = ROOT / MANIFEST_NAME
    man_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    try:
        rc = subprocess.run(
            [sys.executable, "-m", "nornyx.cli", "workspace-check", "--manifest", MANIFEST_NAME],
            cwd=ROOT,
        ).returncode
    finally:
        man_path.unlink(missing_ok=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
