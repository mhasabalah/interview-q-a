---
title: Architecture Defense
aliases: [Architecture Defense, Defending Your Architecture, Vertical Slice vs Clean, MediatR Defense]
tags: [architecture, cqrs, mediatr, ddd, vertical-slice, interview]
order: 17
---

# Defending Your Own Architecture — Interview Q&A

> [!info]+ Related Notes
> [[07-Domain-Driven-Design|Domain-Driven Design]] · [[08-Clean-Architecture|Clean Architecture]] · [[09-Onion-Architecture|Onion Architecture]] · [[11-Module-Communication|Module Communication]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]] · [[03-Design-Patterns|Design Patterns]] · [[19-Modular-Monolith|Modular Monolith]] · [[20-Choosing-An-Architecture|Choosing an Architecture]]

> [!tip] The other half of this round
> This note defends the choices *inside* one deployable. When they ask **"why this topology, and when would you split it?"** — the comparison of every style, the default a senior picks, and the migration paths are in [[20-Choosing-An-Architecture|Choosing an Architecture]].

> [!danger]+ Read this first — the rule of this round
> They will read **"vertical slice + MediatR + EF Core"** on your CV and probe whether you *chose* it or *copied* it. The difference between mid and senior in this round is one thing:
>
> **A mid-level engineer describes. A senior states an opinion, names what it cost, and says when they'd choose differently.**
>
> Every answer below has the same shape — practise it until it's automatic:
> 1. **What it buys me** (one concrete benefit, from my system)
> 2. **What it cost me** (a real drawback — naming this is what buys credibility)
> 3. **When I'd choose the other thing** (proves it was a decision, not a habit)
>
> "I don't have an opinion on that" is the worst possible answer. A *wrong but reasoned* opinion beats a *correct but memorised* description.

---

## Vertical Slice vs Clean/Onion

**Q: You used vertical slice architecture. Why not Clean Architecture?**

**A (the opinion):** "Because my unit of change is a **feature**, not a layer. In a layered app, adding one field means touching a controller, a service interface, an implementation, a repository interface, a repository, and a DTO mapper — six files across four projects, none of which are near each other. In a vertical slice, that change is one folder. I optimised for **change locality**, because that's what I actually do every day."

**What VSA buys you:**
- **Change locality** — a feature is one folder; you delete a feature by deleting a folder.
- **No artificial layer ceremony** — no `IUserService` with one implementation existing purely to satisfy a diagram.
- **Per-slice freedom** — the "list orders" slice can be raw Dapper with a projection, while "place order" goes through the full rich domain model. Layered architecture forces both through the same pipes.
- **Coupling becomes visible** — shared code has to be *deliberately* promoted to a shared place, instead of quietly accumulating in a god-service.

**Where it hurts (say this before they say it):**
- **Duplication across slices** — similar mapping/validation code repeated. Some is healthy (decoupling); some is real debt, and telling them apart requires judgement.
- **No obvious home for shared domain logic** — the pressure is to copy-paste or to create a `Common` dumping ground.
- **It rots into transaction scripts without discipline** — if every handler is "load entity, mutate properties, save", you have procedural code with a folder structure. The domain model has to stay rich, or VSA gives you nothing over a CRUD controller.
- **Onboarding** — juniors can't pattern-match "where does this go?" as easily as with layers.
- **Cross-cutting consistency** — with no shared pipeline, twelve slices can end up with twelve different transaction/validation behaviours.

```text
Vertical slice                         Clean / Onion
────────────────────────────           ────────────────────────────
Features/                              src/
  Orders/                                Domain/          <- entities, VOs
    PlaceOrder/                          Application/     <- use cases, interfaces
      PlaceOrderCommand.cs               Infrastructure/  <- EF, HTTP, files
      PlaceOrderHandler.cs               Api/             <- controllers
      PlaceOrderValidator.cs
      PlaceOrderEndpoint.cs            change one feature -> 4 projects
      PlaceOrderResponse.cs            change one layer  -> 1 project
    CancelOrder/ ...
  Domain/          <- still rich, still shared
```

**Q: When would you pick layered/Clean instead?**

A: Name concrete conditions:
- **A large team with a mandated structure** — consistency beats locality once "where does this go?" is asked by 30 people.
- **A genuinely rich domain reused across many use cases** (insurance rating, payroll, pricing) — the domain layer is the product; slices would fragment it.
- **A library or SDK** — consumers need a stable public surface, not features.
- **A team that hasn't got the discipline** — VSA without review discipline degrades faster than layers do.

