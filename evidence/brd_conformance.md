# BRD conformance — NotifySvc

Maps every requirement in [docs/BRD.md](../docs/BRD.md) to its implementation and
the test(s) that prove it. Generated as delivery evidence under the `notify.nyx`
evidence contract.

## Functional requirements

| Req | Requirement | Implementation | Test |
|-----|-------------|----------------|------|
| FR-1 | `POST /routes`, unique `(event, channel)`, names `^[a-z0-9-]+$`, dup → 409 | `app/main.py::create_route`, `app/models.py::Route`, `app/store.py::RouteStore.create` | `test_create_and_get_event_routes`, `test_create_duplicate_conflicts`, `test_invalid_name_pattern_422` |
| FR-2 | `GET /routes` lists all in stable order | `app/main.py::list_routes`, `RouteStore.list` | `test_list_routes_stable_order` |
| FR-3 | `GET /routes/{event}` ordered by channel | `app/main.py::get_event_routes`, `RouteStore.for_event` | `test_create_and_get_event_routes` |
| FR-4 | `PATCH /routes/{event}/{channel}`, unknown → 404 | `app/main.py::update_route`, `RouteStore.update` | `test_update_route`, `test_update_unknown_route_404` |
| FR-5 | `POST /route` deterministic channels | `app/main.py::route_notification`, `app/routing.py` | `test_route_notification_full_channels`, `test_route_notification_skips_disabled`, `test_partial_sample_is_deterministic`, `test_partial_sample_approximates_percentage` |
| FR-6 | `DELETE /routes/{event}/{channel}` → 204, unknown → 404 | `app/main.py::delete_route`, `RouteStore.delete` | `test_delete_route`, `test_delete_unknown_route_404` |
| FR-7 | `GET /health` → `{status:"ok"}` | `app/main.py::health` | `test_health` |

## Non-functional requirements

| Req | Requirement | Evidence |
|-----|-------------|----------|
| NFR-1 | `sample_percent` 0–100, invalid → 422 | `app/models.py` field bounds; `test_invalid_sample_percent_422` |
| NFR-2 | Routing pure and deterministic (no randomness/clock) | `app/routing.py` (SHA-256 bucket, no `random`/`time`); `test_partial_sample_is_deterministic`, `test_bucket_is_stable_and_in_range` |
| NFR-3 | No secrets, no network, no credentials | in-memory only; no network calls in `app/` |
| NFR-4 | Every change ships with green tests | 23 passing tests; CI runs `pytest -q` |

## Governance constraints

| Req | Constraint | Evidence |
|-----|-----------|----------|
| G-1 | `deny secrets_to_llm` | generated `policy.yaml`; `test_generated_policy_carries_org_rules` |
| G-2 | `require tests_if_code_changed` | generated `policy.yaml`; same test |
| G-3 | `deny nondeterministic_evaluation` | deterministic `app/routing.py`; `test_routing.py` |
| G-4 | `require human_approval_before_merge` | `evidence/approval_log.json`; generated `policy.yaml` |
| G-5 | Control artifacts generated from one `.nyx`, no drift | `scripts/check_drift.py` (full-output `nornyx drift`); `test_no_drift_between_contract_and_generated_artifacts` |

## Cross-repo governance
`notify.nyx`'s `SafeDeliveryPolicy` is byte-identical to the canonical org policy
in `agenticnetworks-governance`; `nornyx workspace-check` reports **pass** for both
`govflags.nyx` and `notify.nyx`.
