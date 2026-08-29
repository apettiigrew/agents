# Trade Tracker — Product Requirements Document

**Status:** Draft for review
**Date:** 2026-08-29
**Owner:** Andrew Pettigrew

---

## 1. Summary

A personal, single-user web application for tracking manually-entered spot cryptocurrency
trades. It answers two questions at a glance — *which positions do I hold right now, and
what is each one worth?* — and keeps a complete, auditable history of every buy and sell
behind them.

Trades are entered by hand from the user's own record of on-chain and venue activity. The
application never connects to a wallet or an exchange.

---

## 2. Problem

The user trades spot crypto, predominantly BTC, ETH and SOL. The record of that activity
lives on the blockchain and in individual venue histories, with no consolidated view. Two
things are missing:

1. **No single answer to "what am I holding and how is it doing."** Valuing the portfolio
   means checking prices manually and doing arithmetic per holding.
2. **Averaging destroys the thing being tracked.** A spreadsheet that blends every BTC buy
   into one average cost produces a number that matches neither the trade that was made nor
   the decision to close it. Closing one of two separate BTC entries should show the PNL of
   *that* entry.

---

## 3. Goals

| ID | Goal |
|----|------|
| G1 | Record every buy and sell with enough fidelity to reconstruct the full trading history |
| G2 | Show all currently open positions with live valuation and unrealised PNL |
| G3 | Attribute PNL to the specific position that produced it, not to a blended per-coin average |
| G4 | Answer "how am I doing overall" in a single glance |
| G5 | Keep data durable and reachable from both phone and laptop |

### Non-goals for v1

Stated explicitly so they do not creep into scope:

- Leverage, shorts, perpetuals or any derivative instrument. **Spot only.**
- Multi-currency or FX. **USD only.**
- Tax reporting. UK HMRC rules require Section 104 pooling plus same-day and 30-day
  matching, which is a materially different calculation from the one specified here
  (§7). This application reports trading performance, not a tax position.
- Automatic import from exchanges, wallets or block explorers.
- Price alerts or notifications.
- Multiple users, sharing or collaboration.
- On-chain provenance fields (transaction hash, chain, wallet address). See §12.

---

## 4. Users and context

A single user — the owner — authenticated with Google OAuth restricted to one email
address. There is no second role, no sharing, and no invitation flow. The data model
carries a `userId` foreign key so that multi-user support would be an additive change
rather than a rewrite, but no v1 feature exposes it.

Usage is low-frequency and deliberate: a handful of entries per week, checked daily.
The application is read-heavy and write-light, and total row counts are expected in the
hundreds for years. Every design decision below assumes that scale.

---

## 5. Core concepts

### 5.1 The ledger

The ledger is the complete chronological history of buys and sells. It is the only thing
the user types. Everything else in the application — positions, valuations, PNL, charts —
is derived from it.

The ledger is a **view, not a table** (§6). Every ledger row traces back to a position, so
nothing is ever entered twice.

### 5.2 Positions

**Every buy opens its own position.** Buying BTC while a BTC position is already open
creates a second, independent BTC position. Positions are never merged and entry prices
are never blended.

A position is **open** while it has quantity remaining, and **closed** once its full
quantity has been sold. A sell targets one specific position and may take out part of it,
leaving the rest open.

### 5.3 Specific identification

The accounting method is **specific identification** — the user nominates which position a
sell closes. This is a standard method, alongside weighted-average cost and FIFO, and is
the one that matches how the user reasons about trades.

Worked example. Two BTC positions — position 1 is 1 BTC at $100, position 2 is 1 BTC at
$200 — and position 2 is closed at $300:

| Method | Realised | Unrealised | Lifetime total |
|--------|----------|------------|----------------|
| **Specific identification** (closes position 2) | $300 − $200 = **$100** | position 1: $300 − $100 = **$200** | **$300** |
| Weighted average cost (avg = $150) | $300 − $150 = **$150** | 1 BTC at $150 basis = **$150** | **$300** |

