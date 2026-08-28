# Observability

If you can't answer "what happened to request X" from logs + traces alone, the instrumentation is incomplete.

## Logging

- Structured JSON only, via the app `Logger` (wraps `pino`). No `console.*` — ESLint errors on it.
- Every log line carries: `timestamp`, `level`, `service`, `env`, `requestId`, `tenantId` (when known), `traceId`/`spanId`. These are injected by the request-context middleware — never pass them manually.
- Message is a short, static, searchable string; variables go in fields:
  ```ts
  this.logger.info('order shipped', { orderId, carrier });      // good
  this.logger.info(`order ${orderId} shipped via ${carrier}`);  // bad — unsearchable, cardinality
  ```
- Levels:
  - `error` — something failed and needs a human (5xx, job failure after retries). Include the error object; pino serialises the stack + cause chain.
  - `warn` — degraded but handled (4xx, retry succeeded, fallback used).
  - `info` — business-meaningful state changes (order created / shipped / cancelled). One line per event, not per step.
  - `debug` — developer detail; off in prod.
- Log at the point of handling, not at every layer. A request that fails should produce **one** `error` line (from the exception filter), not one per layer.
- **No PII, ever** (see security.md). The logger redacts a denylist of keys as a backstop — don't rely on it.
- No logging inside tight loops or per-row in batch jobs. Log the batch summary.

## Request lifecycle

The `RequestLoggingInterceptor` emits one line per request at completion:

```json
{"msg":"request","method":"POST","route":"/v1/orders","status":201,"durationMs":42,"requestId":"...","tenantId":"..."}
```

`route` is the pattern (`/v1/orders/:id`), not the concrete path — keeps cardinality bounded.

## Metrics

Prometheus via `@willsoto/nestjs-prometheus`, scraped at `/metrics` (internal network only).

- RED per route, provided by the framework module: `http_requests_total{route,method,status}`, `http_request_duration_seconds{route,method}`.
- Business counters for meaningful events: `orders_created_total{tenant_tier}`, `shipments_failed_total{carrier,reason}`.
- Queue/job metrics: depth, processing duration, failures, oldest message age.
- Upstream calls: `upstream_request_duration_seconds{upstream,operation,status}`.
- Label rules: **low cardinality only**. Never `tenantId`, `orderId`, email, or any free-form string as a label. Tier/carrier/status/reason enums are fine.
- Histograms over summaries. Use the default buckets unless you have a reason.

## Tracing

OpenTelemetry SDK initialised in `src/tracing.ts` **before** Nest bootstraps (auto-instrumentation must patch `http`, `pg`, etc. first).

- HTTP, Prisma, and outbound `fetch` are auto-instrumented. Don't hand-create spans for these.
- Add manual spans for business operations that span multiple queries/calls: `tracer.startActiveSpan('orders.ship', ...)`. Name = `<module>.<verb>`.
- Propagate context to queues: put `traceparent` in message headers; consumers extract it.
- Span attributes follow the same PII rules as logs.

## Health

- `GET /health/live` — process is up. No dependencies checked. Used by the orchestrator's liveness probe.
- `GET /health/ready` — DB reachable, migrations applied, required upstreams responding (with short timeouts). Used for readiness / load-balancer.
- Both unauthenticated, both excluded from request logging and metrics.

## Alerts (what we page on)

Defined in `ops/alerts/*.yaml`, reviewed like code. Alert on symptoms, not causes:

- 5xx rate > 1% for 5 min per service
- p99 latency > SLO for 10 min
- Queue oldest-message age > threshold
- Readiness failing on > 50% of pods

Every alert links to a runbook in `docs/runbooks/`. An alert without a runbook is not merged.

## Checklist for a new feature

1. Business event logged at `info` with IDs (no PII).
2. Counter for the business event if anyone would ever graph it.
3. Manual span if the operation crosses > 2 I/O calls.
4. New upstream → timeout, breaker, `upstream_*` metrics, readiness check if it's required to serve traffic.
5. New queue consumer → depth/age metrics, trace propagation, dead-letter alert.
