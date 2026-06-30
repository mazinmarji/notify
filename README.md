# NotifySvc — a notification-routing API built **under Nornyx governance**

NotifySvc is a small, self-contained notification-routing service (create / list /
get / update / route / delete routes, with deterministic percentage sampling per
recipient). It is the **second** app governed by the AgenticNetworks org policy —
its purpose is to show that one [Nornyx](https://github.com/mazinmarji/nornyx)
governance standard (`SafeDeliveryPolicy`) holds across more than one repo, not
just inside [GovFlags](https://github.com/mazinmarji/govflags).

## The governed pipeline

```
docs/BRD.md  ──►  notify.nyx  ──►  nornyx generate  ──►  AGENTS.md + policy.yaml
 (requirements)   (the contract)    (deterministic)       harness/evals/context/
                                                          skills/evidence contract
                        │
                        └──►  nornyx check  +  scripts/check_drift.py  (CI gate)
                        │
                        └──►  nornyx workspace-check  (org-policy gate, run from
                              agenticnetworks-governance)
```

- **[docs/BRD.md](docs/BRD.md)** — business requirements (FR-1..FR-7, NFR-1..NFR-4,
  governance G-1..G-5).
- **[notify.nyx](notify.nyx)** — the single source of truth. Its
  `SafeDeliveryPolicy` is the org standard, owned by
  [agenticnetworks-governance](https://github.com/mazinmarji/agenticnetworks-governance);
  this repo carries a governed copy that `workspace-check` keeps identical.
- **[AGENTS.md](AGENTS.md)** — generated agent guidance at the repo root. Never
  hand-edited; the drift gate enforces it.
- **`.nyx-out/`** — full generated control artifact set (build output).

## The app

| Endpoint | Behaviour |
|----------|-----------|
| `POST /routes` | create a route (`event`/`channel` match `^[a-z0-9-]+$`); duplicate → 409 |
| `GET /routes` | list all routes |
| `GET /routes/{event}` | routes for one event, ordered by channel |
| `PATCH /routes/{event}/{channel}` | partial update; unknown → 404 |
| `POST /route` | `{event, recipient_id}` → deterministic sorted `channels` |
| `DELETE /routes/{event}/{channel}` | delete; 204; unknown → 404 |
| `GET /health` | `{"status":"ok"}` |

Routing is **deterministic**: a partial `sample_percent` fires per
`(event, channel, recipient_id)` via a stable SHA-256 bucket — no randomness, no
clock (NFR-2 / G-3).

## Run it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000/health
pytest -q                            # tests, including governance + drift
nornyx check notify.nyx              # contract is valid
nornyx drift notify.nyx --out .nyx-out   # control artifacts match the contract
```

## Governance

This app is governed two ways:
1. **Within-repo** — `scripts/check_drift.py` runs `nornyx drift` over the *whole*
   generated output (not just AGENTS.md), so a policy change can't pass silently.
2. **Across repos** — the `SafeDeliveryPolicy` block must stay byte-identical to
   the canonical one in `agenticnetworks-governance`; that repo's
   `nornyx workspace-check` fails if NotifySvc or GovFlags diverges.