The lifetime total is identical under both methods. They differ only in how that total is
*split between realised and unrealised at a point in time*, never in the total itself.
Nothing is lost or double-counted; the user simply gets the attribution they want —
"position 2 closed, +$100" — instead of a blended figure matching neither trade.

This identity is a hard invariant of the system and is tested as such (§7.4).

---

## 6. Domain model

Three tables. The shape enforces the rules of §5 structurally rather than by convention.

### `Coin`

The tradeable assets being tracked.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `symbol` | text | `BTC`, `ETH`, `SOL`. Unique. |
| `name` | text | `Bitcoin` |
| `coingeckoId` | text | `bitcoin`. Unique. Used for all price lookups. |
| `displayPrecision` | int | Decimal places shown for a quantity of this coin |
| `createdAt` | timestamptz | |

Seeded with BTC, ETH and SOL. Further coins are added by the user via CoinGecko search.

### `Position`

A position **is** the buy. The opening trade's economics live on the position record
itself, which makes "every buy is exactly one position" impossible to violate — there is
no way to express a buy that is not a position, or a position with two buys.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `userId` | uuid | FK |
| `coinId` | uuid | FK → `Coin` |
| `openedAt` | timestamptz | When the buy occurred. Stored UTC, displayed local. |
| `quantity` | numeric(38,18) | Coin quantity bought. Must be > 0. |
| `entryPriceUsd` | numeric(38,8) | USD price per coin at entry |
| `feeUsd` | numeric(38,8) | Total fee on the buy. Defaults to 0. |
| `note` | text | Optional free text |
| `createdAt` / `updatedAt` | timestamptz | |

Indexed on `(userId, coinId)` and `(userId, openedAt)`.

### `PositionClose`

A sell against exactly one position.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `positionId` | uuid | FK → `Position`, indexed |
| `closedAt` | timestamptz | When the sell occurred |
| `quantity` | numeric(38,18) | Coin quantity sold. Must be > 0 and ≤ remaining. |
| `exitPriceUsd` | numeric(38,8) | USD price per coin at exit |
| `feeUsd` | numeric(38,8) | Total fee on the sell. Defaults to 0. |
| `note` | text | Optional free text |
| `createdAt` / `updatedAt` | timestamptz | |

### Derived values

Nothing is denormalised.

- `quantityRemaining` = `Position.quantity − Σ PositionClose.quantity`
- A position is **open** when `quantityRemaining > 0`, otherwise **closed**
- The **ledger** is the chronological union of positions (rendered as BUY rows) and
  closes (rendered as SELL rows)

At the expected scale these aggregate every time they are read. A stored
`quantityRemaining` column would be faster and would eventually drift out of sync with the
rows it summarises; that trade is not worth making for a few hundred rows. Revisit only if
row counts reach the tens of thousands.

### Numeric handling

All quantities, prices and monetary values are Postgres `numeric`, mapped to Prisma
`Decimal`. **Floating point is never used for a quantity or a monetary value at any layer,
including the browser.** Values cross the server/client boundary as strings and are
rendered through a shared decimal formatter. Rounding happens at display only: USD to 2
decimal places, coin quantities to the coin's `displayPrecision`.

---

## 7. PNL calculation

### 7.1 Open position

```
costBasis     = quantityRemaining × entryPriceUsd
                + feeUsd × (quantityRemaining ÷ quantity)
marketValue   = quantityRemaining × currentPriceUsd
unrealisedPnl = marketValue − costBasis
unrealisedPct = unrealisedPnl ÷ costBasis
```

The opening fee is allocated pro-rata across the position's whole quantity. The portion
belonging to quantity still held sits in the cost basis above; the portion belonging to
quantity already sold is charged against realised PNL (§7.2). The two shares always sum to
exactly the fee, so it is counted once and only once over the position's life.

