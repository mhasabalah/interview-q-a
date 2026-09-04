---
title: Event Sourcing & Event-Driven Architecture
aliases: [Event Sourcing, EventStoreDB, EDA, Event-Driven Architecture, Projections]
tags: [event-sourcing, eda, eventstoredb, cqrs, architecture, interview]
order: 22
---

# Event Sourcing & Event-Driven Architecture — Interview Q&A

> [!info]+ Related Notes
> [[17-Architecture-Defense|Architecture Defense]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]] · [[11-Module-Communication|Module Communication]] · [[12-RabbitMQ-MassTransit|RabbitMQ & MassTransit]] · [[07-Domain-Driven-Design|Domain-Driven Design]] · [[21-Database-Part-2|Database Part 2]] · [[23-Observability|Observability]]

> [!danger]+ Why this note exists
> **"Event Sourcing" and "Event-Driven Architecture" are on your CV, and one of them is a project bullet** — *"persisted the Booking aggregate to EventStoreDB as an append-only stream, giving a full audit trail and rebuildable projections."* A skills-list word gets a shallow question; a **project bullet gets a deep one**, because the interviewer assumes you made the decisions.
>
> The three questions you will actually be asked:
> 1. **"Why event sourcing for that aggregate?"** → and the answer must include *why not for the others*
> 2. **"How do you handle concurrency / rebuild a projection / version an event?"** → the mechanics
> 3. **"What did it cost you?"** → if you can't name the pain, you didn't build it
>
> Read Part 0 first. Most candidates lose this round in the first sentence by using "event" to mean three different things.

---

# Part 0 — The vocabulary problem (read this first)

**Q: What is an "event"?** Three different things wear the word, and conflating them is the fastest way to sound junior:

|                    | **Domain event**                     | **Integration event**                         | **Event-sourcing event**                         |
| ------------------ | ------------------------------------ | --------------------------------------------- | ------------------------------------------------ |
| Purpose            | something happened *inside* my model | telling **other services** something happened | **the state itself**                             |
| Scope              | in-process, one bounded context      | cross-boundary contract                       | one aggregate's stream                           |
| Lifetime           | discarded after handling             | consumed, then discarded                      | **kept forever — it IS the data**                |
| Can you change it? | freely                               | carefully, it's a public contract             | **never** — it's history                         |
| Example            | `OrderPlacedDomainEvent`             | `OrderPlaced` v1 on RabbitMQ                  | `SeatHeld`, `PaymentAuthorised` in `booking-123` |

**And the two architectures are independent:**

- **EDA** = services communicate by publishing/subscribing to events instead of calling each other. Says **nothing** about how you store data.
- **Event Sourcing** = you store an aggregate's state as its sequence of events. Says **nothing** about how services communicate.

> **You can have EDA with a plain relational store (most systems). You can have event sourcing inside a monolith with no broker at all. They're often used together — because an event-sourced aggregate already has events to publish — but they solve different problems.**

