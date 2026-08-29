---
title: Modular Monolith
aliases: [Modular Monolith, Modulith, Modular Monolith Architecture]
tags: [architecture, modular-monolith, modules, interview]
order: 19
---

# Modular Monolith - Interview Q&A

> [!info]+ Related Notes
> [[20-Choosing-An-Architecture|Choosing an Architecture]] · [[07-Domain-Driven-Design|Domain-Driven Design]] · [[11-Module-Communication|Module Communication]] · [[17-Architecture-Defense|Architecture Defense]] · [[09-Onion-Architecture|Onion Architecture]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]]

> [!danger]+ Why this one matters right now
> The modular monolith is the architecture a senior is expected to **default to** — and the one candidates most often define wrongly. "A monolith with folders" is not it, and saying that loses the round.
>
> The definition to have memorised: **microservice boundaries without the network.**
>
> The follow-up is always the same: *"so when do you split it?"* If you can answer that with named **drivers** rather than "when it gets big", you're done.

---

## What a modular monolith actually is

**Q: Define it.**

A: **One deployable unit** made of **independently designed modules**. Each module owns its data, exposes a small explicit public contract, hides everything else, and could be extracted into its own service without a redesign. One process, one pipeline, one database instance — many autonomous modules.

The point is to **separate two decisions that microservices force you to make together**:

| Decision | Monolith | **Modular monolith** | Microservices |
|---|---|---|---|
| **Logical** modularity | ✗ | **✓** | ✓ |
| **Physical** distribution | ✗ | **✗ (deliberately)** | ✓ |

You get boundaries, ownership and independent reasoning **without** buying network calls, distributed transactions, service discovery, eventual consistency everywhere, and a 10× ops bill. You pay for those later — *if* a real driver shows up.

**Q: How does it differ from the alternatives?** Four things get confused; know all four:

| | Big ball of mud | **Modular monolith** | Microservices | **Distributed monolith** |
|---|---|---|---|---|
| Boundaries | none | **enforced at compile time** | enforced by the network | claimed, not real |
| Deployables | 1 | **1** | N | N |
| Data | shared tables everywhere | **schema per module** | database per service | **shared DB across services** ← the tell |
| Changing one feature | touches everything | **one module** | one service | all of them, in lockstep |
| Deploy | all at once | all at once | independently | **all at once, but over a network** |
| Worst property | can't change it | one process, one stack | ops + distributed failure modes | **every cost, none of the benefits** |

> [!warning] The distributed monolith is the real enemy
> It is strictly worse than either endpoint: you have network latency, partial failure, and versioned contracts **and** you still can't deploy anything independently. Teams get there by splitting into services **before** they knew where the boundaries were. The modular monolith exists precisely so you can discover those boundaries **cheaply** — a wrong boundary costs a refactor, not a migration.

**Q: Isn't this just a well-organised layered monolith?**

A: No — the slicing direction is different, and so is the enforcement.

```text
LAYERED (horizontal)                   MODULAR (vertical, by capability)
├── Controllers/   (all of them)       ├── Modules/
├── Services/      (all of them)       │   ├── Booking/     <- its own layers inside
├── Repositories/  (all of them)       │   ├── Billing/     <- its own schema
└── Models/        (all of them)       │   └── Notifications/
                                       └── Shared/          <- tiny, deliberate
Any service may call any service.      A module may call another only
Any repo may join any table.           through its published Contracts.
Coupling is invisible.                 Coupling is a compile error.
```

In a layered monolith, coupling is **invisible and unpunished**. In a modular monolith, crossing a boundary the wrong way **fails the build**. That enforcement is the whole architecture — remove it and you have folders.

---

## The five rules that make a module a module

If you can't recite these, you can't claim the architecture:

1. **A module owns its data.** Its own schema; **no other module reads its tables.** Not "shouldn't" — *can't*.
2. **The public surface is tiny and explicit.** A `Contracts` project (or namespace): DTOs, integration events, one facade interface. Everything else is `internal`.
3. **No cross-module joins and no cross-schema foreign keys.** Reference other modules' things **by ID**, exactly like referencing another aggregate — see [[07-Domain-Driven-Design#Bounded context ≠ microservice|context ≠ service]].
4. **Communication goes through declared channels only** — the facade for synchronous queries, in-process integration events for notifications. Never reach into internals.
5. **Extractability is the test.** *"If I had to move this module into its own process next month, what breaks?"* If the answer is "a join" or "a shared transaction", **the boundary is fake**.

