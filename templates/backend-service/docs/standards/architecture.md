# Architecture

Layered, module-per-bounded-context. Dependencies point inward: controller → service → repository → Prisma. Nothing points outward.

## Module layout

```
src/modules/orders/
├── orders.module.ts          # wires providers; imports only what it needs
├── orders.controller.ts      # HTTP only: routing, DTO binding, status codes
├── orders.service.ts         # business rules; the only place domain logic lives
├── orders.repository.ts      # Prisma queries; returns domain types, never Prisma types
├── dto/
│   ├── create-order.dto.ts   # request shape + class-validator decorators
│   └── order.response.dto.ts # response shape; never expose Prisma models directly
├── entities/order.entity.ts  # domain type (plain interface or class), DB-agnostic
└── orders.service.spec.ts
```

One module = one bounded context. If two modules need each other's data, one exports a service and the other imports the module — never reach into another module's repository.

## Layer responsibilities

| Layer | Does | Never does |
|-------|------|------------|
| Controller | Route, bind DTOs, set status codes, call one service method | Business logic, DB access, try/catch for domain errors |
| Service | Domain rules, orchestration, transactions, emits domain events | HTTP concerns (`@Res`, status codes), SQL |
| Repository | Data access, mapping Prisma ↔ entity | Business decisions, throwing HTTP exceptions |

A controller method body should be one to three lines. If it's longer, logic has leaked.

```ts
// good
@Post()
@HttpCode(201)
create(@Body() dto: CreateOrderDto): Promise<OrderResponseDto> {
  return this.orders.create(dto);
}
```

## Dependency injection

- Constructor injection only. `private readonly` fields.
- Depend on abstractions for anything external (payment gateway, mail, clock): define an interface + injection token, provide the concrete class in the module. This is what makes services unit-testable without mocking Prisma.
- No `@Global()` modules except `ConfigModule`, `LoggerModule`, `PrismaModule`.
- No circular imports. If you need `forwardRef`, the module boundary is wrong — fix the boundary.

## Cross-cutting concerns

Use the framework, not ad-hoc code in every handler:

- Auth → guards (`@UseGuards(JwtAuthGuard)` at controller level, `@Public()` to opt out)
- Validation → global `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true })`
- Response shaping / timing → interceptors
- Error → response mapping → one global exception filter (see error-handling.md)

## Configuration

- All config via `ConfigService` backed by a validated schema (`config/schema.ts`, zod). The app must fail at boot on a missing/invalid variable — never at first use.
- No `process.env` outside `config/`.
- Feature flags are config, not code branches on environment name.

## What to do when the pattern doesn't fit

Stop, and report it as a concern with a proposed alternative. Don't invent a fourth layer or a new folder convention inside a task. Architectural changes are their own task with their own review.
