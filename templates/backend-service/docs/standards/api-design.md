# API Design

REST over JSON. Versioned. Boring on purpose — clients should be able to guess the next endpoint.

## URLs

- Prefix every route with `/v1/`. Version the whole API, not individual resources.
- Plural nouns, kebab-case: `/v1/orders`, `/v1/shipping-labels`.
- Nest at most one level: `/v1/orders/{orderId}/items`. Deeper → promote to a top-level resource with a filter.
- No verbs in paths. Actions that don't map to CRUD are sub-resources expressed as POST: `POST /v1/orders/{id}/cancel`.
- IDs are opaque strings (UUID v7). Never expose auto-increment integers.

## Methods & status codes

| Operation | Method | Success |
|-----------|--------|---------|
| Create | `POST /v1/orders` | `201` + body + `Location` header |
| Read one | `GET /v1/orders/{id}` | `200` |
| List | `GET /v1/orders` | `200` |
| Full replace | `PUT` | `200` |
| Partial update | `PATCH` (JSON merge patch) | `200` |
| Delete | `DELETE` | `204`, no body |
| Action | `POST .../{id}/cancel` | `200` with resulting resource |

`PUT`/`DELETE`/`PATCH` must be idempotent. `POST` create endpoints accept an optional `Idempotency-Key` header; duplicate keys within 24h return the original response.

## Request bodies

- One DTO class per request shape in `dto/`. Decorate every field with class-validator. Unknown fields are rejected (`forbidNonWhitelisted`).
- `camelCase` JSON keys.
- Never accept IDs of the authenticated tenant/user in the body — derive them from the auth context.
- Dates in ISO 8601 with timezone. Money as `{ amount: 1299, currency: "USD" }`.

## Response bodies

- Always a response DTO. Never return a Prisma model or entity directly — it leaks columns.
- Single resource: the object at top level. No `{ data: ... }` wrapper for single items.
- Collections:

```json
{
  "items": [ ... ],
  "nextCursor": "eyJpZCI6Ii4uLiJ9",
  "hasMore": true
}
```

- Cursor pagination only. Query params: `limit` (default 25, max 100), `cursor`. No offset pagination on anything that can grow.
- Filtering via query params named after the field: `?status=shipped&createdAfter=2026-01-01T00:00:00Z`.
- Sorting: `?sort=-createdAt,id`. Leading `-` = descending. Always include a tiebreaker.

## Errors

RFC 7807 `application/problem+json`, produced only by the global exception filter (see error-handling.md):

```json
{
  "type": "https://errors.example.com/order-not-found",
  "title": "Order not found",
  "status": 404,
  "detail": "No order with id 018f...",
  "instance": "/v1/orders/018f...",
  "requestId": "req_7Kx...",
  "errors": [ { "field": "items[0].sku", "message": "must not be empty" } ]
}
```

`errors[]` is present only for `400` validation failures.

## Headers

- Read `X-Request-Id` if present, else generate; always echo it back.
- Auth: `Authorization: Bearer <jwt>`. Never API keys in query strings.

## Documentation

- Every controller method has `@ApiOperation`, `@ApiResponse` for each status it can return, and DTOs have `@ApiProperty`. Swagger is generated, not hand-written, and served at `/docs` in non-prod.
- Breaking change = new version. Additive changes (new optional field, new endpoint) are fine within a version.

## Checklist for a new endpoint

1. DTOs for request and response, fully decorated.
2. Controller method: ≤3 lines, correct status code, Swagger decorators.
3. Service method with unit tests.
4. E2E test covering success, validation failure, not-found, and unauthenticated.
5. Update the OpenAPI snapshot test.
