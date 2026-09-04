---
title: Observability
aliases: [Observability, OpenTelemetry, Tracing, Metrics, Logging, Monitoring]
tags: [observability, opentelemetry, tracing, metrics, logging, sre, interview]
order: 23
---

# Observability — Interview Q&A

> [!info]+ Related Notes
> [[16-System-Design|System Design]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]] · [[22-Event-Sourcing-And-EDA|Event Sourcing & EDA]] · [[12-RabbitMQ-MassTransit|RabbitMQ & MassTransit]] · [[21-Database-Part-2|Database Part 2]] · [[14-CI-CD|CI/CD]] · [[10-Middlewares|Middlewares]]

> [!danger]+ Why this note exists
> Your CV lists **OpenTelemetry, Prometheus, Grafana, Loki, Serilog, Seq and Application Insights** as a headline skill, and BateCom claims *"instrumented with OpenTelemetry into 3 backends, surfaced in Grafana alongside Serilog in Seq."* That's a build-it-yourself claim, so expect build-it-yourself questions.
>
> The three that actually get asked:
> 1. **"How do you debug a slow request in production?"** → the end-to-end walkthrough, Part 8
> 2. **"How does a trace survive going through RabbitMQ?"** → context propagation, Part 4 — *the discriminator for someone doing event-driven work*
> 3. **"What do you alert on?"** → symptoms and error budgets, not CPU
>
> One sentence to anchor everything: **telemetry is not observability. Observability is being able to answer a question you didn't anticipate, without shipping new code.**

---

# Part 1 — The basics

**Q: Monitoring vs observability?**

| | **Monitoring** | **Observability** |
|---|---|---|
| Answers | *"is the thing I predicted happening?"* | *"why is this specific request behaving like that?"* |
| Built from | dashboards and thresholds you defined in advance | high-cardinality, correlatable telemetry you can slice arbitrarily |
| Handles | **known unknowns** — CPU high, queue deep | **unknown unknowns** — "only Android users on tenant 42 since Tuesday" |
| Fails when | the failure is one you didn't foresee | you never emitted the dimension you now need |

Monitoring is a subset. If the only way to answer a new question is to add a log line and redeploy, you have monitoring, not observability.

**Q: The three pillars — and what each is actually for?**

