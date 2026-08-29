---
title: Domain-Driven Design
aliases: [DDD, Domain-Driven Design]
tags: [ddd, architecture, interview]
order: 7
---

# Domain-Driven Design (DDD) - Interview Q&A

> [!info]+ Related Notes
> [[08-Clean-Architecture|Clean Architecture]] · [[09-Onion-Architecture|Onion Architecture]] · [[06-Database|Database]] · [[17-Architecture-Defense|Architecture Defense]]

> [!tip] Going deeper
> For the *defending-it-out-loud* versions — invariants vs FluentValidation, aggregate sizing, anemic-vs-rich as a **judgement call**, and **domain events vs integration events** (dispatch before vs after commit) — see [[17-Architecture-Defense#DDD tactical patterns|Architecture Defense]].

---

## Overview

**Q: What is Domain-Driven Design?**

A: Approach to software development that focuses on complex domain logic. Places domain model at center of development. Emphasizes collaboration between technical and domain experts. Uses ubiquitous language.

**Core Concepts:**
- Ubiquitous Language
- Bounded Contexts
- Entities
- Value Objects
- Aggregates
- Domain Events
- Repositories
- Domain Services

**DDD has two halves, and they are not equally weighted:**

| | **Strategic design** ([[#Part 1 — Strategic Design\|Part 1]]) | **Tactical design** ([[#Part 2 — Tactical Design\|Part 2]]) |
|---|---|---|
| Answers | *where are the boundaries, and where do we invest?* | *how do I model inside one boundary?* |
| Tools | subdomains, core/supporting/generic, bounded contexts, ubiquitous language, context maps, EventStorming | entities, value objects, aggregates, domain events, repositories, domain services |
| Scale | system and organisation | classes and packages |
| Get it wrong and | you build the wrong system, or rebuild a solved problem | you write awkward code inside the right system |
| Interview weight | **this is the senior signal** | table stakes |

**You can do tactical DDD perfectly inside a boundary that should never have existed.** That's why Part 1 comes first.

---

# Part 1 — Strategic Design

> [!danger]+ Why this part decides the interview
> Almost every candidate can define an entity and a value object. **Tactical DDD is table stakes; strategic DDD is the senior signal**, because it's the part that makes *architecture decisions* — what to build, what to buy, where the seams go, which team owns what.
>
> Eric Evans himself has said the biggest mistake in his book was putting the tactical patterns first — people read half of it and think DDD means "entities and repositories". If you can talk about **subdomains, boundaries, context maps and language**, you're immediately in a different bracket.
>
> The one-sentence version to have ready: **"DDD is not a coding style. It's a way of deciding where to draw boundaries and where to spend your best engineers."**

## Domain, Subdomain and Bounded Context

**Q: What's the difference between a domain, a subdomain and a bounded context?** *(the classic opener — get the problem/solution split right)*

| Term | Space | What it is | Who defines it |
|---|---|---|---|
| **Domain** | problem | the business you're in — "online travel booking" | the business, it already exists |
| **Subdomain** | problem | a coherent slice of that business — *booking*, *payments*, *reviews*, *identity* | discovered by analysis, not invented |
| **Bounded Context** | **solution** | an explicit boundary inside which **one model and one language apply** | **you design it** — it's an engineering decision |

> **Subdomains are found. Bounded contexts are drawn.** The problem space exists whether or not you write software; the solution space is your architecture.

```text
DOMAIN: Online Travel                            (problem space — the business)
├── Subdomain: Booking & Inventory  [CORE]
├── Subdomain: Pricing              [CORE]
├── Subdomain: Payments             [GENERIC]  -> buy (Stripe)
├── Subdomain: Notifications        [GENERIC]  -> buy (SendGrid)
├── Subdomain: Identity             [GENERIC]  -> buy (Auth0 / Entra)
└── Subdomain: Reviews              [SUPPORTING]

                 ▼ your design decision ▼

SOLUTION: Bounded Contexts                       (solution space — your code)
┌──────────────┐   ┌─────────────┐   ┌──────────────┐   ┌─────────────┐
│  Reservation │──►│   Pricing   │   │   Payment    │   │  Reviews    │
│  (core, rich │   │ (core, rich │   │ (ACL around  │   │ (CRUD, thin)│
│   model)     │   │  model)     │   │  Stripe)     │   │             │
└──────────────┘   └─────────────┘   └──────────────┘   └─────────────┘
```

**Q: Should a bounded context map 1:1 to a subdomain?**
A: **Ideally yes, in practice not always** — and knowing why is the senior answer. One subdomain may need two contexts (different lifecycles or teams). One context may cover two small subdomains (not worth splitting yet). A legacy system may cram five subdomains into one context — that's the classic **Big Ball of Mud**, and naming it as a *deliberate, mapped* context beats pretending it isn't there.

**The practical test for "is this one context or two?":** *does the same word mean the same thing on both sides?* If `Customer` in Sales means "someone with a credit limit" and in Shipping means "an address to deliver to", those are **two models** — and forcing them into one class gives you a 40-property god object with half the fields null at any moment. **A shared database table is not a shared model.**

---

## Core, Supporting and Generic subdomains

**Q: How do you decide where to invest engineering effort?** *(this is the strategic question — the one that shows you think like an owner)*

Classify every subdomain on two axes: **how much it differentiates the business**, and **how complex it is**.

| Type | Definition | The test | Build strategy | Who works on it |
|---|---|---|---|---|
| **Core** | your competitive advantage — why customers pick you | "if a competitor copied this exactly, would we lose?" | **build in-house, rich model, tactical DDD, highest test coverage** | your best engineers |
| **Supporting** | necessary and specific to you, but not a differentiator | "we need it, but nobody chooses us because of it" | build simply — **CRUD/transaction scripts are fine**, vertical slices, no ceremony | anyone; a good place for juniors |
| **Generic** | a solved problem, identical for every company | "can I buy this?" | **buy or use a library**, wrap in an ACL | nobody, ideally |

```text
                 high complexity
                       │
        SUPPORTING     │      CORE            <- invest here: rich domain model,
     (simplify, or     │  (build, protect,       aggregates, invariants, deep
      buy if you can)  │   iterate hardest)      collaboration with experts
                       │
   ────────────────────┼────────────────────  differentiation ──►
                       │
        GENERIC        │      (rare)
      (buy it —        │   simple but
    auth, email,       │   differentiating:
    payments, PDF)     │   just build it fast
                       │
                  low complexity
```

**Q: So when would you NOT use DDD?** *(a trap — "always" is the wrong answer)*

A: **DDD's best return is telling you where *not* to spend effort.** You don't put an aggregate, a repository, domain events and a ubiquitous language around a table of country codes. Skip tactical DDD when:

- The subdomain is **generic** — buy it. Writing your own auth or payment engine is how teams lose a year.
- The subdomain is **supporting and simple** — an admin CRUD screen is a CRUD screen. Forcing a rich model on it is *ceremony without invariants*, and the reviewer will call it over-engineering.
- **There are no real invariants** — if every rule is "field is required", that's validation, not a domain model. See [[17-Architecture-Defense#DDD tactical patterns\|anemic vs rich as a judgement call]].
- **The domain is not understood yet and nobody will talk to you.** DDD without access to domain experts is just extra classes — you'll encode your own guesses in a very expensive way.
- **It's a short-lived or throwaway system.** DDD pays back over years of change.

> [!warning] The trap everyone falls into
> **Every team believes their whole system is core.** It isn't. In most products the core is *one or two* subdomains, and half the codebase is generic work someone rebuilt. Being able to say *"this part is core so it gets the rich model; that part is supporting so it's plain CRUD and I'm fine with that"* is the single most senior-sounding thing in this whole topic — it shows you optimise **effort**, not elegance.

**Distillation — the artefact to mention:** a **Core Domain Chart** (one page: each subdomain, its type, and its build/buy decision) plus a one-paragraph **domain vision statement** for the core. Cheap to produce, and it's what makes the classification a *shared* decision rather than your private opinion.

---

## Ubiquitous Language

**Q: What is Ubiquitous Language?**

A: Common language shared by developers and domain experts. Used in code, conversations, and documentation. Reduces translation errors. Model directly reflects business terminology.

```csharp
// BAD: Technical terms
public class DataRecord
{
    public int RecordId { get; set; }
    public string Field1 { get; set; }
    public decimal Field2 { get; set; }
}

// GOOD: Business terms (Ubiquitous Language)
public class Order
{
    public int OrderId { get; set; }
    public Customer Customer { get; set; }
    public decimal TotalAmount { get; set; }
    public OrderStatus Status { get; set; }
}
```

### Making it real (the senior half)

**Q: The language is "ubiquitous" — across the whole company?**

A: **No — and this is the most common misunderstanding.** A ubiquitous language is ubiquitous **within one bounded context**, not across the organisation. Trying to make one glossary span the whole company produces the worst possible outcome: a committee-designed `Customer` that satisfies nobody. **Each context gets its own dialect, and the context map records the translation.**

```text
"Policy"   in Underwriting = a risk assessment with terms and conditions
"Policy"   in Billing      = a schedule of premiums to collect
"Policy"   in Claims       = the coverage rules to evaluate against
-> three models, three contexts, three languages. Not one shared "Policy" class.
```

**Q: How do you actually build one?** Concrete practices, not slogans:

- **Take the business's words verbatim** — including awkward ones. If the business says *"a booking is **held**, then **confirmed**, then **settled**"*, then the method is `Confirm()`, not `UpdateStatus(2)`. If the code and the conversation use different words, **the code is wrong**, not the business.
- **The language lives in the code**, not in a wiki. Class names, method names, event names, folder names, test names. A glossary that no code enforces rots in a month.
- **Rename ruthlessly when the business corrects you.** A rename that touches 40 files is a *cheap* fix; a mistranslated concept lives forever. This is the moment where most teams give up on ubiquitous language.
- **Watch for the smells** that mean you don't have one yet: developers saying "what the business calls X, we call Y"; a mapping layer whose only job is renaming fields; names like `Manager`, `Processor`, `Handler`, `Info`, `Data`; a business person unable to read your test names.
- **Tests are the best glossary you'll get** — `Should_reject_cancellation_when_booking_is_already_settled` is a sentence a domain expert can confirm or deny.

> [!tip] The answer that lands
> *"Ubiquitous language isn't naming conventions — it's a **feedback loop**. When I can't express a business rule cleanly in the model's language, that's a signal the model is wrong, not that I need a better variable name. Twice on my last project a naming argument turned out to be two different concepts wearing one word, and splitting them removed a pile of conditional logic."*

---

## Bounded Context

**Q: What is a Bounded Context?**

A: Explicit boundary within which domain model applies. Different contexts can have different models for same concept. Reduces complexity. Enables team autonomy.

```csharp
// Sales Context
namespace Sales
{
    public class Customer
    {
        public int CustomerId { get; set; }
        public string Name { get; set; }
        public decimal CreditLimit { get; set; }
        public List<Order> Orders { get; set; }
    }
}

// Shipping Context - Different Customer model
namespace Shipping
{
    public class Customer
    {
        public int CustomerId { get; set; }
        public string Name { get; set; }
        public Address ShippingAddress { get; set; }
        // No CreditLimit - not relevant in shipping context
    }
}

// Support Context - Different Customer model
namespace Support
{
    public class Customer
    {
        public int CustomerId { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public List<Ticket> Tickets { get; set; }
        // Different concerns - support history
    }
}
```

### How big should a bounded context be?

There is no size rule — there are **forces**. Use these, in priority order:

1. **Language.** One context = one consistent meaning per term. The moment a word needs qualifying ("the *billing* customer"), you've found a seam.
2. **Invariants.** Anything that must be transactionally consistent belongs **inside one context** — an aggregate can never span two. If a rule needs data from two contexts to be enforced *atomically*, either your boundary is wrong or that rule must become eventually consistent. Say which one you'd choose and why.
3. **Ownership.** A context should be **ownable by one team** (Conway's law: your architecture will end up mirroring your communication structure, so choose the structure deliberately). Two teams inside one context means constant merge and design conflict.
4. **Rate and reason for change.** Things that change together for the same business reason belong together — the SRP applied at architecture scale.
5. **Lifecycle and actors.** Different phase of the business process, different people using it → likely a different context.

**Symptoms your boundaries are wrong** — the diagnostic list interviewers love:

| Symptom | Likely cause |
|---|---|
| Every feature touches 3+ contexts | boundaries cut *across* business processes instead of along them |
| Chatty synchronous calls between contexts | you split by **entity/table** (`CustomerService`, `ProductService`) instead of by capability → a **distributed monolith** |
| A shared database table written by two contexts | not two contexts — one context pretending |
| A god entity with 40 properties, half null | multiple contexts' models merged into one class |
| Constant cross-team coordination to ship anything | ownership doesn't match the boundary |
| A "common"/"shared" project that only grows | concepts were never assigned a home |

---

## Context Mapping

**Q: What is a context map, and why does it matter more than the boxes?**

A: A context map records **how contexts relate and who has the power** — because the hard part of integration isn't the wire format, it's *whose model wins* and *who has to change when the other side does*. Each relationship is marked **U** (upstream — changes flow *from* here) and **D** (downstream — has to cope).

```text
        ┌───────────────┐          ┌────────────────┐
        │  Reservation  │ U ────► D│    Billing     │   Customer/Supplier
        └───────────────┘          └────────────────┘
               │ U                          │ D
               ▼ D                          ▼
        ┌───────────────┐          ┌────────────────┐
        │   Reporting   │          │  ACL → Stripe  │   Conformist behind an ACL
        │  (Conformist) │          └────────────────┘
        └───────────────┘
```

| Pattern | What it means | Costs you | Choose it when |
|---|---|---|---|
| **Partnership** | two teams succeed or fail together; changes are planned jointly | heavy coordination; doesn't scale past two teams | two contexts must evolve in lockstep, temporarily |
| **Shared Kernel** | a **small** shared model/code subset both own | every change needs both teams to agree — it's a shared liability | a genuinely stable, tiny overlap (IDs, money, a contracts package) |
| **Customer/Supplier** | downstream's needs enter upstream's backlog; upstream accommodates | requires real organisational power balance to work | both teams are internal and management backs it |
| **Conformist** | downstream **adopts upstream's model wholesale**, no translation | their model leaks into yours forever | upstream is big, stable and you have zero influence (a vendor, a platform team) — and the model is *good enough* |
| **Anti-Corruption Layer (ACL)** | downstream **translates** at the boundary to protect its own model | an extra layer and mapping to maintain | integrating with legacy, a vendor, or anything you don't control — **the default for anything external** |
| **Open Host Service (OHS)** | upstream publishes one well-defined protocol for *all* consumers | you must version and support it | many consumers, so bespoke integrations don't scale |
| **Published Language** | a shared, versioned interchange schema (integration events, OpenAPI, an industry standard) | governance and versioning discipline | usually paired with OHS |
| **Separate Ways** | **no integration at all** — duplicate the small bit you need | duplicated data, possible drift | integration costs more than the duplication is worth — legitimate and badly underused |
| **Big Ball of Mud** | a region with no coherent model | nothing, if you're honest about it | mark it on the map, **wrap it in an ACL**, and never model inside it |

**The Anti-Corruption Layer in code** — its job is that *no foreign type ever crosses the boundary*:

```csharp
// The domain speaks only its own language...
public interface IPaymentGateway                      // port, owned by MY context
{
    Task<Result<PaymentReceipt>> ChargeAsync(Money amount, PaymentMethodId method, CancellationToken ct);
}

// ...the ACL translates, and absorbs the vendor's model, errors and vocabulary
public class StripePaymentGateway(IStripeClient stripe) : IPaymentGateway   // adapter
{
    public async Task<Result<PaymentReceipt>> ChargeAsync(Money amount, PaymentMethodId method, CancellationToken ct)
    {
        try
        {
            var intent = await stripe.PaymentIntents.CreateAsync(new PaymentIntentCreateOptions
            {
                Amount   = (long)(amount.Value * 100),      // their unit, not mine
                Currency = amount.Currency.ToLowerInvariant(),
                PaymentMethod = method.Value
            }, cancellationToken: ct);

            return new PaymentReceipt(new ReceiptId(intent.Id), amount);   // MY types come back out
        }
        catch (StripeException ex) when (ex.StripeError.Type == "card_error")
        {
            return Result.Failure<PaymentReceipt>(PaymentErrors.Declined(ex.StripeError.Code));  // MY errors
        }
    }
}
```

**What makes this an ACL and not "a mapper":** `Stripe.PaymentIntent`, `StripeException` and the word "intent" **never appear outside this class**. If the vendor is replaced, one file changes. If `Stripe.Customer` were allowed into your handlers, you'd be a Conformist and wouldn't know it.

> [!tip] The senior line
> "Every integration is a **relationship with a power dynamic**, not a pipe. Before I pick a protocol I ask: *can I influence their model, or do I have to absorb it?* That answer picks the pattern — ACL if I need to stay clean, Conformist if their model is fine and I have no leverage, Separate Ways if the integration costs more than the duplication."

---

## Finding the boundaries — EventStorming

**Q: Concretely, how do you *discover* contexts? Where do the boxes come from?**

A: Not from the database schema and not from the org chart. From the **business process**, mapped with domain experts in the room. **EventStorming** is the fastest technique and the one to name.

**How it runs** (a wall of paper, sticky notes, no chairs, no laptops):

```text
① Chaotic exploration — everyone writes DOMAIN EVENTS (orange), past tense, and slaps them up
      "Booking Requested"  "Payment Authorised"  "Seat Held"  "Booking Confirmed"  "Refund Issued"

② Enforce the timeline — order them left to right, argue, discover the real process

③ Add the rest:
      🟦 Command  (what caused it)         "Confirm Booking"
      🟨 Aggregate (what decides)          Booking
      🟪 Policy   ("whenever X, then Y")   "whenever Payment Authorised, Confirm Booking"
      🟩 Read model (what someone looks at to decide)
      🌸 External system                   Stripe, the airline GDS
      🟥 HOTSPOT  — disagreement, unknown, "it depends"  <- the most valuable stickies on the wall

④ Draw candidate boundaries around clusters
```

**Where the seams actually appear — the tells:**

- **The language changes.** The same thing stops being called a *Booking* and starts being called a *Shipment* or an *Invoice Line*. That word change is a boundary, almost every time.
- **Pivotal events** — a change of business phase (`Booking Confirmed`, `Payment Captured`, `Order Shipped`). The process visibly hands off; that handoff is a seam.
- **Coupling density** — events that reference each other constantly belong together; a thin link between two clusters is a boundary.
- **Actors change** — a different department or role takes over.
- **Hotspots cluster** — red stickies pile up exactly where two mental models collide.

**Three levels of the workshop** (name these to show you know it's not one activity): **Big Picture** (whole business, find subdomains and contexts) → **Process Modelling** (one process end-to-end) → **Software Design** (aggregates, commands, policies — this is where tactical DDD starts).

**Alternatives worth naming:** *Domain Storytelling* (draw actors and work objects as a narrated story — gentler with non-technical people) · *Business Capability Mapping* (top-down, good for the core/supporting/generic classification) · *Wardley Mapping* (evolution — sharpens buy-vs-build).

**Wrong ways to split, and what each produces:**

| Split by… | You get |
|---|---|
| **entity / table** (`CustomerService`, `ProductService`) | a **distributed monolith** — every use case is a chatty multi-service dance |
| **technical layer** (`ApiService`, `DataService`) | layers over a network; latency with none of the autonomy |
| **CRUD verbs** | no model at all; contexts that can't enforce a single rule |
| **today's org chart, uncritically** | a structure that's wrong the moment someone reorganises (though Conway's law means you must *account* for teams — just deliberately, via Team Topologies, not accidentally) |

> [!warning] If you've never run one, don't fake it
> Say what's true: *"I haven't facilitated a full EventStorm; I've mapped our process this way on a whiteboard with the ops lead, and the pivotal-event heuristic is what we used to split X from Y."* Interviewers can tell instantly, and an honest smaller claim scores far better than a rehearsed workshop you've never run.

---

## Bounded context ≠ microservice

**Q: Is a bounded context a microservice?**

A: **No.** A bounded context is a **model/language boundary** (logical). A microservice is a **deployment and runtime boundary** (physical). They're often aligned, but conflating them is how teams end up distributed for no benefit.

| | Bounded context | Microservice |
|---|---|---|
| Boundary of | a model and its language | a deployable process |
| Enforced by | discipline, module structure, compiler | the network |
| Cost of getting it wrong | refactor — hours to days | **distributed monolith** — months |
| Cost of changing it later | cheap if modules are enforced | expensive: contracts, data, deploys |

**The relationship:** one context **may** become one service, or several (splitting one context's read side out for scale is fine). Several contexts **may** live in one deployable — that's a **[[19-Modular-Monolith|modular monolith]]**, and it's the correct default. For how it compares to every other option and how you migrate between them, see [[20-Choosing-An-Architecture|Choosing an Architecture]].

**Say this:** *"I model contexts first and deploy them as modules in one process. A module boundary costs a project reference and an `internal` keyword; a service boundary costs a network hop, a contract, a deployment pipeline and a distributed failure mode. I only pay the second price when there's a driver for it."*

**Real drivers to split a context into its own service** — you must be able to name at least one:
- **Independent scaling** — one context's load profile is genuinely different (search, media processing).
- **Independent deploy cadence** — one part changes daily, another quarterly, and they block each other.
- **Team autonomy at scale** — several teams contending in one deployable.
- **Different availability, compliance or data-residency requirements** — payments/PII isolated for audit.
- **Different technology** — that part genuinely needs Python/ML or a different datastore.

"Microservices are modern" is not a driver, and saying so out loud scores points.

**Enforcing context boundaries inside a monolith** (the practical bit — this is what makes the later split cheap):

```text
src/
  Modules/
    Reservation/        <- own DbContext + own schema; NOTHING else touches its tables
      Domain/ Application/ Infrastructure/ Contracts/   <- only Contracts is public
    Billing/
      ...
    Shared.Kernel/      <- tiny: ids, Money, Result. If it grows, you're doing it wrong.
  Host/                 <- the single deployable
```

- One **`DbContext` and schema per module**; cross-module reads go through a public contract, never a join. (A shared table is the boundary violation that makes the future split impossible.)
- Public surface is a **`Contracts` folder only**; everything else `internal`. Enforce with an architecture test (NetArchTest / ArchUnitNET) so it fails the build, not the review.
- Cross-module communication in-process via **integration-event contracts** — the same shape you'd send over a broker later, so the split becomes a transport change. See [[11-Module-Communication|Module Communication]] and [[17-Architecture-Defense#Domain events vs integration events|domain vs integration events]].

---

## Designing a system with DDD — the method

**Q: "Walk me through how you'd apply DDD to a new system."** *(This is the strategic question. Have a repeatable method, not an opinion.)*

**Do not start with:** the database schema, the entity list, or the folder structure. Every one of those is a *conclusion*, and starting there is the difference between DDD and CRUD with extra classes.

| # | Step | Output | Time |
|---|---|---|---|
| 1 | **Learn the business** — talk to the people who do the work, watch the current process, read the complaints | notes in *their* words | days, not hours |
| 2 | **Map the process** — EventStorm the flow end to end, past-tense events on a timeline | a wall of events, commands, policies, hotspots | half a day |
| 3 | **Find subdomains** — cluster the process into coherent business capabilities | a subdomain list (problem space) | — |
| 4 | **Classify each: core / supporting / generic** → build, simplify, or buy | **core domain chart** + build-vs-buy decisions | — |
| 5 | **Draw candidate bounded contexts** using the boundary forces (language, invariants, ownership, change rate) | boxes with names in business language | — |
| 6 | **Write the language per context** — a short glossary, including the words that mean different things across contexts | glossary in the repo | — |
| 7 | **Draw the context map** — every relationship with a pattern and U/D direction | the context map | — |
| 8 | **Assign ownership** — one context, one team | ownership table | — |
| 9 | **Only now go tactical — and only in the core**: aggregates, invariants, domain events | the model | weeks |
| 10 | **Validate**: walk 3 real scenarios (including a failure and a refund/cancel) across the map | corrected boundaries | — |

**Step 10 is the one candidates skip** and it's the cheapest bug-finder you have. Walking *"customer cancels after payment but before shipping"* through the map exposes missing policies, ownership gaps, and rules that need two contexts to agree — which is where you decide *eventual consistency + saga* versus *move the boundary*.

**Worked mini-example — a travel booking platform:**

```text
STEP 2-3  Events:  Search Performed · Seat Held · Booking Requested · Payment Authorised
                   Booking Confirmed · Ticket Issued · Booking Cancelled · Refund Issued

STEP 4    Core:        Inventory & Reservation (no double-booking, holds, overbooking rules)
                       Pricing (dynamic, the reason customers pick us)
          Supporting:  Reviews, Content/CMS            -> plain CRUD slices, no aggregates
          Generic:     Payments, Identity, Email, PDF  -> BUY, wrap each in an ACL

STEP 5    Contexts:    Reservation | Pricing | Payment | Ticketing | Reviews | Identity

STEP 6    Language:    "Booking" in Reservation = a held/confirmed seat allocation
                       "Booking" in Ticketing   = an issued travel document
                       -> different meanings => the boundary between them is real

STEP 7    Map:         Reservation ──U/D──► Ticketing        (Customer/Supplier)
                       Reservation ──ACL──► Payment/Stripe   (ACL, we own the port)
                       Reviews     ── Separate Ways ──       (needs only a bookingId)

STEP 9    Tactical:    Reservation.Booking aggregate — invariant: a seat is held once,
                       hold expires in 10 min, cannot cancel after Ticket Issued
                       (Reviews gets NO aggregate — it's a table and a form)

STEP 10   Scenario:    "cancel after payment, before ticketing"
                       -> spans Reservation + Payment + Ticketing
                       -> cannot be one transaction => SAGA with compensations
                       -> see the booking design in [[16-System-Design|System Design]]
```

> [!tip] Close with this
> *"The output of strategic design isn't a diagram, it's a set of **decisions with owners**: what we build, what we buy, where the seams are, and who owns each. And I expect to be wrong about some boundaries — which is exactly why I keep them as modules in one deployable until a real driver forces a split."*

---

## Strategic design in a legacy system

**Q: You're not greenfield. The system is a ball of mud. Now what?** *(the realistic version — and far more likely to be your actual job)*

**You don't rewrite it.** You carve it, and DDD's strategic tools are what make carving safe:

1. **Map what exists first.** Draw the context map of the mud — including the parts you dislike. You cannot carve what you haven't mapped, and the map usually reveals the seam is not where people assume.
2. **Pick the first slice by pain × value**, not by architectural beauty. Usually the **core** subdomain (where change is constant) or the worst bottleneck. Never start with the hardest, most entangled part — you need a win that survives management's patience.
3. **Strangler Fig** — put a façade in front, route one capability at a time to the new context, and let the old system shrink until it's deletable. The point is *incremental, always-shippable*, with the old path intact as a fallback.
4. **ACL at every seam** with the legacy — so the mud's model never contaminates the new one. Without this, you've just copied the ball of mud into a new namespace, which is the most common failed "rewrite".
5. **Bubble context** — when you need to model cleanly *next to* something you can't change: a small pristine context with an ACL wrapping the legacy, giving the new work room to breathe.
6. **Data is the hard part, not code.** A shared table read by six modules is the real boundary violation. Sequence it: duplicate/sync the data, move writes, then move reads, then break the table apart.

**Techniques to name:** *branch by abstraction* (an interface both implementations sit behind while you migrate) · *event interception* (publish events from the legacy so new contexts can react without the legacy knowing) · *asset capture* (the new context takes ownership of a data set, becoming its source of truth).

**And say the honest thing:** *"The strangler is only finished when the old path is **deleted**. A half-migrated system with two sources of truth is worse than either endpoint, so I'd rather migrate one capability completely than five capabilities halfway."*

---

# Part 2 — Tactical Design

## Building Blocks

### Entities

**Q: What is an Entity in DDD?**

A: Object with unique identity that persists over time. Defined by ID, not attributes. Mutable. Tracked throughout lifecycle.

```csharp
public class Order
{
    public int OrderId { get; private set; }  // Identity
    public DateTime OrderDate { get; private set; }
    public OrderStatus Status { get; private set; }
    
    private readonly List<OrderLine> _orderLines = new();
    public IReadOnlyCollection<OrderLine> OrderLines => _orderLines.AsReadOnly();
    
    // Constructor
    private Order() { }
    
    public static Order Create(Customer customer)
    {
        return new Order
        {
            OrderDate = DateTime.UtcNow,
            Status = OrderStatus.Pending
        };
    }
    
    // Business logic
    public void AddOrderLine(Product product, int quantity)
    {
        if (Status != OrderStatus.Pending)
            throw new DomainException("Cannot modify non-pending order");
        
        var orderLine = OrderLine.Create(product, quantity);
        _orderLines.Add(orderLine);
    }
    
    public void Submit()
    {
        if (!_orderLines.Any())
            throw new DomainException("Cannot submit empty order");
        
        Status = OrderStatus.Submitted;
        AddDomainEvent(new OrderSubmittedEvent(this));
    }
}

// Two orders with same data but different IDs are different entities
var order1 = new Order { OrderId = 1, TotalAmount = 100 };
var order2 = new Order { OrderId = 2, TotalAmount = 100 };
// order1 != order2 (different identity)
```

---

### Value Objects

**Q: What is a Value Object?**

A: Object without identity. Defined by attributes. Immutable. Equality based on value. Can be freely replaced.

```csharp
public class Money : ValueObject
{
    public decimal Amount { get; private set; }
    public string Currency { get; private set; }
    
    private Money() { }
    
    public static Money Create(decimal amount, string currency)
    {
        if (amount < 0)
            throw new DomainException("Amount cannot be negative");
        
        if (string.IsNullOrWhiteSpace(currency))
            throw new DomainException("Currency is required");
        
        return new Money { Amount = amount, Currency = currency };
    }
    
    // Value objects are immutable - return new instance
    public Money Add(Money other)
    {
        if (Currency != other.Currency)
            throw new DomainException("Cannot add different currencies");
        
        return Create(Amount + other.Amount, Currency);
    }
    
    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Amount;
        yield return Currency;
    }
}

// Usage
var price1 = Money.Create(100, "USD");
var price2 = Money.Create(100, "USD");
// price1 == price2 (same value)

var price3 = price1.Add(price2);  // Returns new Money instance
```

**More Value Objects:**
```csharp
public class Address : ValueObject
{
    public string Street { get; private set; }
    public string City { get; private set; }
    public string ZipCode { get; private set; }
    public string Country { get; private set; }
    
    public static Address Create(string street, string city, string zipCode, string country)
    {
        // Validation
        return new Address 
        { 
            Street = street, 
            City = city, 
            ZipCode = zipCode, 
            Country = country 
        };
    }
    
    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Street;
        yield return City;
        yield return ZipCode;
        yield return Country;
    }
}

public class EmailAddress : ValueObject
{
    public string Value { get; private set; }
    
    public static EmailAddress Create(string email)
    {
        if (string.IsNullOrWhiteSpace(email))
            throw new DomainException("Email cannot be empty");
        
        if (!email.Contains("@"))
            throw new DomainException("Invalid email format");
        
        return new EmailAddress { Value = email.ToLower() };
    }
    
    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Value;
    }
}
```

---

### Aggregates & Aggregate Root

**Q: What is an Aggregate?**

A: Cluster of domain objects (entities and value objects) treated as single unit. Ensures consistency. Has clear boundary. Aggregate Root is entry point.

**Q: What is Aggregate Root?**

A: Entity that serves as entry point to aggregate. Only object external code can reference. Enforces invariants for entire aggregate.

```csharp
// Aggregate Root
public class Order  // Aggregate Root
{
    public int OrderId { get; private set; }
    public Customer Customer { get; private set; }
    public OrderStatus Status { get; private set; }
    
    // Internal entities - only accessible through root
    private readonly List<OrderLine> _orderLines = new();
    public IReadOnlyCollection<OrderLine> OrderLines => _orderLines.AsReadOnly();
    
    // Value object
    public Money TotalAmount => Money.Create(
        _orderLines.Sum(ol => ol.Price.Amount * ol.Quantity), 
        "USD"
    );
    
    // Only way to modify aggregate
    public void AddOrderLine(Product product, int quantity)
    {
        // Enforce invariants
        if (Status != OrderStatus.Pending)
            throw new DomainException("Cannot modify submitted order");
        
        if (quantity <= 0)
            throw new DomainException("Quantity must be positive");
        
        var orderLine = OrderLine.Create(product, quantity);
        _orderLines.Add(orderLine);
        
        // Maintain consistency - check business rules
        if (TotalAmount.Amount > 10000)
            throw new DomainException("Order exceeds maximum amount");
    }
    
    public void RemoveOrderLine(int orderLineId)
    {
        if (Status != OrderStatus.Pending)
            throw new DomainException("Cannot modify submitted order");
        
        var orderLine = _orderLines.FirstOrDefault(ol => ol.Id == orderLineId);
        if (orderLine != null)
        {
            _orderLines.Remove(orderLine);
        }
    }
    
    public void Submit()
    {
        if (!_orderLines.Any())
            throw new DomainException("Cannot submit empty order");
        
        Status = OrderStatus.Submitted;
        AddDomainEvent(new OrderSubmittedEvent(this));
    }
}

// Entity within aggregate - only accessible through Order
public class OrderLine
{
    public int Id { get; private set; }
    public Product Product { get; private set; }
    public int Quantity { get; private set; }
    public Money Price { get; private set; }
    
    private OrderLine() { }
    
    internal static OrderLine Create(Product product, int quantity)
    {
        return new OrderLine
        {
            Product = product,
            Quantity = quantity,
            Price = product.Price
        };
    }
}

// Usage - Always through Aggregate Root
var order = Order.Create(customer);
order.AddOrderLine(product, 5);  // Through root
order.RemoveOrderLine(1);        // Through root
order.Submit();                  // Through root

// NOT ALLOWED - cannot modify OrderLine directly
// var orderLine = order.OrderLines.First();
// orderLine.Quantity = 10;  // Readonly collection prevents this
```

**Aggregate Rules:**
1. Reference other aggregates by ID only
2. One transaction per aggregate
3. Small aggregates (2-3 entities max)
4. Enforce invariants within boundary
5. Only aggregate root has repository

```csharp
// Good: Reference by ID
public class Order
{
    public int CustomerId { get; private set; }  // Reference by ID
    // Not: public Customer Customer { get; set; }
}

// Load related aggregate separately
var order = await _orderRepository.GetByIdAsync(orderId);
var customer = await _customerRepository.GetByIdAsync(order.CustomerId);
```

---

### Domain Events

**Q: What are Domain Events?**

A: Represent something that happened in the domain. Captures business events. Enables decoupling. Supports eventual consistency.

```csharp
// Base domain event
public abstract class DomainEvent
{
    public DateTime OccurredOn { get; protected set; }
    
    protected DomainEvent()
    {
        OccurredOn = DateTime.UtcNow;
    }
}

// Specific domain events
public class OrderSubmittedEvent : DomainEvent
{
    public int OrderId { get; }
    public int CustomerId { get; }
    public decimal TotalAmount { get; }
    
    public OrderSubmittedEvent(Order order)
    {
        OrderId = order.OrderId;
        CustomerId = order.Customer.Id;
        TotalAmount = order.TotalAmount.Amount;
    }
}

public class PaymentProcessedEvent : DomainEvent
{
    public int OrderId { get; }
    public decimal Amount { get; }
    
    public PaymentProcessedEvent(int orderId, decimal amount)
    {
        OrderId = orderId;
        Amount = amount;
    }
}

// Entity with domain events
public abstract class Entity
{
    private readonly List<DomainEvent> _domainEvents = new();
    public IReadOnlyCollection<DomainEvent> DomainEvents => _domainEvents.AsReadOnly();
    
    protected void AddDomainEvent(DomainEvent domainEvent)
    {
        _domainEvents.Add(domainEvent);
    }
    
    public void ClearDomainEvents()
    {
        _domainEvents.Clear();
    }
}

// Usage in aggregate
public class Order : Entity
{
    public void Submit()
    {
        // Business logic
        Status = OrderStatus.Submitted;
        
        // Raise domain event
        AddDomainEvent(new OrderSubmittedEvent(this));
    }
}

// Domain event handler
public class OrderSubmittedEventHandler : INotificationHandler<OrderSubmittedEvent>
{
    private readonly IEmailService _emailService;
    private readonly IInventoryService _inventoryService;
    
    public async Task Handle(OrderSubmittedEvent notification, CancellationToken cancellationToken)
    {
        // Send confirmation email
        await _emailService.SendOrderConfirmationAsync(notification.OrderId);
        
        // Reserve inventory
        await _inventoryService.ReserveItemsAsync(notification.OrderId);
        
        // Can trigger other processes...
    }
}

// Publishing events after SaveChanges
public override async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
{
    var domainEntities = ChangeTracker.Entries<Entity>()
        .Where(x => x.Entity.DomainEvents.Any())
        .ToList();
    
    var domainEvents = domainEntities
        .SelectMany(x => x.Entity.DomainEvents)
        .ToList();
    
    // Clear events before saving
    domainEntities.ForEach(entity => entity.Entity.ClearDomainEvents());
    
    // Save changes
    var result = await base.SaveChangesAsync(cancellationToken);
    
    // Publish events after successful save
    foreach (var domainEvent in domainEvents)
    {
        await _mediator.Publish(domainEvent, cancellationToken);
    }
    
    return result;
}
```

---

### Repositories

**Q: What is Repository in DDD?**

A: Provides collection-like interface for accessing aggregates. Abstracts persistence. One repository per aggregate root. Returns fully formed aggregates.

```csharp
// Repository interface - in Domain layer
public interface IOrderRepository
{
    Task<Order> GetByIdAsync(int id);
    Task<IEnumerable<Order>> GetByCustomerIdAsync(int customerId);
    Task AddAsync(Order order);
    Task UpdateAsync(Order order);
    Task DeleteAsync(int id);
}

// Repository implementation - in Infrastructure layer
public class OrderRepository : IOrderRepository
{
    private readonly AppDbContext _context;
    
    public OrderRepository(AppDbContext context)
    {
        _context = context;
    }
    
    public async Task<Order> GetByIdAsync(int id)
    {
        // Load entire aggregate
        return await _context.Orders
            .Include(o => o.OrderLines)
            .ThenInclude(ol => ol.Product)
            .FirstOrDefaultAsync(o => o.OrderId == id);
    }
    
    public async Task<IEnumerable<Order>> GetByCustomerIdAsync(int customerId)
    {
        return await _context.Orders
            .Include(o => o.OrderLines)
            .Where(o => o.CustomerId == customerId)
            .ToListAsync();
    }
    
    public async Task AddAsync(Order order)
    {
        await _context.Orders.AddAsync(order);
    }
    
    public Task UpdateAsync(Order order)
    {
        _context.Orders.Update(order);
        return Task.CompletedTask;
    }
    
    public async Task DeleteAsync(int id)
    {
        var order = await GetByIdAsync(id);
        if (order != null)
        {
            _context.Orders.Remove(order);
        }
    }
}

// Usage
public class OrderService
{
    private readonly IOrderRepository _orderRepository;
    private readonly IUnitOfWork _unitOfWork;
    
    public async Task ProcessOrderAsync(int orderId)
    {
        var order = await _orderRepository.GetByIdAsync(orderId);
        
        order.Submit();  // Business logic
        
        await _orderRepository.UpdateAsync(order);
        await _unitOfWork.SaveChangesAsync();
    }
}
```

---

### Domain Services

**Q: What is a Domain Service?**

A: Encapsulates domain logic that doesn't naturally fit in entity or value object. Stateless. Operates on multiple aggregates. Contains complex business logic.

```csharp
public interface IOrderPricingService
{
    Money CalculateTotalPrice(Order order, Customer customer);
}

public class OrderPricingService : IOrderPricingService
{
    public Money CalculateTotalPrice(Order order, Customer customer)
    {
        decimal subtotal = order.OrderLines.Sum(ol => 
            ol.Product.Price.Amount * ol.Quantity);
        
        // Apply customer discount
        decimal discount = customer.IsVip ? 0.10m : 0;
        subtotal = subtotal * (1 - discount);
        
        // Apply tax
        decimal tax = subtotal * 0.08m;
        
        // Add shipping
        decimal shipping = subtotal > 100 ? 0 : 10;
        
        decimal total = subtotal + tax + shipping;
        
        return Money.Create(total, "USD");
    }
}

// Usage
public class Order
{
    public Money CalculateTotal(IOrderPricingService pricingService, Customer customer)
    {
        return pricingService.CalculateTotalPrice(this, customer);
    }
}
```

**Another Example:**
```csharp
public interface ITransferService
{
    Task TransferAsync(Account fromAccount, Account toAccount, Money amount);
}

public class TransferService : ITransferService
{
    public async Task TransferAsync(Account fromAccount, Account toAccount, Money amount)
    {
        // Domain logic involving multiple aggregates
        if (fromAccount.Currency != toAccount.Currency)
            throw new DomainException("Currency mismatch");
        
        fromAccount.Withdraw(amount);
        toAccount.Deposit(amount);
        
        // Both changes saved together via Unit of Work
    }
}
```

---

## DDD Best Practices

1. **Always use factory methods for creation**
```csharp
public static Order Create(Customer customer) { /* ... */ }
```

2. **Make constructors private**
```csharp
private Order() { }
```

3. **Use private setters**
```csharp
public int OrderId { get; private set; }
```

4. **Validate in domain objects**
```csharp
if (amount <= 0) throw new DomainException("...");
```

5. **Encapsulate collections**
```csharp
private readonly List<OrderLine> _orderLines = new();
public IReadOnlyCollection<OrderLine> OrderLines => _orderLines.AsReadOnly();
```

6. **Use value objects for concepts without identity**
```csharp
public Money Price { get; private set; }
```

7. **Keep aggregates small**
8. **Reference other aggregates by ID**
9. **Use domain events for cross-aggregate communication**
10. **Put business logic in domain layer**

---

## Common Mistakes

❌ **Anemic Domain Model** - All logic in services
```csharp
// BAD
public class Order
{
    public int OrderId { get; set; }
    public decimal Total { get; set; }
}

public class OrderService
{
    public void SubmitOrder(Order order)
    {
        // All logic in service
    }
}
```

✅ **Rich Domain Model** - Logic in entities
```csharp
// GOOD
public class Order
{
    public int OrderId { get; private set; }
    
    public void Submit()
    {
        // Business logic here
    }
}
```

❌ **Direct aggregate modification**
```csharp
order.OrderLines.Add(new OrderLine());  // BAD
```

✅ **Through aggregate root**
```csharp
order.AddOrderLine(product, quantity);  // GOOD
```

---

# Part 3 — Strategic Design Drill

Say each in **20 seconds or less**. These are the questions that separate "I've used DDD" from "I've made DDD decisions".

| # | Probe | Your answer, compressed |
|---|---|---|
| 1 | Domain vs subdomain vs bounded context? | Domain and subdomains are the **problem space** — they exist already. A bounded context is the **solution space** — I draw it. Subdomains are found; contexts are designed. |
| 2 | How do you decide what to build vs buy? | Classify each subdomain: **core** (differentiator → build, rich model, best people), **supporting** (needed, not special → simple CRUD), **generic** (solved → buy and wrap in an ACL). |
| 3 | When would you *not* use DDD? | Generic or simple supporting subdomains, anything with no real invariants, no access to domain experts, or a throwaway system. Tactical DDD there is ceremony. |
| 4 | Is the ubiquitous language company-wide? | No — **per bounded context**. One company-wide glossary produces a committee `Customer` nobody can use. |
| 5 | How do you know two things are different contexts? | The same word means different things. `Policy` in Underwriting ≠ in Billing ≠ in Claims. |
| 6 | How big should a context be? | Sized by forces, not lines: one language, invariants inside it, **one team owning it**, things that change together for the same reason. |
| 7 | How do you find the boundaries? | EventStorm the process with experts; boundaries show up where the **language changes**, at **pivotal events**, and where coupling density drops. Not from the schema or the org chart. |
| 8 | What's the worst way to split? | By **entity or table** (`CustomerService`, `ProductService`) — every use case becomes a chatty multi-service dance. A distributed monolith. |
| 9 | What is a context map for? | Recording **who has the power** in each relationship — upstream/downstream — because the hard part is whose model wins, not the wire format. |
| 10 | Name the integration patterns. | Partnership · Shared Kernel · Customer/Supplier · Conformist · **ACL** · Open Host Service · Published Language · Separate Ways · Big Ball of Mud. |
| 11 | When Conformist over ACL? | When upstream is big, stable, I have zero influence, and their model is good enough. ACL when I must protect my model — the default for anything external. |
| 12 | What makes an ACL more than a mapper? | **No foreign type crosses the boundary** — their DTOs, exceptions and vocabulary stop at the adapter. Replace the vendor, change one file. |
| 13 | Is a bounded context a microservice? | No. Context = model boundary (logical). Service = deployment boundary (physical). Default to **modules in one deployable**; split only for a named driver. |
| 14 | Name a real driver to split. | Independent scaling, independent deploy cadence, team autonomy at scale, different compliance/availability, genuinely different technology. |
| 15 | How do you keep a future split cheap? | One `DbContext`/schema per module, public `Contracts` only (enforced by an architecture test), cross-module calls through integration-event contracts. |
| 16 | Two contexts must agree on a rule — now what? | It can't be one transaction. Either the boundary is wrong, or the rule is **eventually consistent** → saga with compensations. Say which you'd pick and why. |
| 17 | Where do you start in a legacy ball of mud? | Map it first, pick by **pain × value**, strangler fig one capability at a time, ACL at every seam, and finish — a half-migration with two sources of truth is worse than either end. |
| 18 | What's the actual output of strategic design? | Not a diagram — **decisions with owners**: what we build, what we buy, where the seams are, who owns each. And boundaries I expect to move. |

---
