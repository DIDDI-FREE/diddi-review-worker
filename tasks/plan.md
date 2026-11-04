# Implementation plan

1. Bootstrap Python/FastAPI, settings and health endpoints.
2. Add actor contracts, JWT review validation and redaction.
3. Add typed HTTP adapters with idempotency and domain error mapping.
4. Add scenarios and run state machine with an in-memory repository for the first vertical slice.
5. Add API run lifecycle, tests, Docker and documentation.

The first implementation is intentionally contract-driven: endpoint paths and payloads are
configuration, while the runner owns orchestration state and never accesses business DBs.
# Plan: Reactive Google Play Review Assistant

## Scope

Convert the runner from a manually submitted review executor into a reactive,
read-only-observation assistant. It must act only after a trusted event from an
explicitly bound review account and must never act for the reviewer.

## Work order

1. Account bindings and safe event model.
2. Read-only poller contracts for Go, Send and Food.
3. Durable event ledger and lease for deduplication/restart safety.
4. Product-specific reaction handlers, only for confirmed public contracts.
5. API/worker wiring and operational metrics.
6. Contract/integration tests with mocked APIs; no shared staging missions.

## Current blockers

- Send has no public consumer delivery listing/webhook in the inspected OpenAPI.
- Food has no public customer order listing/webhook in the inspected OpenAPI.
- Progression contracts for GPS, PIN, proofs and test payments are not yet
  confirmed.

## Verification gates

- No event: zero reactions.
- Unknown account or repeated event: zero reactions.
- Restart/concurrency: one reaction maximum.
- Terminal state: no further reaction.
- All upstream calls are mocked in local tests.
