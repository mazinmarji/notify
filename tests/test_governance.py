"""Governance conformance: the repo honours its own Nornyx contract.

These tests make the BRD's governance constraints (G-1..G-5) executable so they
can't silently rot:
- the contract passes `nornyx check`;
- the committed control artifacts are exactly what `notify.nyx` generates (G-5,
  whole-output drift, not just AGENTS.md);
- the generated policy carries the rules the org standard requires (G-1..G-4).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "notify.nyx"


def _nornyx(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "nornyx.cli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_contract_passes_nornyx_check():
    result = _nornyx("check", str(CONTRACT))
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_drift_between_contract_and_generated_artifacts():  # G-5 (whole output)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_drift.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_generated_policy_carries_org_rules(tmp_path):  # G-1..G-4
    out = tmp_path / "gen"
    gen = _nornyx("generate", str(CONTRACT), "--out", str(out))
    assert gen.returncode == 0, gen.stdout + gen.stderr
    policy = (out / "policy.yaml").read_text(encoding="utf-8")
    for rule in (
        "deny secrets_to_llm",                    # G-1
        "require tests_if_code_changed",          # G-2
        "deny nondeterministic_evaluation",       # G-3
        "require evidence_if_harness_completed",  # evidence
        "require human_approval_before_merge",    # G-4
    ):
        assert rule in policy, f"missing policy rule: {rule}"
