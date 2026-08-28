# Error Handling

Errors are data. Throw typed domain errors from services, map them to HTTP in exactly one place, and never lose the cause.

## The hierarchy

`src/common/errors/app.exception.ts`:

```ts
export abstract class AppException extends Error {
  abstract readonly code: string;        // stable, machine-readable: "ORDER_NOT_FOUND"
  abstract readonly httpStatus: number;
  constructor(message: string, readonly context?: Record<string, unknown>, options?: { cause?: unknown }) {
    super(message, options);
    this.name = new.target.name;
  }
}

export class NotFoundError extends AppException { httpStatus = 404; code = 'NOT_FOUND'; }
export class ValidationError extends AppException { httpStatus = 400; code = 'VALIDATION_FAILED'; }
export class ConflictError extends AppException { httpStatus = 409; code = 'CONFLICT'; }
export class ForbiddenError extends AppException { httpStatus = 403; code = 'FORBIDDEN'; }
export class UpstreamError extends AppException { httpStatus = 502; code = 'UPSTREAM_FAILED'; }
```

Modules subclass these with specific codes when a client would branch on them:

```ts
export class OrderNotFoundError extends NotFoundError {
  code = 'ORDER_NOT_FOUND';
  constructor(orderId: string) { super(`Order ${orderId} not found`, { orderId }); }
}
```

## Rules

1. **Services throw `AppException` subclasses. Never `HttpException`, never raw `Error`.** Services don't know about HTTP.
2. **Repositories don't throw domain errors.** They return `null` / empty and let the service decide what that means.
3. **Controllers don't catch.** The global `AppExceptionFilter` maps every `AppException` to an RFC 7807 body (see api-design.md). Anything else becomes a `500` with a generic message and a full log entry.
4. **Wrap, don't swallow.** When catching an external error to rethrow, pass it as `cause`:
   ```ts
   try { await this.gateway.charge(...) }
   catch (err) { throw new UpstreamError('Payment gateway failed', { orderId }, { cause: err }); }
   ```
5. **Never `catch (e) {}`** or `catch` that only logs and continues. If it's genuinely ignorable, comment why and name the specific error class you're ignoring.
6. **`context` is for structured logging, never for the response body** unless the field is explicitly safe. It must never contain PII (see security.md).
7. **Validation errors from `ValidationPipe`** are converted by the filter into `ValidationError` with `errors[]` — don't reformat them in controllers.
8. **Don't use exceptions for control flow** inside a service. `findById` returning `null` is fine; `try { getById } catch (NotFound) { create }` is not — use `findById` then branch.

## What gets logged

The filter logs:
- `4xx`: `warn` level, code + context + requestId. No stack trace.
- `5xx`: `error` level, full stack including `cause` chain, requestId.

Services should *not* also log the error they're throwing — that produces duplicates. Log at the point of *handling*, not the point of throwing.

## Async & background work

- Every `async` call is `await`ed or explicitly `void`-ed with a comment. `@typescript-eslint/no-floating-promises` is an error.
- Queue consumers / cron jobs wrap the body in a try/catch that logs and either acks (permanent failure) or nacks (transient). Classify with `err instanceof UpstreamError` etc. — don't string-match messages.
- Unhandled rejections crash the process (`process.on('unhandledRejection')` rethrows). A crash-loop is louder and safer than silent corruption.

## Testing errors

- Unit tests assert on the error *class*, not the message: `await expect(svc.ship(id)).rejects.toBeInstanceOf(OrderNotFoundError)`.
- E2E tests assert the full problem+json shape including `code`.
