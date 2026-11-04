# Implementation plan

1. Bootstrap Python/FastAPI, settings and health endpoints.
2. Add actor contracts, JWT review validation and redaction.
3. Add typed HTTP adapters with idempotency and domain error mapping.
4. Add scenarios and run state machine with an in-memory repository for the first vertical slice.
5. Add API run lifecycle, tests, Docker and documentation.

The first implementation is intentionally contract-driven: endpoint paths and payloads are
configuration, while the runner owns orchestration state and never accesses business DBs.