This pro-rata split on *both* sides is load-bearing. Charging the opening fee only on
closes leaves the open portion's share accounted for nowhere, and the §7.4 invariant then
fails for any partially closed position — realised + unrealised falls short of lifetime PNL
by `feeUsd × (quantityRemaining ÷ quantity)`. On a freshly opened position the formula
reduces to `quantity × entryPrice + feeUsd`, which is exactly the total outlay previewed
before saving (F1).

### 7.2 Realised PNL on a close

The opening fee is allocated pro-rata to the quantity being closed:

```
realisedPnl = (exitPriceUsd − entryPriceUsd) × quantity
              − closeFeeUsd
              − openFeeUsd × (quantity ÷ positionQuantity)
```

The pro-rata term is what keeps partial closes honest — closing half a position takes half
its entry cost with it, and a fully closed position has absorbed exactly its whole opening
fee across all of its closes.

A position's realised PNL is the sum over its closes. Portfolio realised PNL is the sum
over all closes, all time.

### 7.3 Portfolio totals

```
totalCostBasis   = Σ costBasis      over open positions
totalMarketValue = Σ marketValue    over open positions
totalUnrealised  = totalMarketValue − totalCostBasis
totalRealised    = Σ realisedPnl    over all closes, all time
totalPct         = totalUnrealised ÷ totalCostBasis
```

### 7.4 Invariant

> For any coin, at any time: **realised PNL + unrealised PNL = lifetime PNL**.

Lifetime PNL is defined independently of §7.1 and §7.2, straight from the raw ledger, so
that the test cannot pass by repeating the implementation's own reasoning:

```
lifetimePnl = Σ (sell quantity × exit price)      -- proceeds
            − Σ sell fees
            + quantityRemaining × currentPrice    -- what is still held
            − Σ (buy quantity × entry price)      -- outlay
            − Σ buy fees
```

This is the identity demonstrated in §5.3, extended to include fees. It is implemented as
a property test over randomly generated buy/sell sequences — including partial closes,
multiple closes against one position, and non-zero fees on both sides — and is the single
highest-value test in the suite. Any arithmetic or fee-allocation error breaks it, and the
error corrected during the design of this document (an opening fee charged only on closes)
is precisely the kind it catches.

### 7.5 Edge cases

| Case | Behaviour |
|------|-----------|
| No current price ever retrieved for a coin | Value and PNL render as `—`, never `0`. A zero would read as a total loss. |
| Price retrieved but now stale | Last known price is shown with a visible staleness marker and its timestamp. |
| `costBasis` is zero (airdrop, zero-price entry) | Absolute PNL is shown; percentage renders as `—` rather than dividing by zero. |
| Close quantity exceeds remaining | Rejected server-side inside the write transaction (§9.3). |
| Position fully closed | Disappears from open positions, appears in closed history with its total realised PNL. |

---

## 8. Features

Each feature lists acceptance criteria written to be directly testable.

### F1 — Record a buy (open a position)

The user records a purchase, which opens a new position.

- Fields: coin, date/time, quantity, entry price (USD), fee (USD, optional, defaults to 0), note (optional)
- Quantity must be greater than zero; price and fee must be zero or greater
- The date/time may not be in the future
- Before saving, the form shows the computed cost basis (`quantity × price + fee`) so a
  mistyped decimal is visible before it is committed
- On save, a new position always appears in open positions — never merged into an existing one
- Recording a buy takes under 30 seconds

### F2 — Close a position (fully or partially)

The user records a sale against a specific open position.

- The user selects which position is being closed; positions are identified by coin, open date, size and entry price
- Fields: date/time, quantity, exit price (USD), fee (USD, optional), note (optional)
- Quantity defaults to the full remaining size, so a full close is one click
- Quantity may not exceed the remaining size, and may not be zero or negative
- The close date/time may not precede the position's `openedAt`, nor be in the future
- On a partial close, the position stays open with its size reduced and its entry price unchanged
- On a full close, the position leaves open positions and enters closed history
- The realised PNL for the close is shown immediately on save

### F3 — Edit and delete entries

Manual entry means mistakes, so correction is a first-class feature rather than an afterthought.

