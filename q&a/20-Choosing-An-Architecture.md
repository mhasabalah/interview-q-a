---
title: Choosing an Architecture
aliases: [Choosing an Architecture, Architecture Comparison, Architecture Decision, Migration Paths]
tags: [architecture, comparison, migration, decision, interview]
order: 20
---

# Choosing an Architecture — Comparison, Decision & Migration

> [!info]+ Related Notes
> [[19-Modular-Monolith|Modular Monolith]] · [[17-Architecture-Defense|Architecture Defense]] · [[08-Clean-Architecture|Clean Architecture]] · [[09-Onion-Architecture|Onion Architecture]] · [[07-Domain-Driven-Design|Domain-Driven Design]] · [[16-System-Design|System Design]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]]

> [!danger]+ The framing that wins this round
> Most candidates answer "Clean Architecture or microservices?" as if it were one question. **It's two questions on two independent axes**, and saying so immediately separates you:
>
> | Axis | Question | Options |
> |---|---|---|
> | **A. Internal structure** | how is the *code inside one deployable* organised? | layered · hexagonal · onion · clean · vertical slice |
> | **B. Deployment topology** | how many *processes*, and where are the network boundaries? | single monolith · modular monolith · microservices · serverless |
>
> You pick **one from each**. "Clean Architecture vs microservices" is a category error — a microservice has an internal structure too, and it's usually one of the ones on axis A. The real sentence is: *"vertical slices inside a modular monolith, with a rich domain in the core module"* — that's an answer on both axes, and it sounds like someone who has actually decided.

---

# Axis A — Internal structure

**Q: Compare the ways to organise code inside one deployable.**

| | **Layered / N-tier** | **Hexagonal (Ports & Adapters)** | **Onion** | **Clean** | **Vertical Slice** |
|---|---|---|---|---|---|
| Core idea | stack: UI → business → data | domain in the middle, **ports** out, **adapters** plugged in | concentric rings, dependencies point **inward** | onion + explicit use-case layer and boundary interfaces | organise by **feature**, not by layer |
| Dependency rule | downward (business → data) | inward via interfaces | **inward only** | **inward only** | slice depends on domain |
| Unit of change | a layer | an adapter | a ring | a use case | **a feature folder** |
| Optimises for | familiarity, simple CRUD | swappable I/O, testability | domain independence | explicit use cases, big teams | **change locality, speed** |
| Costs you | domain depends on data; coupling hides in "services" | more interfaces than juniors expect | ceremony; indirection | most ceremony; layer tax on every change | duplication; shared logic needs a deliberate home |
| Fails as | a god `OrderService` and an anemic model | over-abstracted ports nobody swaps | same as clean, quieter | "6 files to add a field" | transaction scripts in folders |
| Pick it for | genuine CRUD, small apps, supporting subdomains | anything with lots of external I/O | rich domains | large teams needing a mandated shape | **most feature work** |

> [!tip] The thing to say about Hexagonal / Onion / Clean
> **They are the same idea at three resolutions.** Hexagonal (2005) says *domain in the middle, everything external is an adapter behind a port*. Onion (2008) draws it as rings. Clean (2012) adds named layers and an explicit use-case ring. If someone asks you to compare them and you say "they're the same principle — protect the domain, invert the dependencies, differ only in how prescriptive the diagram is" — that's the correct and confident answer. **The principle is Dependency Inversion applied at architecture scale.**