Each module also owns its **own tests, own EF migrations, and own configuration section**. If two modules must be migrated together, they're one module.

---

## Structure in .NET

```text
src/
  Modules/
    Booking/
      Booking.Domain/           <- entities, VOs, invariants   (internal)
      Booking.Application/      <- handlers, slices            (internal)
      Booking.Infrastructure/   <- DbContext, EF config, jobs  (internal)
      Booking.Contracts/        <- ★ THE ONLY PUBLIC PROJECT ★
      Booking.Tests/
    Billing/
      ... same shape
    Notifications/
      ... same shape
  Shared/
    SharedKernel/               <- ids, Money, Result, base types. TINY. If it grows, you failed.
    Infrastructure/             <- logging, auth, outbox, event dispatcher plumbing
  Host/
    Api/                        <- the single deployable; references Contracts + module registrars
```

**The host must know nothing about a module's internals** — each module registers itself:

```csharp
// Booking.Infrastructure/BookingModule.cs — the module's only entry point
public static class BookingModule
{
    public static IServiceCollection AddBookingModule(this IServiceCollection services, IConfiguration config)
    {
        services.AddDbContext<BookingDbContext>(o => o.UseNpgsql(
            config.GetConnectionString("Default"),
            npg => npg.MigrationsHistoryTable("__migrations", Schemas.Booking)));   // own schema

        services.AddScoped<IBookingModuleApi, BookingModuleApi>();   // the public facade
        services.Scan(s => s.FromAssemblyOf<BookingDbContext>()...); // internal handlers
        return services;
    }

    public static IEndpointRouteBuilder MapBookingEndpoints(this IEndpointRouteBuilder app) { ... }
}

// Host/Program.cs — flat, boring, no knowledge of internals
builder.Services
    .AddBookingModule(builder.Configuration)
    .AddBillingModule(builder.Configuration)
    .AddNotificationsModule(builder.Configuration);

app.MapBookingEndpoints().MapBillingEndpoints();
```

```csharp
// Booking.Contracts — everything another module is allowed to see
public interface IBookingModuleApi                                  // sync queries only
{
    Task<BookingSummary?> GetSummaryAsync(Guid bookingId, CancellationToken ct);
}

public sealed record BookingSummary(Guid Id, Guid CustomerId, decimal Total, string Status);

// Integration events — SAME SHAPE you'd publish over RabbitMQ later. This is the whole trick.
public sealed record BookingConfirmed(Guid BookingId, Guid CustomerId, decimal Total, DateTime OccurredOn);
```

---

## Enforcing the boundary (compile time, not code review)

Discipline does not survive a deadline. Make the boundary a **build failure**:

| Mechanism | Strength | Notes |
|---|---|---|
| **Separate projects + `internal`** | ★★★★ | the backbone: a module's types are literally unreachable |
| **Project reference rules** | ★★★★ | `Billing.Application` may reference `Booking.Contracts` — *never* `Booking.Application` |
| **Architecture tests** (NetArchTest / ArchUnitNET) | ★★★★ | catches what references can't express; runs in CI |
| **Roslyn analyzers / banned symbols** | ★★★ | ban `DbContext` types crossing modules |
| **Folders in one project** | ★ | discipline only — fine for a 3-person MVP, nothing more |

```csharp
[Fact]
public void Modules_must_not_reference_each_others_internals()
{
    var result = Types.InAssembly(typeof(BillingDbContext).Assembly)
        .Should()
        .NotHaveDependencyOnAny("Booking.Domain", "Booking.Application", "Booking.Infrastructure")
        .GetResult();

    result.IsSuccessful.Should().BeTrue(
        $"Billing may only depend on Booking.Contracts. Violations: {string.Join(", ", result.FailingTypeNames ?? [])}");
}

[Fact]
public void Modules_must_not_share_a_DbContext() { /* one DbContext type per module assembly */ }
```

> [!tip] Say this
> "The boundary isn't a convention, it's a **compile error and a failing test**. Every modular monolith that decayed into a ball of mud did so because the boundary was a wiki page."

---

## Data: the part that decides whether it works

**Q: One database or many?**

A: **One database instance, one schema per module** — `booking.*`, `billing.*`, `notifications.*`. You keep operational simplicity (one backup, one connection pool, real transactions inside a module) while keeping the *logical* separation that makes extraction possible.