| | **Logs** | **Metrics** | **Traces** |
|---|---|---|---|
| What it is | discrete events with context | numeric aggregates over time | the causal path of **one** request across services |
| Answers | *what exactly happened here?* | *is the system healthy? is it getting worse?* | *where did the time go? what called what?* |
| Cardinality | very high (any field) | **must be low** | high (per request) |
| Cost at volume | **highest** | lowest | medium (sampled) |
| Retention | days–weeks | months–years (cheap to aggregate) | days |
| Weak at | aggregation, trends | explaining a single request | telling you *why* a span was slow (that's the log) |

**They are not alternatives — they're one investigation.** The workflow that matters: a **metric** tells you something is wrong → a **trace** tells you where → a **log** tells you why. If those three aren't linked by IDs, you have three tools and no answer.

> [!tip] The concept that governs everything: cardinality
> **Cardinality = the number of distinct values a dimension can take.** `http.method` is ~7. `user.id` is millions.
> - In **metrics**, high cardinality is fatal — each label combination is a separate time series, and putting `userId` in a Prometheus label is how you take Prometheus down.
> - In **traces and logs**, high cardinality is the *entire point* — `user.id` on a span is what lets you find the one broken customer.
>
> Knowing which pillar tolerates it — and why — is a genuine senior signal.

---

# Part 2 — Logs

**Q: What's wrong with `_logger.LogInformation($"Order {orderId} placed")`?**

A: The interpolation happens **before** the logger sees it, so you've produced a unique string instead of an event with fields. You can no longer filter by `OrderId`, group by message type, or aggregate — and you pay the formatting cost even when the level is disabled.

```csharp
// ❌ interpolated: one unique string, no structure, always formatted
_logger.LogInformation($"Order {orderId} placed for {customerId} totalling {total}");

// ✅ message template: OrderId/CustomerId/Total become queryable properties in Seq/Loki
_logger.LogInformation("Order {OrderId} placed for {CustomerId} totalling {Total}", orderId, customerId, total);
//    Seq:  OrderId = 'abc-123'
//    and every log for that message shares one template => you can count them as one event type

// Scopes attach context to everything logged inside the block
using (_logger.BeginScope(new Dictionary<string, object> { ["TenantId"] = tenantId, ["OrderId"] = orderId }))
{
    await _handler.HandleAsync(cmd, ct);      // every log inside carries TenantId + OrderId
}

// Source-generated logging — zero allocation, compile-time checked (the modern default for hot paths)
[LoggerMessage(Level = LogLevel.Warning, Message = "Payment declined for {OrderId}: {Reason}")]
public static partial void PaymentDeclined(ILogger logger, Guid orderId, string reason);
```

**Levels, and what actually belongs at each** *(be opinionated — "we log everything at Information" is a red flag)*:

| Level | Meaning | Rule of thumb |
|---|---|---|
| `Trace`/`Debug` | developer detail | **off in production** by default; enable per-scope when hunting |
| `Information` | a business milestone — order placed, message consumed | should be **countable**, not chatty. Not inside loops. |
| `Warning` | recovered or degraded — retry fired, cache miss storm, validation rejected | someone should look eventually, nobody wakes up |
| `Error` | this request failed and a user is affected | must be actionable; if it's not, it's a Warning |
| `Critical` | the process/dependency is down | pages someone |

**The rules that show experience:**
- **Log once, at the boundary.** `catch → log → rethrow` at every layer produces the same failure five times and makes error counts meaningless. Log where you *handle*, not where you *pass through* — see [[04-CSharp-Fundamentals#Exceptions|exceptions]].
- **`OperationCanceledException` is not an error.** Filter it out or your dashboard is noise every time a user closes a tab.
- **Never log PII, tokens, connection strings, card data.** Serilog destructuring will happily serialise a whole request object including the password — use `[NotLogged]`-style attributes, explicit projections, or a redaction enricher.
- **Never log inside a database transaction** if the sink is remote — you've put a network call inside a lock ([[21-Database-Part-2#Long transactions the systemic killer|long transactions]]).
- **Attach the trace ID to every log** so a log line links back to its trace (Part 5).

**Loki specifically** (your stack): Loki indexes **labels only**, not log content. So labels must stay low-cardinality (`app`, `env`, `level`) and everything else goes in the line, searched at query time. Putting `traceId` or `userId` in a *label* is the classic Loki mistake — it explodes the index. **Seq** is the opposite: it indexes properties, which is why it's excellent for a single app and expensive at fleet scale.

---

# Part 3 — Metrics

**Q: The instrument types?**

| Type | Behaviour | Example |
|---|---|---|
| **Counter** | monotonically increasing | `orders_placed_total`, `messages_consumed_total` |
| **Gauge** | goes up and down | queue depth, active connections, thread-pool threads |
| **Histogram** | bucketed distribution → percentiles | request duration, message age, payload size |
| **Up-down counter** | a counter that can decrease | items in flight |

```csharp
// .NET's built-in metrics API — OpenTelemetry picks these up directly
public sealed class BookingMetrics
{
    private readonly Counter<long>    _confirmed;
    private readonly Histogram<double> _holdDuration;

    public BookingMetrics(IMeterFactory factory)
    {
        var meter      = factory.Create("BateCom.Booking");
        _confirmed     = meter.CreateCounter<long>("bookings.confirmed", unit: "{booking}");
        _holdDuration  = meter.CreateHistogram<double>("bookings.hold.duration", unit: "s");
    }

    // ✅ LOW cardinality labels only
    public void Confirmed(string channel) => _confirmed.Add(1, new KeyValuePair<string, object?>("channel", channel));
    // ❌ NEVER: _confirmed.Add(1, new("bookingId", id)) — one time series per booking, forever
}
```

ASP.NET Core, `HttpClient` and the runtime emit **built-in meters** since .NET 8 (`http.server.request.duration`, `http.client.request.duration`, GC, thread pool) — you get the RED signals for free just by enabling the instrumentation.

**Q: What do you actually measure?** Use a named framework — it shows you're not guessing:

- **RED** — for every *service*: **R**ate (req/s), **E**rrors (%), **D**uration (p50/p95/p99).
- **USE** — for every *resource*: **U**tilisation, **S**aturation (queue depth — often the earliest warning), **E**rrors.
- **Four golden signals** — latency, traffic, errors, saturation. Same idea, Google's naming.

Then add the **business** metrics, which is what separates a senior answer: bookings confirmed per minute, payment success rate, outbox backlog, consumer lag. *"A drop in orders per minute is a better outage signal than CPU, because it's the thing that actually matters and it catches failures no infrastructure metric sees."*

> [!warning] You cannot average a percentile
> `avg(p99)` across instances is **mathematically meaningless**. Aggregate the histogram buckets and compute the quantile from the total — `histogram_quantile(0.99, sum(rate(bucket[5m])) by (le))`. Also: **p99 is a user, not a rounding error.** At 3,000 rps that's 30 people a second having your worst experience.

---

# Part 4 — Traces *(the senior part)*

**Q: What is a trace?**

A: One **trace** = the whole journey of a request, identified by a `trace_id`. It's a tree of **spans**, each with a name, start/end, attributes, status, and a parent span ID. The trace shows where the time went and what called what — the thing no log or metric can tell you in a distributed system.

```text
trace_id=4bf92f…  POST /api/bookings                                    [ 840ms ]
 ├─ Middleware: auth                                                     [   4ms ]
 ├─ MediatR: CreateBookingCommand                                        [ 812ms ]
 │   ├─ EF Core: SELECT availability                                     [  12ms ]
 │   ├─ HTTP POST payments.stripe.com                                    [ 700ms ]  ← there it is
 │   └─ EF Core: INSERT booking + outbox                                 [  18ms ]
 └─ RabbitMQ publish: BookingConfirmed                                   [   6ms ]
      └─ [consumer, different process] Billing: CreateInvoice            [  95ms ]   ← same trace_id
```

**Q: How does the trace ID travel?**

A: **W3C Trace Context** — a `traceparent` header, `00-<32 hex trace-id>-<16 hex span-id>-<flags>`. Over HTTP it's automatic. In .NET the primitive is `System.Diagnostics.Activity`: `Activity.Current` carries the context, `ActivitySource` creates spans, and OpenTelemetry exports them.

```csharp
private static readonly ActivitySource Source = new("BateCom.Booking");

using var activity = Source.StartActivity("ConfirmBooking", ActivityKind.Internal);
activity?.SetTag("booking.id", bookingId);            // high cardinality is FINE on a span
activity?.SetTag("booking.channel", channel);
try
{
    await _handler.HandleAsync(cmd, ct);
}
catch (Exception ex)
{
    activity?.SetStatus(ActivityStatusCode.Error, ex.Message);   // makes it findable as a failed trace
    throw;
}
```

## The question for *your* CV: propagation across the broker

**Q: Your producer publishes to RabbitMQ and a consumer in another process handles it. How does the trace survive?**

A: It doesn't — **unless you propagate it explicitly**. HTTP propagation is automatic because the header rides along; a message is just bytes on a queue. So the pattern is:

1. **Producer**: inject the current `traceparent` (and `tracestate`) into the **message headers** before publishing.
2. **Consumer**: extract those headers and start its span with the extracted context as **parent** — or, for a queued hand-off, as a **span link**.

```csharp
// Conceptually — MassTransit does this for you when OTel instrumentation is enabled:
//   .AddOpenTelemetry().WithTracing(t => t.AddSource("MassTransit"))
// Hand-rolled, it's inject/extract via the OTel propagator:
Propagators.DefaultTextMapPropagator.Inject(
    new PropagationContext(activity.Context, Baggage.Current), headers,
    (h, key, value) => h[key] = value);
```

**The nuance to state:** a consumer usually runs **long after** the producer finished, so making it a plain child span produces a trace with a huge gap. The correct modelling is `ActivityKind.Producer` / `ActivityKind.Consumer`, and for genuinely detached async work a **span link** rather than a parent-child edge — the causal relationship is recorded without pretending it's one synchronous operation.

**And the async reality:** a retried message, a DLQ replay, or an outbox relay publishing 200 events at once are all *separate* traces causally linked to the original. This is exactly where `correlationId`/`causationId` in message metadata earn their place — see [[22-Event-Sourcing-And-EDA#Part 4 — EventStoreDB specifics|correlation and causation]] and [[11-Module-Communication|Module Communication]].

## Sampling

**Q: You can't keep every trace. How do you choose?**

| | **Head sampling** | **Tail sampling** |
|---|---|---|
| Decided | at the start of the trace, in the app | after the trace completes, in the **Collector** |
| Cost | cheap, no buffering | must buffer whole traces in memory |
| Problem | you may drop the **one** trace you needed | infrastructure and memory |
| Typical | `ParentBased(TraceIdRatioBased(0.1))` — 10%, consistent across services | **keep 100% of errors and slow traces, sample the boring successes** |

The senior answer: *"Head sampling with a parent-based ratio so a trace is kept or dropped consistently across every service — a 10% decision made independently per service gives you shredded traces. Where it matters I add tail sampling at the Collector so **every error and every slow request is kept**, and normal traffic is sampled down. And sampling is a metrics problem too: metrics stay 100%, so my counts stay correct even when traces are sampled."*

**Auto vs manual instrumentation:** turn on the auto-instrumentation first — ASP.NET Core, `HttpClient`, EF Core, StackExchange.Redis, MassTransit — which gives you most of the picture for free. Add **manual spans only around meaningful business operations** (`ConfirmBooking`, `RebuildProjection`), not around every method. Over-instrumenting produces traces nobody can read.

---

# Part 5 — OpenTelemetry in .NET, concretely

```csharp
builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r
        .AddService(serviceName: "batecom-api", serviceVersion: "1.4.2")
        .AddAttributes([new("deployment.environment", builder.Environment.EnvironmentName)]))
    .WithTracing(t => t
        .AddAspNetCoreInstrumentation(o => o.RecordException = true)
        .AddHttpClientInstrumentation()
        .AddEntityFrameworkCoreInstrumentation(o => o.SetDbStatementForText = true)  // careful: SQL may contain PII
        .AddSource("BateCom.Booking")
        .AddSource("MassTransit")
        .AddOtlpExporter())
    .WithMetrics(m => m
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .AddMeter("BateCom.Booking")
        .AddOtlpExporter());
```

**Resource attributes are not optional** — `service.name`, `service.version` and `deployment.environment` are what let you say "p99 regressed in 1.4.2" instead of "something is slow somewhere."

**Q: Why run an OpenTelemetry Collector instead of exporting straight to Tempo/Prometheus/Loki?**

Because it decouples the app from the backends. The Collector gives you: **fan-out** to several backends (exactly your Tempo + Prometheus + Loki setup) from one OTLP endpoint · **batching and retry** so a backend outage doesn't back-pressure your app · **redaction/filtering** of attributes centrally instead of in every service · **tail sampling** · **enrichment** with k8s/host metadata · and the ability to **change backend without redeploying a single service**. That last one is the answer.

**Correlating the three pillars** — the piece that makes it one investigation rather than three tools:

```csharp
// Serilog: stamp TraceId/SpanId onto every log line, so a log links to its trace
Log.Logger = new LoggerConfiguration()
    .Enrich.FromLogContext()
    .Enrich.WithProperty("service.name", "batecom-api")
    .Enrich.With<TraceIdEnricher>()     // reads Activity.Current.TraceId
    .WriteTo.Seq(seqUrl)
    .CreateLogger();
```

- **Logs → traces:** every log carries `trace_id`; in Grafana, Loki's *derived fields* turn it into a link straight to the trace in Tempo.
- **Metrics → traces:** **exemplars** attach a sample `trace_id` to a histogram bucket, so you click the p99 spike and land in an actual slow trace.
- **Traces → logs:** from a span, filter Loki by that `trace_id`.

*(If they mention **.NET Aspire** — which your CV does — `AddServiceDefaults()` wires exactly this: OTel tracing/metrics/logging with OTLP export, health-check endpoints, service discovery and default resilience handlers. Knowing that Aspire is a **dev-time orchestration and defaults story**, not a production runtime, is the right nuance.)*

---

# Part 6 — Health checks

**Q: Liveness vs readiness vs startup?**

| Probe | Question | Failure means | Rule |
|---|---|---|---|
| **Startup** | "has it finished booting?" | keep waiting, don't kill it yet | for slow starters — protects them from liveness |
| **Liveness** | "is this process wedged?" | **restart the container** | must be **shallow** — no dependency checks |
| **Readiness** | "can it serve traffic right now?" | **pull it from the load balancer** (don't restart) | may check critical dependencies — carefully |

```csharp
builder.Services.AddHealthChecks()
    .AddCheck("self", () => HealthCheckResult.Healthy(), tags: ["live"])
    .AddNpgSql(cs,    tags: ["ready"])
    .AddRedis(redis,  tags: ["ready"]);   // think hard before adding this one

app.MapHealthChecks("/health/live",  new() { Predicate = c => c.Tags.Contains("live")  });
app.MapHealthChecks("/health/ready", new() { Predicate = c => c.Tags.Contains("ready") });
```

> [!warning] The trap worth naming out loud
> **A readiness check that fails on a dependency blip takes every instance out of rotation at once — turning a degraded dependency into a total outage.** And if *liveness* checks the database, a slow database restarts your whole fleet, which is strictly worse than serving degraded responses. So: liveness stays shallow; readiness only covers dependencies you genuinely cannot serve *anything* without; and for optional dependencies (Redis) prefer **degrade and fail open** ([[18-Distributed-Systems-Reliability#"What happens when Redis is down?"|what happens when Redis is down]]) over declaring yourself unready.

---

# Part 7 — Alerting that people don't ignore

**Q: What do you alert on?**

A: **Symptoms, not causes.** High CPU is not an incident — *users getting errors or waiting* is. Alerting on causes produces pages for things nobody needs to act on, and misses the outage that had normal CPU.

- **Page on:** SLO burn rate (error budget being consumed fast), sustained elevated error rate, latency past the SLO threshold, queue/consumer lag growing without bound, **DLQ depth > 0**, outbox backlog growing, a job that didn't run.
- **Ticket, don't page:** disk at 70%, certificate expiring in 20 days, a slowly rising p99.
- **Never page on:** a single failed request, CPU %, memory %, a retry that succeeded.

**SLI / SLO / error budget** — the vocabulary to use (the definitions are in [[16-System-Design|System Design §32]]): an SLI is the measurement, an SLO the target (99.9% of requests < 300 ms over 30 days), and the **error budget** is the 0.1% you're allowed to burn. Multi-window **burn-rate alerts** (fast burn → page; slow burn → ticket) are how you avoid both alert fatigue and silent degradation. The cultural point worth making: *"the error budget makes reliability a shared, negotiable number instead of an argument — if we've burned it, we stop shipping features and fix reliability."*

**Every alert needs a runbook** — what it means, how to confirm, first three actions, how to escalate. An alert without one is a page that ends in someone guessing at 3am. And **review alerts regularly**: any alert that fired and needed no action is either mistuned or should be deleted.

---

# Part 8 — "Debug this slow request in production"

*(Answer with a **path through your telemetry**, not a list of tools.)*

> **1. Confirm and scope it.** Is it p99 or everyone? Since when? Which endpoint, tenant, region, version? *(RED dashboard.)* This separates "one user's phone" from "we shipped a regression at 14:02".
>
> **2. Correlate with a change.** Deploy markers on the dashboard, feature-flag flips, a migration, a traffic spike. Most incidents are caused by a change; check that before theorising.
>
> **3. Find an exemplar trace.** Click the p99 bucket → a real slow trace. Don't sample by hand; go from the metric to the trace.
>
> **4. Read the waterfall.** Where did the time actually go? Typical shapes: one slow downstream span (dependency) · **many small repeated spans (N+1)** · a long gap with no span (queueing, lock wait, GC, or missing instrumentation — the gap itself is information) · time before your first span (load balancer, TLS, cold start).
>
> **5. Drop to logs for that `trace_id`.** The span says *where*; the log says *why* — the retry that fired, the cache miss, the validation branch.
>
> **6. Check the resource dimension.** DB wait stats / `pg_stat_activity`, connection-pool saturation, thread-pool queue length, GC time. Slow-with-low-CPU almost always means **waiting**: blocking, pool exhaustion, or a lock ([[21-Database-Part-2#Part 9 — Diagnostic scenarios|DB diagnostics]], [[04-CSharp-Fundamentals#Concurrency and Thread Safety|thread pool starvation]]).
>
> **7. Fix, verify on the same dashboard, and close the loop** — add the missing span/metric that would have made this a 5-minute investigation instead of an hour.

Step 7 is the one that marks a senior: **every incident should improve the instrumentation**, so the next unknown unknown is a known one.

---

# Part 9 — Cost and pitfalls

| Pitfall | What happens | Fix |
|---|---|---|
| **Metric cardinality explosion** | `userId`/`orderId` as a label → millions of series → Prometheus OOMs | IDs belong on spans and logs, never metric labels |
| **Loki label cardinality** | `traceId` as a *label* explodes the index | labels stay low-cardinality; put the rest in the line |
| **Logging in a hot loop at Information** | logs cost more than the feature | sample repetitive logs; use `Debug` |
| **100% trace sampling at scale** | storage bill and network overhead | head-sample the boring, tail-keep errors and slow traces |
| **Logging PII / SQL text with parameters** | a GDPR incident inside your observability stack | redact in the Collector; be careful with `SetDbStatementForText` |
| **Alerting on causes** | fatigue, then ignored pages | alert on symptoms and burn rate |
| **Dashboards nobody reads** | false comfort | one RED dashboard per service, one per critical dependency, and delete the rest |
| **Instrumenting everything** | unreadable traces, high cost | auto-instrumentation + a few meaningful business spans |

**The cost conversation, done like a senior:** *"Logs are the expensive pillar, metrics the cheap one, traces in between. So I push detail down the stack: aggregate what I can into metrics, sample traces with 100% error retention, and keep logs structured and short-retention with the important ones promoted. Retention is a tiered decision — 7 days hot, 30 days cold — not one number for everything."*

---

## Rapid-Fire Drill

| # | Probe | Your answer, compressed |
|---|---|---|
| 1 | Monitoring vs observability? | Known unknowns vs answering a question you didn't anticipate, without shipping code. |
| 2 | The three pillars, in one workflow? | Metric says something's wrong → trace says where → log says why. Linked by IDs or it's three tools and no answer. |
| 3 | What is cardinality and why care? | Distinct values per dimension. Fatal in metrics, essential in traces/logs. |
| 4 | What's wrong with `$"Order {id}"` in a log? | Interpolation kills the structure — no filtering by `OrderId`, and you format even when the level is off. |
| 5 | How do you log an exception you rethrow? | You don't — log once where you handle it. Log-and-rethrow multiplies one failure into five. |
| 6 | What is a trace made of? | Spans in a tree, sharing a `trace_id`, propagated via the W3C `traceparent` header. |
| 7 | How does a trace cross RabbitMQ? | Inject `traceparent` into message headers, extract on consume. Producer/Consumer span kinds, or a **span link** for detached work. |
| 8 | Head vs tail sampling? | Decide at start (cheap, may drop the interesting one) vs at the Collector after completion (keep all errors/slow). |
| 9 | Why parent-based sampling? | So the decision is consistent across services — otherwise you get shredded partial traces. |
| 10 | Why an OTel Collector? | Fan-out to multiple backends, batching/retry, central redaction, tail sampling, and swapping backends without redeploying. |
| 11 | RED vs USE? | RED = Rate/Errors/Duration for services. USE = Utilisation/Saturation/Errors for resources. |
| 12 | Can you average p99 across instances? | No — aggregate histogram buckets and compute the quantile. |
| 13 | Best outage signal? | A business metric — orders per minute — not CPU. |
| 14 | Liveness vs readiness? | Wedged → restart (keep it shallow) vs can't serve → remove from LB. |
| 15 | Why is a deep readiness check dangerous? | A dependency blip pulls every instance at once, turning degradation into a full outage. |
| 16 | What do you page on? | Symptoms and SLO burn rate — errors, latency, growing lag, DLQ > 0. Never CPU. |
| 17 | What's an error budget for? | It turns reliability into a negotiable number: burn it and you stop shipping features. |
| 18 | Which pillar costs most? | Logs. Push detail into metrics, sample traces, tier retention. |
| 19 | Serilog + traces? | Enrich every log with `TraceId`, then Grafana derived fields jump from a Loki line to the Tempo trace. |
| 20 | Debug a slow request — first move? | Scope it on the RED dashboard and check for a deploy — then go metric → exemplar trace → waterfall → logs for that `trace_id`. |