**And the pairing that actually works in practice:** vertical slices for the application layer + a shared, dependency-free domain project underneath. Slices own orchestration and reads; the domain owns invariants. You keep the Dependency Rule and drop the layer-per-noun ceremony — see [[17-Architecture-Defense#Vertical Slice vs Clean/Onion|the defense]].

---

# Axis B — Deployment topology

| | **Single monolith** | **Modular monolith** | **Microservices** | **Serverless / FaaS** |
|---|---|---|---|---|
| Deployables | 1 | **1** | N | N functions |
| Boundaries enforced by | nothing | **compiler + arch tests** | the network | the platform |
| Data | one schema, shared | **schema per module** | database per service | usually managed stores |
| Team fit | 1 team | **1–5 teams** | many autonomous teams | small pieces, event-driven work |
| Ops burden | ★ | ★★ | ★★★★★ | ★★★ (different: platform + cold starts + limits) |
| Independent deploy | ✗ | ✗ | **✓** | ✓ |
| Independent scale | ✗ | ✗ | **✓** | **✓ (to zero)** |
| Transactions | easy, real ACID | easy inside a module | **sagas + eventual consistency** | sagas |
| Debugging | a stack trace | a stack trace | distributed tracing, correlation IDs | tracing + platform logs |
| Latency between parts | nanoseconds | nanoseconds | **milliseconds + partial failure** | ms + cold start |
| Cost of a wrong boundary | refactor (hours) | **refactor (days)** | **migration (months)** | migration |
| Fails as | big ball of mud | modules with a shared join | **distributed monolith** | a chatty function mesh nobody can trace |

**Event-driven architecture is not on this list on purpose** — it's a **communication style** you overlay on any topology. You can be event-driven inside a modular monolith (in-process integration events) or across services (broker). Saying that shows you understand it's orthogonal.

---

# The forces that actually decide

Not fashion, not résumé-driven development. Rank these, in this order:

1. **How many teams?** *(the strongest force by far)* One team → one deployable, always. Five independent teams blocked by one pipeline → that's a real driver to split. **Microservices are an organisational solution to a team-coordination problem**, not a performance technique. Say that sentence.
2. **Do you know the boundaries yet?** If no → modular monolith. Discovering a boundary is cheap in-process and brutally expensive across services.
3. **Scale profile.** Does one part have a *genuinely different* load or cost curve (search, media, ML)? That part earns its own deployable. Uniform load → replicate the monolith; it's cheaper and simpler.
4. **Deploy cadence.** Does one part need to ship hourly while another ships quarterly, and do they block each other *today*?
5. **Ops maturity.** No platform team, no tracing, no on-call rota? Microservices will fail — not architecturally, *operationally*. Be honest about this in an interview; it's a maturity signal.
6. **Compliance / isolation.** PCI scope, data residency, an audited boundary — a legitimate, non-negotiable driver.
7. **Domain complexity.** Rich invariants → rich domain model (axis A). Genuine CRUD → don't over-build. This decides axis A, not axis B.

```text
Start
 │
 ├─ Is it genuinely CRUD with no real invariants?
 │      └─ YES → layered or vertical slices, single deployable. Stop. Don't over-build.
 │
 ├─ More than ~1–2 teams, or boundaries still unproven?
 │      └─ YES → MODULAR MONOLITH + vertical slices (+ rich domain in core modules only)
 │
 ├─ Is there a NAMED driver for a specific part?
 │   (different scale profile · independent deploy cadence · team autonomy
 │    · compliance isolation · genuinely different tech)
 │      ├─ NO  → stay. Revisit in 6 months.
 │      └─ YES → extract THAT module only → hybrid (monolith + a few services)
 │
 └─ Do several parts each have their own driver, and can you run the ops?
        └─ YES → microservices for those parts. Most companies never get here, and shouldn't.
```

---

# What a senior actually chooses

**The default, stated plainly:**

> **"Modular monolith, vertical slices, rich domain model only in the core subdomain, one schema per module, wire-shaped contracts between modules from day one."**

Why that specific combination:
- **Modular monolith** — I don't know the boundaries yet, and this is the only architecture where being wrong is *cheap*.
- **Vertical slices** — my unit of change is a feature, not a layer.
- **Rich domain only in the core** — supporting subdomains get plain CRUD; putting aggregates around a lookup table is ceremony without invariants ([[07-Domain-Driven-Design#Core, Supporting and Generic subdomains|core/supporting/generic]]).
- **Schema per module + wire-shaped contracts** — free today, and they are the *entire* cost of a future split.

**What a senior does *not* do:**
- Start with microservices "because we'll need to scale". You'll need to scale *the thing you haven't built yet*, on boundaries you haven't discovered.
- Apply Clean Architecture's full ceremony to a CRUD admin panel.
- Split by entity (`CustomerService`, `ProductService`) — that's a [[07-Domain-Driven-Design#Finding the boundaries — EventStorming|distributed monolith]].
- Choose based on what's in the job ad.

**The honest concession to volunteer:** *"If the org already runs 15 services well, has a platform team and tracing, I'd fit into that — architecture that fights the organisation loses. Conway's law isn't advice, it's a description."*

---

# Start here → then transition

The roadmap, with the **trigger** for each move. This is the answer to *"what should I build first, and how do I get to the next thing?"*

### Stage 0 — MVP · 1–3 devs · boundaries unknown

**Build:** one project, **vertical slices** (folder per feature), one schema, no DDD ceremony, no MediatR unless you already want its pipeline. Rich model **only** where real invariants exist.

**But do these four things now, because they're free and they buy every later option:**
1. **Group folders by business capability**, not by technical type — the future module boundaries.
2. **Don't scatter data access** — one place per capability touches the tables.
3. **Name things in the business's language** ([[07-Domain-Driven-Design#Ubiquitous Language|ubiquitous language]]).
4. **Integration tests over a real database** (Testcontainers) — they're what makes every later refactor safe.

> **Design for extraction; don't build for it.** Seams cost nothing at the start. Distribution costs from day one.

**→ Move on when:** more than ~2 teams, or two capabilities keep breaking each other, or onboarding takes weeks.

### Stage 1 — Product-market fit · 5–20 devs

**Build:** promote the capability folders to real **modules** ([[19-Modular-Monolith|modular monolith]]): own project, own schema, `Contracts` public and the rest `internal`, in-process integration events shaped like broker messages, **architecture tests in CI**. Still one deployable.

**→ Move on when:** a *named driver* appears for a specific module — not before.

### Stage 2 — Hybrid · a driver appears

**Build:** extract **one** module — the one with the driver — following the [[19-Modular-Monolith#Extraction modular monolith → microservice|extraction recipe]]. You now run a monolith plus one or two services. Pay the distributed taxes only for that boundary: outbox, idempotency, retries with jitter, timeouts, tracing.

**This is where most successful companies stop, permanently, and that's a correct outcome — not a failure to finish.**

**→ Move on only when:** several parts each have their own driver **and** you have the platform capability to operate them.

### Stage 3 — Microservices for the parts that earn it

Independent deploy, independent scale, team autonomy — and the full ops bill: service discovery, contract versioning, distributed tracing, saga orchestration, on-call, per-service pipelines. See [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]].

```text
Stage 0            Stage 1                Stage 2                 Stage 3
single project  →  modular monolith   →   monolith + 1-2 services  →  microservices
vertical slices    schema per module      extract on a driver         (only what earns it)
capability folders wire-shaped contracts  pay taxes at that seam
                   arch tests in CI

trigger: teams &   trigger: a NAMED       trigger: several drivers +
         breakage           driver                 ops maturity
```

---

# Migration playbooks

### 1. Layered → Vertical Slice *(cheapest, do it incrementally)*
**Trigger:** every small change touches 6 files across 4 projects.
**How:** don't rewrite. **New features go in slices**; when you touch an old feature, move it into a slice (the Boy Scout rule). Keep the domain project shared.
**Risk:** two styles coexisting for a year — acceptable, and better than a big-bang refactor. Write the rule down so it isn't seen as inconsistency.

### 2. Ball of mud → Modular monolith *(the highest-value migration most teams need)*
**Trigger:** unclear ownership, every release is a coordination event, nobody can change anything safely.
**How:**
1. **Map what exists** — the real dependencies, not the intended ones.
2. Pick **one** capability, by pain × value.
3. Create the module's project + `Contracts`; move code in.
4. **Cut the data last**: give it a schema, then remove cross-schema joins one at a time (replace with a facade call or an event-fed copy).
5. Add the architecture test **the moment** the boundary is clean, so it can't regress.
6. Repeat. Ship continuously; never branch for months.
**Risk:** the joins. Always the joins. Budget most of the time there.

### 3. Modular monolith → Microservices
**Trigger:** a named driver on a specific module.
**How:** the [[19-Modular-Monolith#Extraction modular monolith → microservice|7-step extraction]] — freeze contract → swap transport → split data → deploy → shift traffic → delete old path → pay the distributed taxes.
**Risk:** doing it without a driver; extracting everything at once; leaving a shared database (that's how you land in a distributed monolith).

### 4. Microservices → Modular monolith *(consolidation — a real and respected move)*
**Trigger:** services that always deploy together · more time in YAML and tracing than in features · a "service" per developer · latency and cost dominated by chatter between two services that were never separate concerns.
**How:** merge the services that share a change cadence back into modules of one deployable, **keeping the module boundaries**. You lose deployment independence you weren't using and win back transactions, simple debugging and lower cost.
**Say this if it comes up:** *"Consolidating is not an admission of failure — it's correcting a boundary. There are well-publicised cases of teams collapsing an over-distributed pipeline back into one process and cutting cost dramatically. The lesson isn't 'monoliths won', it's **the boundary was wrong**."*

### 5. Any topology → Event-driven
**Trigger:** side effects multiplying inside request handlers; needing to add consumers without touching producers.
**How:** introduce domain events + the **outbox** *inside* the current topology first. No deployment change required.
**Risk:** losing the ability to reason about the flow — [[18-Distributed-Systems-Reliability#Saga orchestration vs choreography|orchestration vs choreography]] matters once it's more than 3 steps.

---

# Scenario answers *(practise these out loud)*

| They ask | You answer |
|---|---|
| **"3 devs, MVP, 3 months."** | Single deployable, vertical slices, folders by capability, one schema, integration tests on a real DB. No MediatR-for-its-own-sake, no aggregates around CRUD. Boundaries are a *guess* right now, so I keep them cheap to move. |
| **"20 devs, 5 teams, one product."** | Modular monolith with a module per team-owned capability, schema per module, contracts + in-process events, arch tests in CI. Split only where a driver exists. The real problem at this size is **ownership**, not technology. |
| **"Existing 500k-LOC monolith, releases are painful."** | Don't rewrite. Map it, carve one capability by pain × value, strangler fig with an ACL at the seam, cut the data last, lock the boundary with an arch test, repeat. Ship every week. |
| **"We need microservices to scale."** | Ask which part, and what the scale numbers are. Usually the answer is *team* scale, not load — and the fix is modules and ownership. If it really is load, replicate the monolith first: it's an afternoon, and it's often enough. Then extract only the hot part. |
| **"Greenfield, but the CTO says microservices."** | Agree on the destination, disagree on the start: modules first with wire-shaped contracts, extract on drivers. If it's non-negotiable, then boundaries must come from an EventStorm with domain experts — because a wrong boundary now costs months later. |
| **"When would you use serverless?"** | Spiky or infrequent event-driven work — image processing, webhooks, scheduled jobs, glue. Not for a latency-sensitive core with heavy state, where cold starts and execution limits bite. It's a *deployment* choice for a *specific workload*, not a whole-system architecture. |
| **"Clean Architecture or vertical slice?"** | Different axes of the same question. I use slices for the application layer and keep a dependency-free domain project — the Dependency Rule survives, the layer-per-noun ceremony doesn't. |

---

# Traps and red flags

| Trap | The correct instinct |
|---|---|
| "Microservices for scalability" | It's mainly **team** scalability. Load scaling is usually replication + caching. |
| "We'll add boundaries later" | Boundaries are cheap now and expensive later. **Always the reverse of what people assume.** |
| "Clean Architecture everywhere" | Ceremony on a CRUD subdomain is over-engineering; a reviewer will say so. |
| "One service per entity" | Distributed monolith. Split by **capability**, never by table. |
| Choosing to match a job ad / conference talk | Choose against **forces**: teams, boundaries known?, scale profile, cadence, ops maturity, compliance. |
| Shared database between services | The single clearest sign of a distributed monolith. |
| Rewriting instead of strangling | Big-bang rewrites fail publicly. Carve, ship weekly, delete the old path. |
| Never revisiting | Architecture is a *series* of decisions. Record them in ADRs with the trigger for revisiting. |

---

## Rapid-Fire Drill

| # | Probe | Your answer, compressed |
|---|---|---|
| 1 | Clean Architecture or microservices? | Two different axes — internal structure vs deployment topology. You choose one from each. |
| 2 | Hexagonal vs Onion vs Clean? | The same principle at three resolutions: protect the domain, invert the dependencies. They differ in how prescriptive the diagram is. |
| 3 | Your default for a new system? | Modular monolith + vertical slices + rich domain only in the core, schema per module, wire-shaped contracts. |
| 4 | Why not microservices from day one? | You don't know the boundaries yet, and a wrong boundary costs a refactor in-process versus a migration across services. |
| 5 | What really drives microservices? | **Team autonomy** — it's an organisational solution. Then scale profile, deploy cadence, compliance, technology. |
| 6 | When is a single plain monolith right? | One team, genuine CRUD, no real invariants. Don't over-build. |
| 7 | What do you do on day one that costs nothing? | Capability folders, contained data access, business language, integration tests on a real DB. **Design for extraction, don't build for it.** |
| 8 | Biggest migration cost, always? | **The data.** Contracts and transport are cheap if you planned them. |
| 9 | Is consolidating services back a failure? | No — it's correcting a boundary. Losing deployment independence you weren't using is a win. |
| 10 | Where does event-driven fit? | It's a communication style overlaid on any topology — in-process events count. |
| 11 | How do you stop a modular monolith rotting? | Architecture tests in CI. Enforcement, not documentation. |
| 12 | How do you decide, in one sentence? | Count the teams, ask whether the boundaries are proven, look for a named driver — and pick the cheapest thing to be wrong about. |