> [!tip] The synthesis answer (strongest version)
> "They're not opposites. I use **vertical slices for the application layer** and keep a **shared, dependency-free domain project** underneath. Slices own orchestration, validation, and reads; the domain owns invariants. The Dependency Rule still holds — my slices depend on the domain, never the reverse — I just stopped creating a layer per noun."

---

## MediatR

**Q: What does MediatR actually buy you? Couldn't you inject the handler directly?**

**A (the honest opinion):** "Strictly, yes — I could inject `IPlaceOrderHandler` directly and it would work. **What I'm actually buying is the pipeline.** One registration gives every request in the system validation, logging with correlation IDs, transaction scope, and performance timing, without decorating 80 handlers by hand. If I couldn't name what my behaviours do, I couldn't justify the dependency — and that's the real test."

**The behaviours that earn it (be able to name yours):**

```csharp
// 1. Validation — fail fast before the handler, uniform 400 response
public class ValidationBehavior<TReq, TRes> : IPipelineBehavior<TReq, TRes> where TReq : notnull
{
    private readonly IEnumerable<IValidator<TReq>> _validators;

    public async Task<TRes> Handle(TReq request, RequestHandlerDelegate<TRes> next, CancellationToken ct)
    {
        var failures = (await Task.WhenAll(_validators.Select(v => v.ValidateAsync(request, ct))))
                       .SelectMany(r => r.Errors).Where(f => f is not null).ToList();
        if (failures.Count != 0) throw new ValidationException(failures);
        return await next();
    }
}

// 2. Transaction / Unit of Work — commands are atomic by construction, handlers never call SaveChanges
public class TransactionBehavior<TReq, TRes> : IPipelineBehavior<TReq, TRes>
{
    public async Task<TRes> Handle(TReq request, RequestHandlerDelegate<TRes> next, CancellationToken ct)
    {
        if (request is not ICommand) return await next();          // queries skip this
        await using var tx = await _db.Database.BeginTransactionAsync(ct);
        var response = await next();
        await _db.SaveChangesAsync(ct);   // domain events dispatched here (see below)
        await tx.CommitAsync(ct);
        return response;
    }
}

// 3. Logging / correlation, 4. Caching for IQuery, 5. Idempotency check, 6. Authorization
```