- Any position or close may be edited; all F1/F2 validation reapplies
- Editing a position's quantity is rejected if the new quantity is less than the total already closed against it
- A position with closes against it cannot be deleted until those closes are deleted first.
  A cascade would silently destroy realised PNL history; an explicit block will not.
- Deletion requires confirmation showing what will be removed

### F4 — Open positions view

The primary view, and the reason the application exists.

- Columns: **Coin · Size · Entry price · Current price · Position value · Unrealised PNL ($ and %) · Opened**
- One row per open position, so two BTC buys show as two rows
- PNL is colour-coded and also carries a sign, so it does not rely on colour alone (§10)
- Sortable by any column; default sort is position value descending
- An empty state explains how to record the first buy
- Every value on screen reflects a price no more than 60 seconds old, or is marked stale

### F5 — Per-coin rollup

A toggle on the open positions table.

- Collapsed: one row per coin showing total quantity, weighted-average entry price, total
  value and aggregate unrealised PNL
- Expanding a coin reveals its individual positions, unchanged from F4
- The weighted average is display-only and never affects a stored value or a PNL calculation

### F6 — Ledger view

The full transaction history.

- Every buy and sell in one chronological list, newest first
- Columns: **Date · Coin · Side · Quantity · Price · Value · Fee · Realised PNL · Note**
- Realised PNL is populated on sell rows only; buy rows show `—`
- Filterable by coin and by date range; free-text search across notes
- Each row links to the position it belongs to

### F7 — Closed positions and realised PNL

- Lists positions that are fully closed, plus positions with partial closes against them
- Shows per position: coin, open date, close date(s), quantity, entry price, exit price(s), total realised PNL
- Shows a running realised total for the period in view
- Without this view, closing a position would make it vanish from the application entirely

### F8 — Portfolio summary bar

Persistent across the top of the dashboard.

- Total cost basis, total current value, total unrealised PNL, total realised PNL, overall percentage change
- Updates live with the price feed
- Degrades gracefully when prices are unavailable: shows cost basis, marks value and PNL as stale or unavailable

### F9 — Live price feed

- Current USD prices for every held coin, from CoinGecko
- Refreshes at most every 60 seconds
- Displays a relative freshness indicator ("updated 12s ago")
- On upstream failure the last known prices remain visible, marked stale, with an
  unobtrusive banner; the application stays fully usable
- A manual refresh control is available

### F10 — Charts

- **Allocation** — current market value by coin. Derived entirely from data already on the dashboard.
- **Value over time** — portfolio USD value on a daily series, over a selectable window
  (30d / 90d / 1y). Reconstructed as `Σ (quantity held that day × that day's close)` from
  the ledger and CoinGecko daily historical closes (§9.2).
- Both charts follow the project's data-visualisation conventions and remain legible in
  light and dark themes

### F11 — Coin management

- Search CoinGecko by name or symbol and add a coin to the tracked list
- Adding stores symbol, name, `coingeckoId` and display precision
- A coin with positions against it cannot be removed
- BTC, ETH and SOL are seeded

### F12 — Authentication

- Google OAuth via Auth.js v5
- The `signIn` callback rejects any email address other than the owner's, so an exposed URL
  is still not an open door
- Every Server Action and route handler asserts a valid session before touching data
- Unauthenticated requests to any application route redirect to sign-in

---

## 9. Architecture

### 9.1 Stack

A single Next.js 15 full-stack application, following the conventions in
`templates/frontend-app`:

| Concern | Choice |
|---------|--------|
| Framework | Next.js 15 App Router, React 19, TypeScript 5 |
| Rendering | Server Components by default; `'use client'` only at leaves that need it |
| Mutations | Server Actions, validated with Zod **on the server** |
| Database | Hosted Postgres (Neon or Prisma Postgres) via Prisma, plain `DATABASE_URL` |
| Server state | TanStack Query, for the live price feed only |
| Styling | Tailwind CSS with `cva` variants |
| Auth | Auth.js v5, Google provider, single-email allowlist |
| Testing | Vitest + Testing Library, Playwright for E2E |
| Hosting | Vercel |