```sql
-- booking schema owns these; nothing else may read them
booking.bookings(id, customer_id, status, total, ...)
booking.seat_holds(...)

-- billing references by ID only — no FK across schemas
billing.invoices(id, booking_id /* just a Guid */, amount, status, ...)
```

**Q: I need booking data in a billing query. How, without a join?** Three legitimate answers — pick by need:

| Option | How | Cost | Use when |
|---|---|---|---|
| **Ask the module** | `IBookingModuleApi.GetSummaryAsync(id)` — in-process call, microseconds | N+1 if you loop it | one or a few records, always fresh |
| **Keep your own copy** | Billing stores the fields it needs, updated from `BookingConfirmed` events | duplication + eventual consistency | you need it in *your* queries, joins, lists |
| **A reporting read model** | a separate schema fed by events, denormalised for reads | another projection to maintain | cross-module dashboards, exports |

**Never**: `join booking.bookings b on b.id = i.booking_id`. It compiles, it's fast, and it welds the two modules together permanently. **That single join is how the architecture dies.**

**Q: Transactions across modules?**

A: **One module per transaction** — the same rule as one aggregate per transaction. Cross-module consistency is achieved with **events and eventual consistency**, exactly as it would be after extraction.

Now the honest part, which is what a senior actually says:

> "Because it's one database, I *can* commit across modules — and that's the seductive shortcut. If I take it, extraction later becomes a migration project instead of a transport change. So the rule is one module per transaction, and if I ever break it deliberately for delivery pressure, it goes in the ADR as debt with the extraction cost written down."

Where a cross-module operation must not be lost, use the **outbox pattern even in-process**: persist the event in the module's transaction, dispatch after commit. It costs almost nothing now and makes the later split a configuration change — see [[18-Distributed-Systems-Reliability#The transactional outbox|the outbox]].

---

## Communication between modules

```csharp
// 1) SYNCHRONOUS — I need an answer now. Direct in-process call through the facade.
public class InvoiceService(IBookingModuleApi bookings)
{
    public async Task<Result<Invoice>> CreateAsync(Guid bookingId, CancellationToken ct)
    {
        var booking = await bookings.GetSummaryAsync(bookingId, ct);      // no HTTP, no serialization
        if (booking is null) return Result.Failure<Invoice>(BillingErrors.BookingNotFound);
        ...
    }
}

// 2) ASYNCHRONOUS — something happened; whoever cares reacts. Publisher knows no consumers.
public sealed record BookingConfirmed(Guid BookingId, Guid CustomerId, decimal Total, DateTime OccurredOn);

// Booking module publishes (after commit, via outbox)
await _eventBus.PublishAsync(new BookingConfirmed(booking.Id, booking.CustomerId, booking.Total, now), ct);

// Billing module handles — it never referenced the Booking module's internals
internal sealed class CreateInvoiceOnBookingConfirmed(IInvoiceService invoices)
    : IIntegrationEventHandler<BookingConfirmed>
{
    public Task HandleAsync(BookingConfirmed e, CancellationToken ct)
        => invoices.CreateForBookingAsync(e.BookingId, e.Total, ct);
}
```

**The rule that makes extraction cheap:** the in-process bus must use the **same contract shape and the same delivery semantics** you'd get from a broker. Same record, published after commit, handler idempotent. Then "extract to a service" is swapping the dispatcher for MassTransit — not a redesign. See [[11-Module-Communication|Module Communication]] and [[17-Architecture-Defense#Domain events vs integration events|domain vs integration events]].

**Sync or async?** Sync when you need the answer to continue (and can tolerate the coupling). Async when the other module's work is a *consequence*, not a precondition. Default to **async for side effects, sync for queries** — the same instinct you'd use across services.

---

## When to choose it — and when not

**Choose a modular monolith when:**
- **You don't yet know where the boundaries are.** This is the most common truth, and the strongest reason.
- The team is roughly **one to five teams** (say up to ~30–50 engineers) with a shared deploy cadence.
- One coherent product, one tech stack, one runtime.
- **Ops capability is limited** — no platform team, no k8s expertise, no distributed tracing yet.
- Speed of change matters more than independent scaling — startups, internal products, most B2B SaaS.
- You want to be **microservice-ready without paying microservice rent**.