**The honest criticism (say it yourself — it's a credibility multiplier):**
- **Indirection.** `_mediator.Send(cmd)` has no compile-time link to the handler. "Go to definition" lands on MediatR's interface, not your code. On a big codebase this genuinely slows people down.
- **Hard-to-trace call graphs.** Reflection-based dispatch means no static call tree, and stack traces run through pipeline frames.
- **Cargo cult.** Most teams use it as an *in-process bus* for no reason — one publisher, one handler, no pipeline. That's a `Send` where a method call would do, and it's indefensible.
- **It's not CQRS.** MediatR is a mediator; separating `IRequest`/`IRequestHandler` isn't architecture, it's naming.
- **Dependency risk.** MediatR and AutoMapper moved to a **commercial licensing model** (announced 2025 by their maintainer). Knowing this — and that alternatives exist — shows you track your dependencies.

**Alternatives to name if pushed:** direct handler injection with **decorators** (Scrutor) for cross-cutting concerns · **Minimal API endpoint filters** (the pipeline, built into the framework) · **FastEndpoints** · a hand-rolled 60-line dispatcher.

> [!warning] The killer follow-up
> *"So if I deleted MediatR from your project tomorrow, what breaks?"*
> Bad answer: "everything's coupled to it."
> Good answer: "My **behaviours** — I'd have to reimplement validation, transactions, and logging as decorators or endpoint filters. Handlers themselves are plain classes with a `Handle` method; they don't care. That's deliberate: the coupling is at the edge, not in the business logic."

---

## Repository over EF Core

**Q: `DbContext` is already a Unit of Work and `DbSet<T>` is already a repository. So why wrap it?**

**A: Acknowledge the premise first — it's true.** `DbContext` = Unit of Work (change tracker + `SaveChanges`), `DbSet<T>` = generic repository. So a `GenericRepository<T>` with `Add/Update/Delete/GetById/GetAll` **adds nothing but a layer of forwarding calls** — that one really is an anti-pattern, and you should say so.

**Then pick a side and price it.**

**The case FOR a repository (per aggregate, not generic):**
- **It expresses the domain, not the storage:** `IOrderRepository.GetPendingOlderThan(TimeSpan)` states intent; `_db.Orders.Where(...).Include(...).AsSplitQuery()` states mechanics — repeated in twelve places.
- **It stops `IQueryable` leaking into the application layer.** Once handlers compose `IQueryable`, your persistence details (lazy loading, translatable expressions, tracking behaviour) are everyone's problem, and a `.Where()` written in a controller can silently produce a table scan.
- **DDD fit:** the repository is the *aggregate's* persistence boundary — one repository per aggregate root, loading the whole consistency boundary and saving it as a unit.
- **Swappability is a weak argument** — say so. Nobody swaps EF Core for MongoDB. But moving *one hot query* to Dapper behind an existing interface is a real, common event.

**The case AGAINST:**
- **It's a leaky abstraction.** `Include`, `AsNoTracking`, projections, split queries, transactions, and `IQueryable` composition all eventually leak through, and you end up with `GetOrderWithLinesAndCustomerAndPayments()`.
- **You lose EF features** or re-expose them one by one until the interface *is* `DbSet<T>`.
- **The testability argument is much weaker now.** It used to be "I need to mock the data layer". With **Testcontainers**, an integration test against a real PostgreSQL in Docker runs in seconds and tests the thing that actually breaks — the SQL. Mocking `IQueryable` proves your LINQ compiles, not that it runs.

```csharp
// The defensible middle ground: aggregate repositories for writes, direct EF/Dapper for reads
public interface IOrderRepository                    // WRITE side: domain-shaped, no IQueryable
{
    Task<Order?> GetAsync(OrderId id, CancellationToken ct);   // loads the whole aggregate
    void Add(Order order);
    // no Update(): the change tracker handles it. No SaveChanges(): the UoW/behaviour owns it.
}

// READ side: no repository at all — a query handler projecting straight to a DTO
var rows = await _db.Orders.AsNoTracking()
    .Where(o => o.CustomerId == id)
    .Select(o => new OrderListItem(o.Id, o.Total, o.Status))
    .ToListAsync(ct);
```

**The sentence to have ready:** "Repositories on the **write** side because that's where invariants and aggregate boundaries live; **no** repository on the read side because a projection is already the simplest thing that works. The cost is asymmetry — two ways to touch the database — and I accept it because writes and reads have genuinely different jobs."

---

## CQRS — where on the spectrum, and why you stopped there

**Q: You say you use CQRS. What does that mean in your system?**

**A: Immediately locate yourself on the spectrum** — most candidates say "CQRS" meaning level 1 and get caught when the interviewer assumes level 3.

| Level | What's separated | Consistency | Cost | Typical trigger |
|---|---|---|---|---|
| **1. Handler-level** | Commands and queries are different types/handlers, one model, one DB | strong | ~zero | default; readability + per-side pipelines |
| **2. Separate read model** | Same DB, reads bypass the domain (SQL views, Dapper, projections/denormalised tables) | strong (same tx) or near-real-time | moderate | domain model is a poor shape for reads |
| **3. Separate read store** | Different database (Elasticsearch, Redis, replica) updated by events/projections | **eventual** | high — sync, lag, rebuild, monitoring | read scale or query shapes SQL can't serve |
| **4. + Event sourcing** | State stored as an event log; read models rebuilt from it | eventual | very high — versioning, replay, snapshots | audit/temporal requirements are a *hard* need |

**Q: Is CQRS the same as event sourcing?**
A: **No — and this is a deliberate trap.** CQRS is separating the read path from the write path. Event sourcing is storing state as a sequence of events. Event sourcing almost forces CQRS (you can't query an event log), but CQRS needs no events at all. Most CQRS systems are plain CRUD tables with two code paths.

**"Where did you stop, and why?"** — the answer that lands:

> "**Level 2.** Commands go through the domain model and enforce invariants; queries are handlers projecting directly to DTOs with `AsNoTracking`, and two heavy list screens read denormalised views. I deliberately stopped before a separate read store, because that buys read-scale I don't need and charges me **eventual consistency in the UI** — a user who edits a record and doesn't see the change in the list will file a bug, and the fix costs real engineering. When read traffic outgrows the primary, the next step is a read replica with a read-your-own-writes rule, not a projection pipeline."

That answer proves you understand CQRS is a **cost curve**, not a badge.

---

## DDD tactical patterns

**Q: Entity vs value object?**

A: **Identity.** An entity has an ID and continuity — two `Order`s with identical fields are different orders. A value object is defined entirely by its values — two `Money(100, "EGP")` are interchangeable, so it's immutable and compared by value.

```csharp
public sealed record Address(string Street, string City, string Country);   // VO — no Id
public sealed record Money
{
    public decimal Amount { get; }
    public string Currency { get; }
    private Money(decimal a, string c) { Amount = a; Currency = c; }

    public static Money Of(decimal amount, string currency) =>          // validation in creation
        amount < 0 ? throw new DomainException("Negative amount") : new(amount, currency);

    public Money Add(Money other) =>                                     // behaviour, not just data
        other.Currency != Currency ? throw new DomainException("Currency mismatch")
                                   : Of(Amount + other.Amount, Currency);
}
// EF Core: map with .OwnsOne(...) / ComplexProperty — VOs are columns, not tables
```

**Q: What is an aggregate?**

A: **A transactional consistency boundary.** Its root is the only entry point; everything inside is saved and loaded together, and its invariants are true **at the end of every transaction**.

The four rules to state:
1. **Reference other aggregates by ID**, never by object reference (`CustomerId`, not `Customer`) — otherwise your boundary is fiction and lazy loading drags half the DB into memory.
2. **One aggregate per transaction.** Two aggregates in one transaction means the boundary is wrong or the consistency is really eventual.
3. **Changes between aggregates are eventually consistent** — via a domain event, and across services via an integration event + [[18-Distributed-Systems-Reliability#The transactional outbox|outbox]].
4. **Keep aggregates small.** A `Customer` with 10,000 orders inside it is a load/lock disaster. Size the boundary by *what must be consistent right now*, not by what's related.

```csharp
public class Order : AggregateRoot
{
    private readonly List<OrderLine> _lines = new();
    public IReadOnlyCollection<OrderLine> Lines => _lines.AsReadOnly();  // no external mutation
    public OrderStatus Status { get; private set; }                      // private setters
    public CustomerId CustomerId { get; private set; }                   // by ID, not navigation

    private Order() { }                                                  // EF only

    public static Order Place(CustomerId customerId, IEnumerable<OrderLine> lines)
    {
        var order = new Order { CustomerId = customerId, Status = OrderStatus.Pending };
        order._lines.AddRange(lines);
        order.EnsureInvariants();
        order.Raise(new OrderPlacedDomainEvent(order.Id));               // event from inside the domain
        return order;
    }

    public void Cancel(string reason)     // behaviour guards the state transition
    {
        if (Status == OrderStatus.Shipped) throw new DomainException("Cannot cancel a shipped order");
        Status = OrderStatus.Cancelled;
        Raise(new OrderCancelledDomainEvent(Id, reason));
    }
}
```

**Q: Anemic vs rich domain model?**

A: Anemic = public getters/setters plus a service that mutates them — the object is a data bag and the rules live scattered in services, so the same rule gets enforced in three places and missed in the fourth. Rich = state is private and changes only through methods that enforce invariants.

**Be fair about it:** anemic models are *fine* for genuine CRUD, and pretending otherwise is over-engineering. The test is: **does this thing have rules?** A lookup table has none — give it a CRUD slice. An order lifecycle has many — give it a model.

**Q: Where do invariants live vs FluentValidation?**

A: Two different questions, and the distinction is a strong discriminator:

| | FluentValidation (boundary) | Domain (invariants) |
|---|---|---|
| Question | "Is this **request** well-formed?" | "Is this **business rule** satisfied?" |
| Examples | required fields, string length, email format, quantity > 0 | "cannot cancel a shipped order", "credit limit not exceeded", "seat not already booked" |
| Runs | in the MediatR validation behaviour, before the handler | inside entity methods / factory methods |
| Failure → | `400 Bad Request` with field errors | `DomainException` → `409 Conflict` / `422` |
| Needs DB? | no | often yes (the aggregate is already loaded) |

"If the rule would still be true with a different UI or a different API, it belongs in the domain. If it's about the *shape of this request*, it belongs at the boundary." A domain object must **never** rely on a validator having run — it protects itself.

---

## Domain events vs integration events

**Q: What's the difference?** *(a real senior discriminator — most candidates blur them)*

| | **Domain event** | **Integration event** |
|---|---|---|
| Scope | inside one bounded context, **in-process** | crosses services/contexts, over a broker |
| Transport | in-memory dispatch (MediatR `INotification`) | RabbitMQ / MassTransit |
| Payload | can carry domain objects | **contract** — primitives only, versioned, public |
| Naming | `OrderPlacedDomainEvent` (past tense, domain language) | `OrderPlaced` v1 (a published API) |
| Coupling | may change with the domain, freely | **breaking changes hurt other teams** |
| Delivery | exactly once, same process, same transaction | at-least-once, must be idempotent |

**The flow:** domain event (in-process, may update other aggregates) → a handler translates it into an integration event → written to the **outbox in the same transaction** → relayed to the broker.

```csharp
// Dispatch domain events from a SaveChanges interceptor — no handler ever remembers to do it
public class DomainEventDispatchingInterceptor : SaveChangesInterceptor
{
    private readonly IPublisher _publisher;

    public override async ValueTask<int> SavedChangesAsync(       // AFTER commit
        SaveChangesCompletedEventData eventData, int result, CancellationToken ct)
    {
        var entities = eventData.Context!.ChangeTracker.Entries<AggregateRoot>()
            .Where(e => e.Entity.DomainEvents.Count != 0).Select(e => e.Entity).ToList();

        var events = entities.SelectMany(e => e.DomainEvents).ToList();
        entities.ForEach(e => e.ClearDomainEvents());             // clear BEFORE publishing (re-entrancy)

        foreach (var domainEvent in events)
            await _publisher.Publish(domainEvent, ct);

        return await base.SavedChangesAsync(eventData, result, ct);
    }
}
```

**Q: Why does dispatching *before* vs *after* commit change the guarantees?** *(this is the question)*

| | **Before `SaveChanges` (inside the transaction)** | **After commit** |
|---|---|---|
| Atomicity | handler failure **rolls back the whole thing** | the commit already happened; a failure leaves work undone |
| Handlers may | mutate other aggregates — changes join the same transaction | not touch the DB expecting atomicity |
| Danger | a handler doing I/O (email, HTTP) **holds a DB transaction open** across the network → lock contention, pool exhaustion | events can be **lost** if the process crashes after commit |
| Reads see | uncommitted state (the ID may not exist to anyone else yet) | committed, consistent state |
| Right for | pure in-domain side effects that must be atomic | anything with external side effects |

**The correct combination — say it exactly like this:**
> "In-domain side effects dispatch **before** commit so they're atomic. External side effects — emails, integration events, webhooks — must **never** happen inside the transaction, because I'd be holding DB locks across an SMTP call, and because the transaction can still roll back after I've sent an email I can't unsend. So those go to the **outbox table in the same transaction**, and a relay publishes them after commit. That converts 'lost events after commit' into at-least-once delivery, which is why consumers must be idempotent."

That single answer covers domain events, integration events, dispatch ordering, the dual-write problem, and idempotency — see [[18-Distributed-Systems-Reliability#The transactional outbox|the outbox]].

---

## Rapid-Fire Defense Drill

Say each answer out loud in under 20 seconds.

| Probe | Your answer, compressed |
|---|---|
| "Why vertical slices?" | Change locality — a feature is a folder. Cost: duplication and no home for shared logic; it needs discipline or it rots into transaction scripts. |
| "When would you use layers instead?" | Big team needing mandated structure, or a rich domain reused across many use cases. |
| "Isn't MediatR just indirection?" | Yes, and that's the cost. I buy the **pipeline**: validation, transaction, logging, caching in one place. Without behaviours I wouldn't use it. |
| "Name a behaviour you wrote." | Transaction behaviour: commands open a transaction, handler runs, `SaveChanges` dispatches domain events, commit. Handlers never call `SaveChanges`. |
| "Why wrap EF in a repository?" | Aggregate-shaped writes and keeping `IQueryable` out of handlers. Reads bypass it entirely. Generic `Repository<T>` adds nothing — `DbSet<T>` already is one. |
| "Testcontainers killed that argument." | Agreed for testability. My reason is domain expressiveness and aggregate boundaries, not mocking. |
| "Is CQRS event sourcing?" | No. CQRS separates read and write paths; event sourcing is a storage model. Mine is CQRS without events. |
| "Where's your read model?" | Same database, projections and two denormalised views. I stopped before a separate store to avoid eventual consistency in the UI. |
| "What is an aggregate?" | The transactional consistency boundary. One per transaction, referenced by ID, kept small. |
| "Anemic model — bad?" | Only where there are rules. Lookup tables get CRUD; order lifecycles get a model. |
| "FluentValidation vs domain rules?" | Request shape at the boundary → 400. Invariants in the entity → `DomainException` → 409. The entity never trusts the validator ran. |
| "Domain vs integration event?" | In-process vs contract over a broker. Domain events dispatch on `SaveChanges`; integration events go through the outbox. |
| "Before or after commit?" | In-domain effects before (atomic); external effects after, via the outbox — never hold a transaction open across an HTTP call. |
| "What would you change if you rebuilt it?" | *Have one real answer ready.* Silence here reads as never having reflected on it. |
