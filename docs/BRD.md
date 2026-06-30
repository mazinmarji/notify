# Business Requirements Document — NotifySvc

## 1. Purpose
NotifySvc is a small, self-contained **notification-routing service**: teams
register routes that map an **event** type to a delivery **channel**, then resolve
which channels a notification for a given recipient goes to — including
**percentage sampling** of a channel that is deterministic per recipient. It is a
*second* product built **under the same Nornyx org policy** as GovFlags, to show
that one governance standard holds across more than one app.

## 2. Scope
**In scope:** an HTTP API to manage routes and resolve channels for a
notification; in-memory storage; a deterministic routing rule; a full test suite.
**Out of scope:** persistence/DB, auth, actually sending messages, retries,
multi-tenant, UI, deployment.

## 3. Functional requirements
- **FR-1 Create route:** `POST /routes` with `{event, channel, enabled?,
  sample_percent?}` → 201 + the route. `(event, channel)` is unique; both match
  `^[a-z0-9-]+$`; duplicate → 409.
- **FR-2 List routes:** `GET /routes` → all routes in stable `(event, channel)`
  order.
- **FR-3 Routes for event:** `GET /routes/{event}` → the routes for that event,
  ordered by channel.
- **FR-4 Update route:** `PATCH /routes/{event}/{channel}` with `{enabled?,
  sample_percent?}` → the updated route; unknown → 404.
- **FR-5 Route a notification:** `POST /route` with `{event, recipient_id}` →
  `{event, recipient_id, channels}`, the sorted channels the notification routes
  to.
  - A disabled route never contributes its channel.
  - `sample_percent == 100` → the channel always fires.
  - A partial sample → the channel fires **deterministically** per
    `(event, channel, recipient_id)` (same inputs always give the same answer)
    and the share of recipients routed to it approximates `sample_percent`.
- **FR-6 Delete route:** `DELETE /routes/{event}/{channel}` → 204; unknown → 404.
- **FR-7 Health:** `GET /health` → `{status:"ok"}`.

## 4. Non-functional requirements
- **NFR-1** `sample_percent` is an integer 0–100; invalid input → 422.
- **NFR-2** Routing is pure and deterministic (no randomness, no clock).
- **NFR-3** No secrets, no external network calls, no credential handling.
- **NFR-4** Every code change ships with tests; the suite is green.

## 5. Data model
`Route { event: str, channel: str, enabled: bool, sample_percent: int (0..100) }`

## 6. Governance constraints (these come from the org `SafeDeliveryPolicy`)
- **G-1** No secrets are read or sent to any model/tool (`deny secrets_to_llm`).
- **G-2** Every code change requires tests (`require tests_if_code_changed`).
- **G-3** Routing logic must stay deterministic
  (`deny nondeterministic_evaluation` — no `random`/`time` in routing).
- **G-4** A change is only mergeable after tests pass and a human approves
  (`require human_approval_before_merge`).
- **G-5** The repo's control artifacts (AGENTS.md, policy, harness, …) are
  generated from one `.nyx` source and must not drift.

## 7. Acceptance criteria
- All FRs implemented; all NFRs satisfied.
- Deterministic sampling: resolving the same `(event, recipient_id)` twice is
  identical; across many recipients a 30% sample lands roughly a third on.
- Test suite green; drift gate passes; control artifacts generated from
  `notify.nyx`.
- `notify.nyx`'s `SafeDeliveryPolicy` stays identical to the org standard in
  `agenticnetworks-governance` (verified by `nornyx workspace-check`).
