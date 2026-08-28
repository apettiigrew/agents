# Database

PostgreSQL via Prisma. Schema is code; every change is a reviewed migration.

## Schema (`prisma/schema.prisma`)

- Table names: `snake_case` plural via `@@map("orders")`. Column names `snake_case` via `@map`. Prisma model/field names stay `PascalCase`/`camelCase`.
- Primary key: `id String @id @default(dbgenerated("uuid_generate_v7()"))`. No serial integers.
- Every table has `createdAt DateTime @default(now())` and `updatedAt DateTime @updatedAt`.
- Soft delete only when there's a business reason (audit, undo). Then `deletedAt DateTime?` and every query goes through a repository method that filters it — never ad-hoc `where: { deletedAt: null }` scattered around.
- Enums in Postgres (`enum OrderStatus`), not check constraints on strings.
- Foreign keys always, with explicit `onDelete` — default to `Restrict`; `Cascade` only for true owned children (order → order_items).
- Money: `Int` minor units + `String @db.Char(3)` currency. Never `Float`/`Decimal` for currency.
- Multi-tenant: every tenant-scoped table has `tenantId` with an index; every repository query includes it. No exceptions.

## Migrations

- `pnpm prisma migrate dev --name add_order_shipped_at`. Name = what it does, snake_case.
- One migration per logical change. Never edit an applied migration; add a new one.
- Review the generated SQL. Prisma is sometimes wrong about column renames (it drops and recreates). Hand-edit the SQL in the migration file when needed and say so in the commit.
- Backward-compatible by default — the previous app version must run against the new schema, because deploys are rolling:
  1. Add nullable column / new table → deploy code that writes both → backfill → make non-null → remove old code. Each step is its own MR.
  2. Never drop or rename a column in the same MR that stops using it.
- Data backfills are separate scripts in `prisma/scripts/`, batched (≤ 5k rows/txn), idempotent, and re-runnable. Not inside schema migrations.
- Indexes on large tables: `CREATE INDEX CONCURRENTLY` in a hand-edited migration.

## Queries (repositories only)

- All Prisma calls live in `*.repository.ts`. Services never import `PrismaService`.
- Repositories return domain entities, not Prisma types. Map in one `toEntity()` function per repository.
- `select` explicitly on hot paths; never `include` more than one level deep.
- No N+1: if you loop and query, stop and write one query with `in` or a join. `prisma.$queryRaw` with tagged template literals is allowed for anything Prisma can't express — never string concatenation.
- Pagination is cursor-based on `(createdAt, id)` or `(id)` — see api-design.md. `skip` is banned outside admin tooling.
- Transactions: `prisma.$transaction(async (tx) => ...)` in the **service**, passing `tx` into repository methods that accept an optional client. Keep transactions short; no external I/O (HTTP, queue) inside one.
- Every query on a tenant-scoped table filters by `tenantId`. Integration tests assert cross-tenant reads return nothing.

## Indexes

- Index every foreign key and every column that appears in a `where` or `orderBy` on a list endpoint.
- Composite index column order = equality columns first, then range/sort columns.
- Add the index in the same MR as the query that needs it. Justify in the MR description with the query shape.

## Connection & performance

- Pool size via `DATABASE_URL?connection_limit=`; sized to `(cores × 2) / replicas`, not "big".
- Query timeout 5s default (`statement_timeout`), overridable per repository method for known-slow reports.
- Log slow queries (> 200ms) at `warn` with the Prisma query hash — not the params (PII).

## Checklist for a schema change

1. Migration is backward-compatible with the currently deployed code.
2. Generated SQL reviewed; hand-edits documented.
3. New columns on tenant tables have `tenantId` handled in every repository method.
4. Indexes added for new query patterns.
5. Integration test covers the new repository method.
6. Backfill (if any) is a separate, idempotent script.