Positions, ledger and closed history are fetched on the server and rendered as Server
Components. TanStack Query is deliberately confined to prices — the one piece of data that
must change after load without a navigation.

### 9.2 Price provider seam

CoinGecko is reached only through a `PriceProvider` interface exposing two operations:

```
getCurrentPrices(coingeckoIds: string[]): Promise<Map<string, Decimal>>
getDailyCloses(coingeckoId: string, days: number): Promise<DailyClose[]>
```

CoinGecko is the only implementation. The seam exists because the price feed is the one
dependency genuinely likely to change — free-tier terms and rate limits move — and
swapping it must not touch a component.

**Current prices.** A cached server route requests `/simple/price` for the union of held
coins, revalidating every 60 seconds. That is one upstream call per minute regardless of
how many tabs are open, comfortably inside the free tier. Clients poll the internal route,
never CoinGecko directly, so no key is ever exposed and CORS is a non-issue.

**Historical closes.** Value-over-time normally forces a nightly snapshot table. It does
not have to here: CoinGecko's `market_chart` endpoint serves up to 365 days of daily
closes, so any past day's portfolio value is reconstructable from the ledger. This is
computed server-side and cached for an hour. The benefit is that history is correct
immediately, with no cold-start gap and no backfill problem — a snapshot table would only
know about days since the application was installed.

*Fallback:* if the historical endpoint proves rate-limiting or its window insufficient,
switch to daily snapshots going forward, accepting the gap.

### 9.3 Write integrity

Recording a close reads the position's remaining quantity and inserts the close **inside a
single database transaction**, re-checking the remaining quantity at write time. Validating
before the transaction and inserting after would permit a double-submit to oversell a
position.

### 9.4 Routes

| Route | Purpose |
|-------|---------|
| `/` | Dashboard — summary bar (F8), charts (F10), open positions (F4, F5) |
| `/ledger` | Full transaction history (F6) |
| `/positions/closed` | Closed and partially closed history (F7) |
| `/coins` | Tracked coin management (F11) |
| `/login` | Google sign-in (F12) |
| `/api/prices` | Cached current-price route consumed by the client |

Recording a buy, closing a position and editing an entry are modal flows over the view
that launched them, so the user never loses their place in the table.

---

## 10. Non-functional requirements

- **Accuracy.** Decimal arithmetic end to end; no floating point for any quantity or
  monetary value. The §7.4 invariant holds for every sequence of operations.
- **Freshness.** Displayed prices are under 60 seconds old, or visibly marked as not.
- **Resilience.** CoinGecko being unavailable degrades the application to cost-basis-only.
  It never blocks recording a trade, and it never shows a wrong number as if it were right.
- **Accessibility.** Semantic tables with proper headers, labelled controls, keyboard
  operable, visible focus. PNL direction is conveyed by sign and arrow as well as colour.
  `eslint-plugin-jsx-a11y` errors block commits.
- **Security.** No secrets reach the browser; only `NEXT_PUBLIC_*` is client-visible.
  Every data access is scoped by session `userId`. Server-side Zod validation on every
  mutation — client-side validation is UX, not security.
- **Testing.** TDD throughout. Pure unit tests over the PNL module including the invariant
  property test; component tests asserting on what the user sees; one Playwright test per
  user-facing flow, including the full buy → partial close → full close lifecycle.
- **Quality gate.** `pnpm typecheck && pnpm lint && pnpm test` green before every commit;
  `pnpm build` succeeds with no server/client boundary warnings.
- **Timezones.** Timestamps stored UTC, displayed in the browser's local zone.

---

## 11. Success criteria

The v1 is done when all of the following hold:

1. A buy can be recorded in under 30 seconds from opening the application.
2. The dashboard answers "what am I holding and am I up" without scrolling or interaction.
3. Closing a position produces a realised PNL that matches a hand calculation exactly,
   including fees, for both full and partial closes.