Saying that sentence unprompted is worth more than any amount of EventStoreDB API knowledge. See also [[17-Architecture-Defense#Domain events vs integration events|domain vs integration events]] and [[17-Architecture-Defense#CQRS — where on the spectrum, and why you stopped there|the CQRS spectrum]] (CQRS ≠ event sourcing either).

---

# Part 1 — Event-Driven Architecture

## The basics

**Q: What is event-driven architecture?**

A: Components communicate by **emitting facts about the past** rather than issuing commands to each other. The producer doesn't know who consumes, or whether anyone does. That inverts the dependency: instead of *Order calls Billing*, *Order announces `OrderPlaced`* and Billing chooses to care.

**Command vs Event vs Query** — the distinction they'll test:

| | **Command** | **Event** | **Query** |
|---|---|---|---|
| Intent | "do this" | "this happened" | "tell me" |
| Tense | imperative — `PlaceOrder` | **past** — `OrderPlaced` | interrogative |
| Recipients | exactly **one** handler | **zero or many** subscribers | one |
| Can be rejected? | **yes** — it may fail validation | **no** — it's already history | n/a |
| Coupling | sender knows the receiver | publisher knows nobody | caller knows the source |

A command that "can't be refused" is really an event with the wrong name; an event that only one specific service may handle is really a command with the wrong name. Naming discipline here is a genuine seniority signal.

## The three flavours of EDA — the framing that scores

Most candidates say "EDA" and mean one thing. There are three, with very different trade-offs (Fowler's taxonomy):

| Pattern | The event carries | Consumer must | Pros | Cons |
|---|---|---|---|---|
| **1. Event notification** | just an ID — `OrderPlaced { OrderId }` | **call back** for details | tiny events, no duplication, no stale data | **chatty** — a callback per event; the producer must stay available; you've re-coupled |
| **2. Event-carried state transfer** | the data the consumer needs — `OrderPlaced { OrderId, CustomerId, Total, Lines[] }` | nothing — it has what it needs | **consumer autonomy**: works when the producer is down; no callbacks | data duplication, staleness, **fatter contracts that are harder to version** |
| **3. Event sourcing** | the full history, and it *is* the source of truth | fold it into state | audit, replay, rebuildable read models | the whole cost list in Part 5 |

**The senior answer to "which do you use?"** — *"Mostly event-carried state transfer, deliberately, because the point of decoupling is that Billing keeps working when Ordering is down; if the consumer has to call back for the data, I've paid the async price and kept the coupling. The cost is duplicated data and fatter contracts, so I only carry what consumers actually need, and I keep an ID in there so they *can* call back for the rare full detail."*

## What EDA buys and what it charges

**Buys you:** temporal decoupling (the consumer can be down and catch up) · adding consumers without touching the producer · natural load levelling under bursts · a real audit of what happened · independent scaling per consumer.

**Charges you — and you must say these:**
- **Eventual consistency becomes a UI problem**, not just a technical one.
- **No stack trace across the system.** "Why did this happen?" needs [[23-Observability|distributed tracing]] and correlation IDs, or it's archaeology.
- **Contracts are now public and versioned** — a rename breaks strangers.
- **At-least-once delivery** → every consumer must be idempotent ([[18-Distributed-Systems-Reliability#Idempotency|idempotency]]).
- **Ordering is not free** (below).
- **Testing is harder** — you're testing a choreography, not a call.
- **Cyclic event chains**: A publishes, B reacts and publishes, C reacts and publishes something A listens to. Nobody notices until production.

**When NOT to use EDA:** a simple CRUD app · a flow needing a **synchronous answer** for the user right now · strong cross-entity consistency requirements · a small team without the ops maturity for a broker and tracing · fewer than ~3 collaborating components (you're adding a broker to avoid a method call).

## Ordering, versioning and the practical rules

**Ordering:** brokers guarantee order only **per partition/queue**, never globally. The fixes, in order of preference:
1. **Design consumers not to need order** — include a version/timestamp and ignore anything older than what you've already applied (this is the *right* answer most of the time).
2. **Partition by aggregate ID** so all events for one entity go to one partition, processed serially.
3. Single-threaded consumption — correct, and it caps your throughput.

**Event versioning — the rules:**
- **Additive only.** Add optional fields; never rename, never repurpose, never change a type or a unit.
- **Tolerant reader**: consumers ignore fields they don't know, and tolerate missing optional ones.
- **New meaning = a new event type** (`OrderPlacedV2`), published alongside the old for a deprecation window.
- **Never leak internal/domain types into a contract** — a public event is an API, not a DTO of your entity.
- Keep them **thin enough to version, fat enough to be useful**: identifiers, the changed facts, `OccurredOn`, and a `MessageId` for dedupe.

---

# Part 2 — Event Sourcing: the basics

**Q: What is event sourcing?**

A: Instead of storing **current state** and overwriting it, you store the **ordered sequence of events that produced it**. Current state is derived: `state = fold(apply, events)`.

```text
STATE-STORED (normal)                    EVENT-SOURCED
┌───────────────────────────┐            booking-123 stream (append-only, immutable):
│ bookings                  │            ┌─ 0 SeatHeld        { seat: 14A, until: 10:15 }
│ id=123 status=Confirmed   │            ├─ 1 PaymentAuthorised { amount: 250 }
│ seat=14A total=250        │            ├─ 2 BookingConfirmed  { at: 10:07 }
└───────────────────────────┘            └─ 3 SeatChanged       { from: 14A, to: 12C }
UPDATE overwrote the truth.              Nothing was ever overwritten.
You know WHAT it is.                     You know what it is AND HOW IT GOT THERE.
```

**The analogies that land:** a **bank ledger** (you don't overwrite a balance, you append transactions and the balance is the sum) · **git** (commits are the truth; the working tree is a projection) · **accounting**, where overwriting history is literally fraud.

**Q: How do you get the current state?** *Rehydration* — read the stream, apply each event in order:

```csharp
public class Booking : EventSourcedAggregate
{
    public BookingId Id { get; private set; } = default!;
    public string? Seat { get; private set; }
    public BookingStatus Status { get; private set; }

    // ---- COMMANDS: validate against current state, then RAISE an event ----
    public void Confirm()
    {
        if (Status != BookingStatus.PaymentAuthorised)          // the invariant
            throw new DomainException("Cannot confirm before payment is authorised");

        Raise(new BookingConfirmed(Id, DateTime.UtcNow));        // decide -> event
    }

    // ---- APPLY: mutate state from an event. NO validation, NO side effects. ----
    // This runs during rehydration too, so it must be pure and must never fail.
    protected override void Apply(object e) => _ = e switch
    {
        SeatHeld ev          => Set(() => { Id = ev.BookingId; Seat = ev.Seat; Status = BookingStatus.Held; }),
        PaymentAuthorised    => Set(() => Status = BookingStatus.PaymentAuthorised),
        BookingConfirmed     => Set(() => Status = BookingStatus.Confirmed),
        SeatChanged ev       => Set(() => Seat = ev.To),
        _                    => Set(() => { })                   // tolerate unknown/old events
    };

    public static Booking Rehydrate(IEnumerable<object> history)
    {
        var b = new Booking();
        foreach (var e in history) b.Apply(e);                   // fold
        return b;
    }
}
```

> [!warning] The rule that catches people out
> **`Apply` must never validate and never have side effects.** It replays historical events — including events written by code that no longer exists, under rules that have since changed. If `Apply` throws on old data, you can no longer load the aggregate. **Validation lives in the command method; `Apply` only mutates.**

**What you gain:** a complete audit trail *for free* (not a bolt-on table someone forgets to write to) · **temporal queries** — "what did this look like on 3 March?" · **new read models from old data** — build a projection today that answers a question nobody asked when the data was written · debugging by replaying the exact sequence · no lossy updates, ever.

**What you pay:** everything in [[#Part 5 — When NOT to event source|Part 5]] — and you must lead with it, not be dragged to it.

---

# Part 3 — Event Sourcing mechanics (the senior half)

## Streams and stream naming

One stream per aggregate instance: `booking-123`, `account-987`. The stream **is** the consistency boundary — which is exactly the [[07-Domain-Driven-Design#Part 2 — Tactical Design|aggregate boundary]] from DDD, now made physical. If two things must be consistent, they're one stream; if they're separate streams, they are **eventually** consistent, no exceptions.

## Concurrency: expected version *(the mechanism they will ask about)*

**Q: Two commands hit the same aggregate at once. What stops them corrupting it?**

A: **Optimistic concurrency on the stream revision.** You read the stream, you know it was at revision 4, and you append *asserting* it's still at 4. If someone else appended in between, the store rejects you.

```csharp
// 1. LOAD
var result   = _client.ReadStreamAsync(Direction.Forwards, streamName, StreamPosition.Start, cancellationToken: ct);
var history  = await Deserialize(result);
var booking  = Booking.Rehydrate(history);
var expected = StreamRevision.FromInt64(history.Count - 1);   // what I believe the stream is at

// 2. DECIDE — pure domain logic, no I/O
booking.Confirm();

// 3. APPEND with the assertion
try
{
    await _client.AppendToStreamAsync(streamName, expected, ToEventData(booking.PendingEvents), cancellationToken: ct);
}
catch (WrongExpectedVersionException)
{
    // Someone else wrote first. My decision was based on stale state.
    // Reload, re-decide, re-append (bounded retries) — or return 409 if the command is not safe to replay.
}
```

**Why this is the good answer:** it's the same optimistic-concurrency idea as a `rowversion` column in EF Core ([[21-Database-Part-2#EF Core optimistic and pessimistic in practice|see Part 2 of the DB note]]), but the store enforces it natively and there is **no lock and no row to contend on** — appends are the only write.

The expected-version options: `StreamState.NoStream` (creating — this also makes creation idempotent), `StreamState.Any` (no check — use it only when the events genuinely commute), or an explicit revision (the default for any aggregate with invariants).

## Snapshots

**Q: A stream has 50,000 events. Do you replay them all?**

A: Usually yes and it's fine — replaying a few thousand small events is milliseconds. Reach for a **snapshot** only when you've measured a problem:

- Store `{ revision, serialised state }` periodically (every N events, or on a schedule).
- Load = newest snapshot + only the events *after* its revision.
- **A snapshot is a cache, never the truth.** You must be able to delete every snapshot and rebuild from events alone.
- **Version your snapshots.** When the aggregate's shape changes, old snapshots are garbage — include a schema version and ignore stale ones rather than trying to migrate them.
- If an aggregate genuinely needs snapshots early, that's often a hint the **aggregate is too big** — a 50k-event stream usually wants closing out (`AccountClosed` → new stream/period) rather than a snapshot.

## Projections and read models

**Q: How do you query event-sourced data? "Find all confirmed bookings for customer X" is impossible over streams.**

A: **You don't query the event store — you project.** A subscription reads events in order and maintains a read model shaped for querying (SQL table, Mongo document, Elasticsearch index). This is why event sourcing effectively forces CQRS.

```csharp
// A catch-up subscription over all events, driven by a stored checkpoint
await foreach (var e in _client.SubscribeToAll(FromAll.After(_checkpoint.Load()), cancellationToken: ct))
{
    switch (Deserialize(e))
    {
        case BookingConfirmed ev:
            // IDEMPOTENT upsert — this event may be delivered again after a restart
            await _read.UpsertAsync(ev.BookingId, r => { r.Status = "Confirmed"; r.ConfirmedAt = ev.At; }, ct);
            break;
        case SeatChanged ev:
            await _read.UpsertAsync(ev.BookingId, r => r.Seat = ev.To, ct);
            break;
    }

    await _checkpoint.Save(e.OriginalPosition);   // save AFTER the write => at-least-once, hence idempotent
}
```

**The four rules of projections:**
1. **Idempotent** — checkpoints are saved after the write, so a crash replays the last event. Upserts, not inserts; absolute sets, not increments (or store the last applied position *with* the row).
2. **Checkpointed** — persist your position, or a restart replays from the beginning of time.
3. **No side effects.** A projection must **never** send an email or call an API — because it *will* be replayed. Side effects belong in a separate process manager/reaction handler that runs only on live events, never during a rebuild. **This is the classic production disaster: rebuilding a projection and emailing 40,000 customers again.**
4. **Rebuildable** — deleting the read model and replaying from zero must produce exactly the same result. Rebuild time is a real operational number; know roughly what yours is.

**Rebuild is the superpower:** a new question arrives ("show conversion from held → confirmed by hour"), and you write a projection that answers it **for all history**, not just from today. That single capability is the strongest argument for event sourcing, and it's the one to lead with.

**Catch-up vs persistent subscriptions** — a real EventStoreDB distinction: a **catch-up** subscription is client-driven, *you* own the checkpoint, and it's ordered — the right choice for building read models. A **persistent** subscription is server-managed with competing consumers and per-message ack/nack/park, giving you parallelism and a built-in poison-message park queue — the right choice for reactions/integrations where order matters less than throughput.

## Event versioning in an event-sourced store

Harder than integration-event versioning, because **you cannot rewrite history** and old events must stay readable forever.

| Technique | What it is | Use when |
|---|---|---|
| **Weak/tolerant schema** | new fields optional with defaults; deserializer ignores unknowns | the default; covers most changes |
| **Upcasting** | on read, transform v1 → v2 in a pipeline before it reaches `Apply` | a real shape change (split a field, change a unit) |
| **New event type** | `SeatChanged` → `SeatChangedV2`; `Apply` handles both forever | the meaning changed, not just the shape |
| **Copy-and-transform** | rewrite the whole store into a new stream set with new schema | a last resort; a migration project, with downtime or dual-run |

The discipline that prevents most of this pain: **events carry business facts, not internal structures.** `PriceChanged { NewPriceCents, Currency }` survives a refactor; `PriceChanged { PricingEngineDto }` does not.

## Deleting data (GDPR) — the question that exposes people

**Q: A user invokes their right to erasure. Your events are immutable. Now what?**

A: This is event sourcing's genuinely hard problem, and having an answer is a strong signal:

- **Crypto-shredding (the standard answer):** encrypt personal data inside events with a **per-subject key** held outside the event store. To erase, **delete the key** — the events remain structurally intact, and the PII is unrecoverable. Downside: those events can't be fully replayed afterwards, so projections must tolerate unreadable PII fields.
- **Keep PII out of events entirely** — events hold a `CustomerId`, and personal data lives in a normal, mutable table you can delete from. Simplest and best when you can arrange it.
- **Stream deletion/truncation + scavenge** — possible, but it breaks the "history is immutable" contract and any projection that depends on those events.

---

# Part 4 — EventStoreDB specifics

*(Your CV names it — expect at least a couple of concrete questions. Note the product was rebranded **KurrentDB** in 2025; recognise both names.)*

| Concept | What to know |
|---|---|
| **Stream** | the unit of append and of optimistic concurrency; named `category-id` (e.g. `booking-123`) |
| **`$all`** | the global ordered log of every event — what you subscribe to for projections, usually with a server-side filter by event type or category prefix |
| **System projections** | `$ce-booking` (category stream) and `$et-BookingConfirmed` (by event type) — enabled per-server, and they let you subscribe to a slice without filtering everything client-side |
| **Append** | `AppendToStreamAsync(stream, expectedRevision, events)` → `WrongExpectedVersionException` on conflict |
| **Event shape** | `EventData`: id (used for **idempotent appends**), type name, data, and **metadata** — put `correlationId`, `causationId`, `userId`, schema version in metadata, never in the payload |
| **Catch-up subscription** | client-side checkpoint, ordered — for read models |
| **Persistent subscription** | server-managed, competing consumers, ack/nack/park — for reactions |
| **Stream metadata** | `$maxAge`, `$maxCount`, `$tb` (truncate-before) — retention per stream |
| **Scavenging** | the offline-ish process that actually reclaims disk from deleted/expired events; until it runs, nothing is really gone |
| **Soft vs hard delete** | soft = stream can be recreated; **hard delete is permanent and the stream name can never be reused** |
| **Clustering** | gossip-based cluster, leader/follower, quorum writes |

**Correlation and causation IDs** deserve a sentence of their own: `correlationId` groups everything caused by one original user action; `causationId` points at the *specific* message that caused this one. Together they let you reconstruct an entire causal tree from the log — and they're what makes [[23-Observability|tracing]] across an event-sourced system possible at all.

**Alternatives to name** (shows you chose rather than defaulted): **Marten** (event store + document store on PostgreSQL — often the pragmatic .NET choice when you already run Postgres and don't want another database), a **hand-rolled append-only table** (`stream_id, version, type, payload` with a unique constraint on `(stream_id, version)` — that unique index *is* your optimistic concurrency, and for one aggregate it's genuinely enough), and **Axon**/**Kafka** in other ecosystems. *(Kafka is a log, not an event store: no per-aggregate expected-version check and no per-stream reads — say that if it comes up.)*

---

# Part 5 — When NOT to event source

**This part is the senior answer. Lead with it.**

> **Event sourcing is an *aggregate-level* decision, not a system-level one.**

Event source an aggregate when **the history is itself the business value**: money and ledgers, bookings and reservations, regulated/audited workflows, anything where "how did we get here?" is a real question people ask, and long-lived entities with meaningful state transitions.

**Do not event source:** CRUD and reference data (countries, categories, settings) · a domain with no meaningful transitions (a profile page) · anything where the team can't be trained on it · a system whose main need is *queries*, where you'd be paying full price for projections and getting nothing back · a short-lived project.

**The costs, stated plainly:**

| Cost | Reality |
|---|---|
| **Learning curve** | every developer must understand rehydration, projections, and why `Apply` can't validate. New joiners are slow for weeks. |
| **You cannot just query** | every question needs a projection built and maintained. "Add a column" becomes "add a projection and rebuild it." |
| **Eventual consistency in the UI** | the write succeeded but the list hasn't updated yet — a product problem, not just a technical one. |
| **Versioning is forever** | old events must remain readable for the life of the system. |
| **Operational surface** | another database, subscription lag to monitor, rebuild runbooks, checkpoint management. |
| **Debugging is different** | better once you're fluent (replay the exact sequence), worse until then. |

**Cheaper alternatives that give you 80% of the audit benefit** — naming these proves you chose rather than followed a conference talk: an **audit/history table** written by a `SaveChanges` interceptor · **temporal tables** (SQL Server system-versioning gives you point-in-time queries out of the box) · **CDC/Debezium** streaming changes out of the WAL · an append-only `events` table *alongside* normal state, giving you a log without giving up SQL queries.

> [!tip] The answer to give about *your* project
> *"I event sourced the **Booking** aggregate specifically, because the seat-hold → payment → confirm → change lifecycle is exactly where the business asks 'what happened and when', and because rebuildable projections let me add read models over the full history. The other modules — Flight, Passenger, Identity — are plain state-stored, and that asymmetry was deliberate: event sourcing everything would have paid the full cost for aggregates with no meaningful history. The real pain I hit was projection rebuilds and making sure no side effects lived in a projection handler."*
>
> That answer contains a decision, a boundary, a rejected alternative, and a scar. That's what "senior" sounds like.

---

## Rapid-Fire Drill

| # | Probe | Your answer, compressed |
|---|---|---|
| 1 | EDA vs event sourcing? | Communication style vs storage model. Independent — you can have either without the other. |
| 2 | CQRS vs event sourcing? | CQRS separates read and write paths; ES stores state as events. ES nearly forces CQRS; CQRS needs no events. |
| 3 | Command vs event? | "Do this" (one handler, can be rejected) vs "this happened" (many subscribers, already history). |
| 4 | Three flavours of EDA? | Event notification (ID only, chatty callbacks) · **event-carried state transfer** (autonomy, duplication) · event sourcing. |
| 5 | Why prefer state transfer? | The consumer keeps working when the producer is down — otherwise you paid async costs and kept the coupling. |
| 6 | How is current state derived? | Rehydration: read the stream, `Apply` each event in order, fold to state. |
| 7 | Why must `Apply` never validate? | It replays historical events written under old rules — if it throws, the aggregate can never load again. |
| 8 | How do you handle concurrent commands? | Optimistic concurrency on expected stream revision → `WrongExpectedVersionException` → reload, re-decide, retry. |
| 9 | When do you snapshot? | Only after measuring. A snapshot is a cache, must be versioned, and must be deletable. Often a hint the aggregate is too big. |
| 10 | Why can't you query the event store? | It's a log, not a query model — you build projections. That's why ES forces CQRS. |
| 11 | Number one projection rule? | **No side effects** — it will be replayed. Don't email 40,000 people twice on a rebuild. |
| 12 | Second rule? | Idempotent + checkpointed — checkpoints save after the write, so the last event replays on restart. |
| 13 | The superpower? | Rebuild: answer a brand-new question over *all* history, not just from today. |
| 14 | Versioning an old event? | Tolerant reader → upcasting → a new event type. Never rewrite history; keep events as business facts, not DTOs. |
| 15 | GDPR erasure? | **Crypto-shredding** — per-subject key outside the store, delete the key. Better: keep PII out of events entirely. |
| 16 | Catch-up vs persistent subscription? | Client-checkpointed and ordered (read models) vs server-managed competing consumers with ack/park (reactions). |
| 17 | Is Kafka an event store? | It's a log — no per-aggregate expected-version check, no per-stream read. Different tool. |
| 18 | When would you *not* event source? | CRUD, reference data, no meaningful transitions, a team that can't carry it — it's an **aggregate-level** decision. |
| 19 | Cheaper alternative for audit? | Audit table via a `SaveChanges` interceptor, temporal tables, or CDC. |
| 20 | What did it cost you? | Projection rebuilds, keeping side effects out of handlers, eventual consistency in the UI, and forever-versioning. |
