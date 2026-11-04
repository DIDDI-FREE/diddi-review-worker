# Capability Map: diddi-review-runner

| Module id | Responsibility | Depends on |
|---|---|---|
| identity | Obtain, validate and isolate normal DiddiFreeID JWTs for review actors | — |
| adapters | Typed clients for DiddiFreeID, DiddiPay, DiddiSend, DiddiGo and DiddiFood | identity |
| scenarios | Declare review journeys, actor roles and business-step contracts | adapters |
| orchestration | Execute journeys with idempotency, retries, compensation policy and state transitions | scenarios, adapters, persistence |
| persistence | Store run definitions, step states, tokens metadata and audit events without business DB access | — |
| api | FastAPI endpoints for creating, inspecting, retrying and cancelling runs | orchestration, persistence |
| observability | Structured logs, metrics, traces, correlation IDs and redaction | api, orchestration |

Build order: identity → adapters → persistence → scenarios → orchestration → api → observability