4. The §7.4 invariant passes under property testing.
5. Every ledger row traces to a position, and every position's history reconstructs from
   ledger rows alone.
6. CoinGecko being down leaves the application usable for recording and reviewing trades.
7. The application is usable on a phone.

---

## 12. Deferred, with the path to adding it

Recorded so future work does not have to rediscover the reasoning.

| Deferred | Path if wanted later |
|----------|---------------------|
| On-chain provenance (tx hash, chain, wallet) | Two nullable columns on `Position` and `PositionClose`, plus a chain→explorer URL map. Purely additive. |
| Weighted-average / FIFO view for tax | A second calculation module over the same ledger. The ledger already holds everything required; no schema change. Note that HMRC's rules are S104 pooling with same-day and 30-day matching, not plain FIFO. |
| Multi-currency | Requires an FX rate stored per transaction for historical accuracy — retrofitting it onto existing rows means assuming rates. Decide before the ledger grows large. |
| Leverage / shorts | Direction, leverage and margin on `Position`, and a signed PNL formula. The §7 formulas hold for shorts with a sign flip. |
| Exchange / wallet import | An importer that writes positions and closes through the same validation path as manual entry. |
| Multi-user | `userId` is already on every row and every query is already scoped by it. |

---

## 13. Risks

| Risk | Mitigation |
|------|-----------|
| CoinGecko free-tier limits or terms change | Server-side caching keeps usage to one call per minute; the `PriceProvider` seam (§9.2) makes swapping providers a single-file change |
| Manual entry errors corrupt history | Full edit/delete (F3), strict validation, and a computed cost-basis preview before every save |
| Historical price endpoint insufficient for charts | Documented fallback to forward-only daily snapshots (§9.2) |
| Fee handling is subtly wrong | The pro-rata allocation is specified explicitly (§7.2) and covered by the invariant test (§7.4) |
| Charts expand scope | Allocation is nearly free; value-over-time is the only genuinely additive work and can ship in a second iteration without affecting any other feature |

---

## 14. Decisions made during design

For the record, with reasoning, so they are not relitigated:

| Decision | Reasoning |
|----------|-----------|
| Specific identification over average cost | Matches how the user reasons about trades; lifetime PNL is identical either way (§5.3) |
| Every buy is its own position | Makes the open-positions view literally the list of trades the user opened; no reconciliation against memory |
| Positions derived from the ledger, never entered twice | Single source of truth; `Position` *is* the buy, so the rule cannot be violated |
| "Market" column dropped | The coin *is* the market for spot trading; a separate venue column would be empty ceremony |
| Optional fee field retained despite minimal-provenance choice | Fees feed directly into the PNL figure the application exists to show; without them every number is gross and a small position can read green while being down after costs |
| No denormalised `quantityRemaining` | At a few hundred rows the aggregate is free, and a stored column would eventually drift |
| Full-stack Next.js over a separate NestJS API | No second client exists; an API contract for a single-user app is cost without benefit |

---

## 15. Delivery order

Twelve features is more than one implementation plan should carry at once. They split into
three milestones, each independently useful — the application is worth using from the end
of the first.

**Milestone 1 — Usable.** Auth (F12), coin seed and management (F11), record a buy (F1),
close a position (F2), open positions view (F4), live prices (F9). At the end of this the
application does the thing it exists for: positions in, valuation out.

**Milestone 2 — Complete history.** Ledger view (F6), closed positions and realised PNL
(F7), edit and delete (F3), portfolio summary bar (F8). This closes the loop so that
nothing entered can be lost or left uncorrectable.

**Milestone 3 — Analysis.** Per-coin rollup (F5), allocation chart (F10a), value-over-time
chart (F10b). Entirely additive; the historical-price integration lives here alone, so
deferring or dropping F10b affects nothing else.

The PNL module (§7) and its invariant test are built first, before any UI, since every
milestone depends on it being right.