**Don't, when:**
- Two parts have genuinely **different scaling profiles** and the expensive one dominates cost (video encoding, ML inference, search).
- Multiple teams need **truly independent deploy cadence** and the shared pipeline is the bottleneck.
- **Compliance/isolation** requires separation (PCI, data residency, differing audit boundaries).
- A part genuinely needs a **different technology** (Python ML, a specialist runtime).
- One deployable is a hard operational limit for your scale (rare, and rarer than people claim).

---

## The trade-offs — say these before they're asked

- **One process = one blast radius.** A memory leak, an infinite loop, or [[04-CSharp-Fundamentals#Concurrency and Thread Safety|thread pool starvation]] in the Notifications module takes down Booking too. Microservices don't remove that risk, they *relocate* it — but the relocation is real and you should concede it.
- **Scaling is all-or-nothing.** You replicate the whole process even if only one module is hot. Usually cheap and fine; occasionally the exact reason to split.
- **One runtime, one stack, one framework version.** An upgrade is all-or-nothing.
- **Deploys couple teams.** One failing test blocks everyone. This demands good CI, trunk-based development, and feature flags — and if the org can't do those, the monolith gets blamed for a process problem.
- **Boundary erosion is one merge away.** Without automated enforcement, someone adds the join at 2am before a release.
- **Build and test times grow** with the codebase.
- **It does not save you from bad design.** A modular monolith with wrong boundaries is a ball of mud with extra project files.

---

## Extraction modular monolith → microservice

This is the payoff, and the answer to *"so when do you split?"*.

**Step 0 — confirm a driver exists.** Independent scaling · independent deploy cadence · team autonomy at scale · compliance isolation · a genuinely different stack. **"It's getting big" is not a driver.** Extract *one* module, the one with the driver — not all of them.

```text
1. FREEZE THE CONTRACT      all traffic already goes through Booking.Contracts?
                            if not, fix that first — that IS the extraction work

2. SWAP THE TRANSPORT       in-process event dispatcher -> MassTransit/RabbitMQ,
                            same records, same handlers. Behaviour unchanged.

3. SPLIT THE DATA           move booking.* to its own database; remove residual joins;
                            dual-write or sync during the transition   <- the hard part

4. DEPLOY AS A SERVICE      same module, own host process, behind the same facade interface;
                            the in-process implementation becomes an HTTP/gRPC adapter

5. SHIFT TRAFFIC            feature flag; keep the in-process path as fallback

6. DELETE THE OLD PATH      a half-migration with two sources of truth is worse than either end

7. PAY THE NEW TAXES        retries + backoff/jitter, idempotent consumers, outbox, timeouts,
                            circuit breakers, distributed tracing, contract versioning
                            -> [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]]
```

**The sentence that ties it together:** *"Steps 1 and 2 are nearly free — because I made those decisions on day one. Step 3 is the real project. That's exactly why schema-per-module and wire-shaped contracts are non-negotiable from the start: they're free at the beginning and they're the entire cost of the split later."*

---

## Rapid-Fire Drill

| # | Probe | Your answer, compressed |
|---|---|---|
| 1 | Define a modular monolith. | One deployable, independently designed modules, each owning its data behind an explicit contract. **Microservice boundaries without the network.** |
| 2 | How is it different from a layered monolith? | Layers slice horizontally and coupling is invisible; modules slice by capability and crossing the boundary is a **compile error**. |
| 3 | What's a distributed monolith? | Services that must deploy together — usually sharing a database. Every microservice cost, no benefit. |
| 4 | One DB or many? | One instance, **one schema per module**. Operational simplicity, logical separation. |
| 5 | How do you query another module's data? | Call its facade, or keep your own copy updated by its events, or a reporting read model. **Never a join.** |
| 6 | Transactions across modules? | One module per transaction; cross-module is events + eventual consistency — same as one aggregate per transaction. |
| 7 | Why the same event shape as a broker? | So extraction is a **transport swap**, not a redesign. |
| 8 | How do you stop the boundary rotting? | Separate projects + `internal`, reference rules, and **architecture tests in CI**. A wiki page is not enforcement. |
| 9 | Biggest weakness? | One process, one blast radius, one stack, all-or-nothing scaling and deploys. |
| 10 | When do you split? | On a named driver: scaling profile, deploy cadence, team autonomy, compliance, technology. **Not size.** |
| 11 | What's the expensive part of splitting? | **The data**, always. Contracts and transport are cheap if you set them up on day one. |
| 12 | Why not just start with microservices? | Because you don't know the boundaries yet, and a wrong boundary in a monolith costs a refactor — in microservices it costs a migration. |
