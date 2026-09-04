---
title: Distributed Systems & Reliability
aliases: [Distributed Systems, Reliability, Idempotency, Outbox, Caching Strategy, Redis]
tags: [distributed-systems, reliability, caching, redis, scaling, consistency, interview]
order: 18
---

# Distributed Systems & Reliability - Interview Q&A

> [!info]+ Related Notes
> [[11-Module-Communication|Module Communication]] · [[12-RabbitMQ-MassTransit|RabbitMQ & MassTransit]] · [[16-System-Design|System Design]] · [[17-Architecture-Defense|Architecture Defense]] · [[06-Database|Database]] · [[04-CSharp-Fundamentals|C# Fundamentals]] · [[22-Event-Sourcing-And-EDA|Event Sourcing & EDA]] · [[23-Observability|Observability]]

> [!danger]+ How this round is scored
> Every question in this round is really **one** question: *"what happens when this part fails?"* Junior answers describe the happy path. Senior answers name the **failure mode**, the **guarantee** it breaks, and the **cost** of the fix.
>
> Three sentences that make you sound senior, used honestly:
> - "That's **at-least-once**, so the consumer has to be idempotent."
> - "That's a **dual write** — it can't be made atomic, so I'd use an outbox."
> - "I'd rather be **available and slightly stale** here, and strongly consistent there — because *this* is money and *that* is a listing page."

---

# 1. Reliability Primitives

## Idempotency

**Q: What is idempotency and why does distributed computing force it on you?**

A: An operation is idempotent if performing it **N times has the same effect as performing it once**. It's mandatory because in a distributed system you can never distinguish *"the request failed"* from *"the response was lost."* A timeout tells you **nothing** about whether the work happened — so the caller must retry, and the receiver must tolerate the retry.

**Q: How do you make an operation idempotent?** Four techniques, cheapest first:

```csharp
// 1) NATURAL IDEMPOTENCY — design the operation so repetition is harmless
order.Status = OrderStatus.Cancelled;         // idempotent (absolute set)
order.Attempts += 1;                          // NOT idempotent (relative change)
// "SET balance = 100" is idempotent; "ADD 50 to balance" is not.

// 2) UNIQUE CONSTRAINT — let the database be the arbiter (strongest, no race)
// UNIQUE INDEX on (IdempotencyKey) — a duplicate insert simply fails
try { await _db.SaveChangesAsync(ct); }
catch (DbUpdateException e) when (e.IsUniqueViolation()) { return existingResult; }

// 3) IDEMPOTENCY KEY — the API-level pattern (Stripe's model)
[HttpPost("payments")]
public async Task<IActionResult> Pay([FromHeader(Name = "Idempotency-Key")] string key, PayRequest req)
{
    var existing = await _store.FindAsync(key, ct);
    if (existing is not null)
    {
        if (existing.RequestHash != Hash(req)) return Conflict("Key reused with a different body");
        if (existing.Status == InFlight)      return Accepted();      // concurrent duplicate
        return Ok(existing.Response);                                 // replay the stored response
    }
    await _store.ReserveAsync(key, Hash(req), ct);   // insert InFlight row in the SAME tx as the work
    ...
}

// 4) INBOX / DEDUPE TABLE — for message consumers
if (await _inbox.AlreadyProcessedAsync(message.MessageId, ct)) return;   // discard duplicate
await ProcessAsync(message, ct);
await _inbox.MarkProcessedAsync(message.MessageId, ct);   // same transaction as the work
```

**The details that separate levels:**
- **Store the response, not just a flag.** A retry must return the *same answer* — the caller needs the payment ID, not a bare `200`.
- **Reserve the key inside the same transaction as the work**, or two concurrent duplicates both see "not processed" and both run.
- **Keys need a TTL** (24h–7d is typical) or the table grows forever. State the retention.
- **Who generates the key?** The **client**, once per logical intent — regenerating it per retry defeats the entire mechanism.

## At-least-once, at-most-once, and why exactly-once is a lie

| Guarantee | Mechanism | You lose | Reality |
|---|---|---|---|
| **At-most-once** | fire-and-forget, ack before processing | messages, on crash | fine for metrics/telemetry |
| **At-least-once** | ack **after** processing, redeliver on failure | nothing; you get **duplicates** | **the default everywhere real** |
| **Exactly-once** | — | — | **not achievable in delivery** |

**Q: Why is exactly-once delivery impossible?**

A: It reduces to the **Two Generals problem**. Delivery ends with an acknowledgement, and the ack can be lost. So the sender must choose: retry (risk a duplicate → at-least-once) or don't (risk a loss → at-most-once). No protocol removes that choice, because there is no way to make "process the message" and "record the ack" a single atomic action across two machines.

**What you *can* have is "effectively once":**

> **at-least-once delivery + idempotent consumer = effectively-once processing**

The duplicate still *arrives*; it just has no effect. That's the sentence to say.

> [!tip] If they mention Kafka's "exactly-once semantics"
> It's real but narrow: it's exactly-once *processing* **within Kafka** — a transaction spanning consume-offset-commit and produce, inside one Kafka cluster. The moment your handler writes to Postgres or calls Stripe, you're outside the transaction and back to at-least-once. Naming that boundary is a strong signal.

## The transactional outbox

**Q: What is the dual-write problem?**

A: Any time one operation must update **two systems that can't share a transaction**, there's a window where one succeeds and the other doesn't — and no ordering fixes it:

```csharp
// BROKEN — three distinct failure modes, all of which happen in production
await _db.SaveChangesAsync(ct);            // (1) commits
await _bus.Publish(new OrderPlaced(...));  // (2) process dies here -> order exists, nobody knows

// Swapping the order doesn't help:
await _bus.Publish(new OrderPlaced(...));  // published
await _db.SaveChangesAsync(ct);            // fails -> consumers act on an order that doesn't exist
```

A distributed transaction (2PC/XA) "solves" it by making both systems block on a coordinator — availability collapses to the weakest link, brokers mostly don't support it, and nobody wants it. So:

**Q: How does the outbox fix it?**

A: **Remove the second system from the critical path.** Write the message into an *outbox table in the same database, in the same transaction* as the business data. One atomic commit, one system. A separate relay publishes it afterwards.

```csharp
// Atomic: business change + intent to publish
await using var tx = await _db.Database.BeginTransactionAsync(ct);
_db.Orders.Add(order);
_db.Outbox.Add(new OutboxMessage {
    Id = Guid.NewGuid(), Type = nameof(OrderPlaced),
    Payload = JsonSerializer.Serialize(evt), OccurredOn = DateTime.UtcNow, ProcessedOn = null
});
await _db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);          // both rows commit or neither does — no dual write

// Relay (BackgroundService, or MassTransit's built-in outbox)
var batch = await _db.Outbox.Where(m => m.ProcessedOn == null)
                            .OrderBy(m => m.OccurredOn).Take(100).ToListAsync(ct);
foreach (var m in batch)
{
    await _bus.Publish(Deserialize(m), ct);   // may crash AFTER publish, BEFORE marking
    m.ProcessedOn = DateTime.UtcNow;          // => at-least-once. Consumers must be idempotent.
}
await _db.SaveChangesAsync(ct);
```

**The four follow-ups you should pre-empt:**
1. **"Doesn't that give duplicates?"** — Yes, deliberately. Crash between publish and mark → redelivery. At-least-once by design; the consumer dedupes.
2. **"Polling is inefficient."** — For most systems a 1–5s poll with an index on `(ProcessedOn, OccurredOn)` is fine. If latency matters, use **CDC** (Debezium reading the WAL) instead of polling. Trade-off: lower latency and less DB load, but a whole new piece of infrastructure to run.
3. **"Ordering?"** — A single relay preserves order per stream; parallel relays don't. If order matters, partition by aggregate ID and process one partition serially. Better: **design consumers not to need global ordering** (version numbers, or last-write-wins on a timestamp).
4. **"Multiple instances?"** — They'd publish the same rows twice. Use `SELECT ... FOR UPDATE SKIP LOCKED` (Postgres), a leader election, or a single-instance worker. Naming `SKIP LOCKED` lands very well.

**The mirror image is the inbox:** the consumer records `MessageId` in a dedupe table *in the same transaction as its side effects*, so redelivery is a no-op. Outbox + inbox = the standard pair.

## Retries done properly

**Q: What's wrong with `for (int i = 0; i < 3; i++) { try { ... } catch { } }`?**

A: Three things: it retries **non-transient** errors (a 400 will never succeed), it retries **non-idempotent** operations (three payments), and it retries **immediately and in lockstep** with every other client — a *thundering herd* that turns a blip into an outage.

**Exponential backoff + jitter:**

```text
Attempt:      1      2      3      4       5
No backoff:  0ms    0ms    0ms    0ms     0ms    <- hammers a struggling service
Exponential: 1s     2s     4s     8s     16s     <- better, but all clients retry IN SYNC
+ jitter:    0.7s   2.9s   3.1s   9.8s   12.4s   <- retries spread out. THIS is the answer.
```

Jitter is the part candidates forget. Without it, every client that failed at T+0 retries at exactly T+1s, T+3s, T+7s — synchronised waves that keep the service down. Randomising the delay (AWS's "full jitter": `sleep = random(0, base * 2^attempt)`) flattens the wave.

```csharp
// Polly v8 resilience pipeline on a typed HttpClient
services.AddHttpClient<IPaymentApi, PaymentApi>()
    .AddResilienceHandler("payments", builder => builder
        .AddTimeout(TimeSpan.FromSeconds(3))                       // per attempt
        .AddRetry(new HttpRetryStrategyOptions
        {
            MaxRetryAttempts = 3,
            BackoffType      = DelayBackoffType.Exponential,
            UseJitter        = true,                                // <- say this word
            ShouldHandle     = args => ValueTask.FromResult(
                args.Outcome.Result?.StatusCode is HttpStatusCode.RequestTimeout
                    or HttpStatusCode.ServiceUnavailable or HttpStatusCode.TooManyRequests
                || args.Outcome.Exception is HttpRequestException)  // transient ONLY
        })
        .AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
        {
            FailureRatio = 0.5, SamplingDuration = TimeSpan.FromSeconds(30),
            MinimumThroughput = 10, BreakDuration = TimeSpan.FromSeconds(15)
        })
        .AddTimeout(TimeSpan.FromSeconds(10)));                     // total, across all attempts
```

**Rules to state:**
- **Only retry transient faults**, and **only idempotent operations** — otherwise you need an idempotency key first.
- **Two timeouts**: per-attempt and overall. Without the outer one, 3 retries × 30s = a 90s request holding a thread and a connection.
- **A timeout must be shorter than your caller's timeout**, or you do work nobody is waiting for.
- **Retry budget**: cap retries as a fraction of total traffic (~10%). Otherwise a partial outage triples your own load at the worst moment.
- **Retry at one layer only.** Retries at HTTP + repository + message consumer multiply: 3×3×3 = 27 calls.

**Circuit breaker** — stop calling a service that is clearly down: **Closed** (normal, counting failures) → **Open** (fail fast immediately, no calls, no threads consumed) → **Half-Open** (let one trial request through) → Closed on success / Open on failure. Its real job is **protecting yourself** (threads, connections, latency) as much as sparing the downstream. **Fail fast, with a fallback**: cached data, a queued request, or a clear degraded response.

**Bulkhead**: cap concurrency per dependency (`SemaphoreSlim` / Polly bulkhead) so one slow dependency can't consume every thread. Ship-hull logic — one flooded compartment, not the whole vessel. See [[04-CSharp-Fundamentals#Concurrency and Thread Safety|thread pool starvation]].

## DLQ and poison messages

**Q: A message fails every time you process it. What happens?**

A: Without a plan: **infinite redelivery**. It blocks the queue (if ordered), burns CPU, floods logs, and can take the consumer down. That message is *poison*.

**The ladder:**
1. **Immediate retries** (2–3, milliseconds apart) — covers a blip.
2. **Delayed/scheduled retries** (seconds to minutes, backoff + jitter) — covers a downstream restart. In MassTransit: `r.Immediate(3)` then `r.Interval(5, TimeSpan.FromMinutes(1))`.
3. **Move to the Dead Letter Queue** after the budget is spent — with the failure reason, stack trace, retry count and original headers preserved.
4. **Alert on DLQ depth > 0.** A DLQ nobody monitors is `/dev/null` with extra steps.
5. **Provide a replay path** — fix the bug or the data, then re-publish from the DLQ. Manual approval, and idempotent consumers make replay safe.

**Common causes to name:** a schema change the consumer can't deserialise (versioning failure) · a referenced entity that no longer exists · a genuine bug on one code path · an unhandled `null`. **Distinguish "poison" (never succeeds — DLQ it) from "downstream is down" (would succeed later — retry it).** Treating the second as the first fills your DLQ with valid work.

## Hangfire vs a real broker

**Q: You use Hangfire. When is that the wrong tool?**

| | **Hangfire** | **RabbitMQ / MassTransit** |
|---|---|---|
| Storage | your SQL database | a dedicated broker |
| Model | **jobs** — "run this method later" | **messages** — "this happened / do this" |
| Coupling | caller references the target method | publisher knows nothing about consumers |
| Scope | within one application | **across services** |
| Strengths | recurring (cron) jobs, delayed jobs, retries + a dashboard, no extra infra | fan-out pub/sub, routing, backpressure, huge throughput, language-agnostic |
| Weaknesses | polls the DB (load + latency), throughput bounded by SQL, jobs serialise a **method call** → refactor and old queued jobs break | infra to run, monitor and secure; more moving parts |

**The answer:** "Hangfire for **in-process background work on a schedule** — nightly reports, cleanup, sending an email after commit, a retryable job the same app owns. A broker the moment work must **cross a service boundary**, fan out to multiple unknown consumers, survive independently of my app, or absorb bursts with backpressure. Hangfire's queue is a table in my database — at high throughput that's contention on my own OLTP database, and that's the point where it stops being free."

> [!warning] The trap
> "Both give me retries" is not a reason to treat them as interchangeable. Hangfire serialises a **method invocation** — rename or move that method and every queued job fails on deserialisation. A broker carries a **contract**, which is versionable. That's an architectural difference, not a feature difference.

---

# 2. Caching

## Strategies and invalidation

**Q: Cache-aside vs write-through — which and why?**

| | **Cache-aside (lazy)** | **Write-through** | **Write-behind** |
|---|---|---|---|
| Read | check cache → miss → DB → populate | always a hit after the first write | same |
| Write | write DB, **invalidate** the key | write cache **and** DB synchronously | write cache, flush to DB async |
| Staleness | up to the TTL | none (if all writes go through it) | window of possible **data loss** |
| Cold start | first read per key is slow | pre-warmed | pre-warmed |
| Failure | cache down → slow but **correct** | cache down → writes fail | cache down → **data lost** |
| Use | **default; 90% of systems** | read-heavy on a small hot set | high write volume, loss-tolerant (counters, analytics) |

**Say:** "Cache-aside, because it only caches what's actually requested and it **degrades to correct-but-slow** if Redis dies. Write-through is only worth it when I control every write path — and one background job writing straight to the DB silently breaks that assumption."

**Q: How do you invalidate?** In order of preference:

```csharp
// 1) TTL only — the simplest correct thing. "Stale for at most 60s" is a real, statable SLA.
await _cache.SetAsync(key, value, TimeSpan.FromSeconds(60));

// 2) Explicit invalidation on write — precise, but you must find every write path
await _repo.UpdateAsync(product, ct);
await _cache.RemoveAsync($"product:{product.Id}");        // DELETE, don't update:
// updating the cache from the writer causes lost updates under concurrency (two writers interleave)

// 3) Versioned / generation keys — invalidate a whole family with one write, no scanning
var v = await _cache.StringIncrementAsync("catalog:version");   // bump on any catalog change
var key = $"catalog:v{v}:page:{page}";                          // old keys are orphaned, TTL reaps them

// 4) Pub/sub fan-out — needed when you also keep an in-process L1 cache
await _redis.GetSubscriber().PublishAsync("invalidate", key);   // every pod drops its local copy
```

**The line to deliver:** "There are two hard problems in computer science, and cache invalidation is the one I try hardest to *avoid solving*. A short TTL plus explicit invalidation on the few write paths I own covers almost everything. When I can't enumerate the write paths, TTL is the only honest answer."

## Stampede protection and TTL jitter

**Q: A popular key expires and 500 requests arrive in the same second. What happens?**

A: **Cache stampede / dog-piling** — all 500 miss, all 500 hit the database with the identical query, the DB saturates, latency spikes, and the responses are slow enough that more requests pile in. A cache *miss* just became an outage.

```csharp
// Fix 1: single-flight — one request rebuilds, the rest wait for it
private static readonly ConcurrentDictionary<string, SemaphoreSlim> _locks = new();

public async Task<T> GetOrCreateAsync<T>(string key, Func<Task<T>> factory, TimeSpan ttl, CancellationToken ct)
{
    if (await _cache.TryGetAsync<T>(key) is { } hit) return hit;

    var gate = _locks.GetOrAdd(key, _ => new SemaphoreSlim(1, 1));
    await gate.WaitAsync(ct);
    try
    {
        if (await _cache.TryGetAsync<T>(key) is { } second) return second;   // double-check: rebuilt while we waited
        var value = await factory();
        await _cache.SetAsync(key, value, Jittered(ttl));
        return value;
    }
    finally { gate.Release(); }
}
// Note: this lock is PER-POD. Across 10 pods you get 10 rebuilds, not 500 — usually enough.
// For a genuinely expensive rebuild, take a distributed lock (below) instead.

// Fix 2: TTL + jitter — never let a batch of keys expire together
private static TimeSpan Jittered(TimeSpan ttl) =>
    ttl + TimeSpan.FromSeconds(Random.Shared.Next(0, (int)(ttl.TotalSeconds * 0.2)));
// Warming 10,000 keys at startup with a flat 300s TTL = all 10,000 expire in the same second, forever.

// Fix 3: serve stale while revalidating — return the old value, refresh in the background
// Fix 4: .NET 9 HybridCache — L1 in-memory + L2 Redis, WITH built-in stampede protection
var value = await _hybridCache.GetOrCreateAsync(key, ct => LoadAsync(ct), cancellationToken: ct);
```

Also worth naming: **negative caching** (cache "not found" briefly, or a miss on a nonexistent ID is a free DB hit every time — and an attack vector), and **cache penetration** (random nonexistent keys bypassing the cache entirely → Bloom filter or negative cache).

## Redis specifics

**Q: Eviction policies — which do you set and why?**

`maxmemory-policy` decides what happens when `maxmemory` is reached:

| Policy | Behaviour | Use for |
|---|---|---|
| `noeviction` | **writes fail** with OOM | Redis as a datastore/queue — losing data is worse than failing |
| `allkeys-lru` | evict least-recently-used, any key | **pure cache — the usual answer** |
| `allkeys-lfu` | evict least-*frequently*-used | skewed traffic where a few keys are hot forever |
| `volatile-lru` | LRU among keys **that have a TTL** | mixed store: persistent keys + cache keys in one instance |
| `volatile-ttl` | evict shortest remaining TTL first | — |
| `allkeys-random` / `volatile-random` | random | very high churn where LRU bookkeeping isn't worth it |

> [!warning] The trap in `volatile-*`
> If **no** key has a TTL, `volatile-lru` behaves like `noeviction` — writes start failing while memory looks full. A cache where someone forgot `SetAsync(..., ttl)` fails in exactly this way.

**Q: Redis persistence?**
- **RDB** — periodic point-in-time snapshot. Fast restart, compact, `fork()`-based; you lose everything since the last snapshot.
- **AOF** — append-only log of writes. `appendfsync everysec` is the sane default (lose ≤1s); `always` is durable and slow. Larger files, rewrite/compaction needed.
- **Both** is common: AOF for durability, RDB for fast restore.
- **For a cache, "none" is a legitimate choice** — and say why: persistence costs `fork()` latency spikes on a large dataset, and a cache should be able to cold-start.

**Other Redis points that land:** command execution is **single-threaded**, so one `KEYS *` or a big `LRANGE` on a 10M-element list **blocks every other client** — use `SCAN`, keep values small, watch for big keys. Use **pipelining** to cut round-trips, and **Lua scripts** when you need multiple commands to be atomic. Cluster mode shards by hash slot, so multi-key operations must use **hash tags** (`{user:123}:orders`) to co-locate.

**Q: Distributed lock in Redis — and the Redlock caveats?**

```csharp
// Correct single-instance lock: atomic SET with NX + expiry + a unique token
var token = Guid.NewGuid().ToString();
bool acquired = await db.StringSetAsync(key, token, TimeSpan.FromSeconds(30), When.NotExists);

// Release MUST be atomic and check ownership — otherwise you release someone else's lock
// (your process paused, the TTL expired, another holder took it, then you deleted theirs)
const string release = @"if redis.call('get', KEYS[1]) == ARGV[1]
                         then return redis.call('del', KEYS[1]) else return 0 end";
await db.ScriptEvaluateAsync(release, new RedisKey[] { key }, new RedisValue[] { token });
```

**The Redlock critique to state:** Redlock (locking across N independent masters) is **not safe for correctness**, per Kleppmann's well-known analysis. Two reasons: it depends on **bounded clock drift and bounded pauses** — a GC pause or VM freeze longer than the TTL means you *believe* you hold a lock you've already lost; and **failover can lose the lock** (a master accepts the lock, dies before replicating, the replica has no record, a second client acquires it). A lock service can't fix this alone — the resource itself must reject stale holders via a **fencing token** (monotonically increasing number, checked on write).

**So:** "Redis locks are fine as an **efficiency** optimisation — 'usually only one worker does this job, and a rare double-run is harmless'. For **correctness** — money, inventory, no-double-booking — I don't use a distributed lock; I use a **database transaction with a unique constraint or `SELECT ... FOR UPDATE`**, because the database is the thing that must reject the second writer anyway." That answer is the single most senior thing you can say about distributed locking.

## "What happens when Redis is down?"

**Q: Redis is unavailable. Walk me through it.** *(Have this answer ready — it's asked constantly.)*

**1. Decide the failure mode per use case — this is the actual question:**

| Redis is used as | Behaviour when down | Why |
|---|---|---|
| **Read cache** | **Fail open** — treat every read as a miss, go to the DB | correctness is preserved; you're only slower |
| **Session store** | **Fail closed** — users are logged out; failing open means no auth | security > availability |
| **Rate limiter** | Judgement call — usually **fail open**, with a local in-process limiter as a fallback | open risks abuse, closed blocks real users |
| **Distributed lock** | **Fail closed** — never assume you hold a lock you couldn't take | see the fencing discussion above |
| **Primary data / queue** | You're down | that's the cost of using a cache as a database |

**2. Make failing open actually work** — the naive version makes things *worse*, because every request now waits for a Redis timeout **before** hitting the DB:

```csharp
// Short timeouts + a circuit breaker so you stop calling a dead cache
services.AddSingleton<IConnectionMultiplexer>(_ => ConnectionMultiplexer.Connect(new ConfigurationOptions
{
    ConnectTimeout = 1000, SyncTimeout = 1000, AbortOnConnectFail = false, ConnectRetry = 3
}));

try { return await _cache.GetAsync<T>(key, ct); }
catch (RedisConnectionException ex) { _log.LogWarning(ex, "Cache down, falling through"); return null; }
// then: circuit breaker around the cache call -> skip Redis entirely while it's open
```

**3. Name the second-order effects — this is the senior part:**
- **The database now takes 100% of read traffic.** If Redis was absorbing 95% of reads, that's a **20× spike** — the DB falls over seconds after the cache does. Mitigations: connection pool caps, per-endpoint rate limiting, request coalescing, a small in-process L1 cache, and load shedding of non-essential endpoints.
- **Recovery is its own stampede.** An empty cache coming back means every key misses at once. Warm the hottest keys, use jittered TTLs, and single-flight the rebuilds.
- **Degraded mode is a product decision.** "Search still works, personalised recommendations are hidden" is a better outcome than an error page — but somebody has to have decided that in advance.

---

# 3. Scaling

## Stateless servers and the sticky-session smell

**Q: Why must app servers be stateless?**

A: Because every scaling and reliability mechanism assumes any instance can serve any request: horizontal autoscaling, rolling deploys, a pod dying, a load balancer rerouting. Local state means a request that lands on the wrong instance is wrong or lost.

**Move state to:** the client (JWT), a shared store (Redis for sessions/cache), or the database. What may stay local: an L1 cache with a short TTL (an *optimisation*, correct if lost), and connection pools.

**Q: Why are sticky sessions a smell?**
- They **defeat load balancing** — a hot instance keeps the same users; a new instance gets no traffic.
- They **break deploys and autoscaling** — draining an instance drops its sessions; scale-in loses users.
- **Failure becomes user-visible** — one crashed pod = those users logged out.
- They **hide the real bug**: state that should have been externalised.

**Where they're defensible (be fair):** WebSocket/SignalR connections are inherently sticky for the connection's lifetime — but that's a *long-lived connection*, not session state, and the right fix for multi-instance SignalR is a **Redis backplane**, not affinity. See [[13-Real-Time-Communication|Real-Time Communication]]. Also legacy in-proc session state you haven't migrated yet — call that debt, not design.

## Read replicas and replication lag

**Q: You add read replicas. What breaks?**

A: **Replication lag.** Replicas are asynchronous; they're behind the primary by milliseconds normally and by seconds under write bursts, long transactions, index builds, or vacuum. So:

```text
POST /profile      -> writes to PRIMARY
GET  /profile      -> reads from REPLICA (50ms behind)
                   -> user sees their OLD name and reports a bug
```

**Q: How do you get read-your-own-writes?**

| Strategy | How | Cost |
|---|---|---|
| **Route writes' owner to the primary** | after a user writes, read from primary for the next N seconds (flag in session/cookie) | simple, effective, slightly more primary load — **the usual answer** |
| **Per-operation routing** | anything in the write path or "critical read" (checkout, balance) always uses primary; browsing uses replicas | explicit and easy to reason about |
| **Consistency token (LSN/GTID)** | client carries the write position; the replica waits until it has caught up | precise; needs DB support and plumbing |
| **Monitor and cap lag** | pull a replica out of rotation above a lag threshold | necessary regardless |

**Also state:** replicas do **not** scale writes — only reads. Every write still lands on the primary and is *also* replayed on every replica, so replicas don't reduce write work at all. When writes are the bottleneck, the answers are sharding, batching, or moving work off the OLTP database.

## Connection pool exhaustion and PgBouncer

**Q: "Timeout expired. The timeout period elapsed prior to obtaining a connection from the pool." — diagnose it.**

A: Every connection in the pool is checked out; new requests wait and then time out. Causes, in order of likelihood:

1. **Long-running work while holding a connection** — an HTTP call inside a transaction, a slow query, `await`-ing something unrelated between opening and closing.
2. **Leaked connections** — a `DbContext`/`SqlConnection` not disposed (resolved from the root container, or created manually), so it's returned only at GC.
3. **Sync-over-async** — blocked threads can't complete the work that would return connections. See [[04-CSharp-Fundamentals#Sync-over-async and deadlocks|sync-over-async]].
4. **Genuine concurrency** exceeding `Max Pool Size` (default **100** in SqlClient/Npgsql, *per process, per connection string*).
5. **N+1 queries** multiplying the connection-seconds each request needs.

**The arithmetic to say out loud:** "Pool size is **per pod**. 20 pods × 100 = **2,000** connections at the database. Postgres allocates a *process* per connection (~5–10 MB each) and starts thrashing well before that — `max_connections` is often 100–500. So the pods must be capped, or you put a pooler in front."

**PgBouncer** — a lightweight connection pooler in front of Postgres, multiplexing thousands of client connections onto a few dozen server connections:

| Mode | Behaviour | Caveat |
|---|---|---|
| `session` | one server connection per client session | barely helps |
| **`transaction`** | server connection returned to the pool **after each transaction** | **the useful mode**, and the one with rules |
| `statement` | returned after each statement | breaks multi-statement transactions |

**Transaction-mode caveats to name:** no session state survives between transactions — **server-side prepared statements** (Npgsql prepares by default; set `No Reset On Close`/`Max Auto Prepare=0` or use PgBouncer ≥1.21 which tracks them), **`SET` / session GUCs**, **advisory locks**, **`LISTEN/NOTIFY`**, and **temp tables** all break or leak across clients. Also: PgBouncer is another hop and another single point of failure — run it HA.

## Partitioning and sharding

**Q: When would you shard, and what does it cost?**

**Shard only when a single primary genuinely can't cope — after you've exhausted:** indexing and query tuning · read replicas · caching · archiving cold data · vertical scaling (a modern box handles far more than people assume) · **table partitioning** (one database, split by range/list — gets you cheap purges and smaller indexes without any of the distributed pain).

**Then:** shard when **writes** or **dataset size** exceed one node — not because "it's web scale".

**The pain, named honestly:**
- **Cross-shard queries** — no joins across shards; you scatter-gather in the app and merge. Anything global (search, reporting) needs a separate store.
- **No cross-shard transactions** — you're in saga territory for anything spanning two shards.
- **Rebalancing** — adding a shard with `hash(id) % N` remaps almost everything. Use **consistent hashing** or a **directory/lookup service** mapping tenant → shard.
- **Hot shards** — one huge tenant, or a shard key with skew (country, status, `created_at`). Choose a key with even distribution *and* the one you filter by most.
- **Global uniqueness and IDs** — no shared sequence; use UUIDv7 / ULID / Snowflake so IDs stay sortable.
- **Operations multiply** — migrations, backups, restores, and monitoring, times N.

**Choosing the key:** by tenant (natural for B2B, but tenants are uneven), by user ID (even, but everything must carry the user), by hash (even, no range queries), by range/time (great for time-series, guarantees a hot shard for "now").

---

# 4. Consistency

## Eventual consistency in practice

**Q: What does eventual consistency mean for the people using the system?**

A: "If writes stop, all replicas eventually converge" — but *practice* is about the window in between:

- **The UI must be designed for it.** "Your order is being processed" instead of showing a list that doesn't contain the order yet. Optimistic UI plus a reconciliation path.
- **Consumers arrive out of order and more than once** → project idempotently, use version numbers, and ignore events older than the state you already have.
- **Monotonic reads**: a user must never see data go *backwards* (present, then absent). Pin a user to one replica or one read source for a session.
- **Bound the window and monitor it.** "Eventually" must have a number — p99 lag < 2s — with an alert, or it's not an SLA, it's a hope.
- **Not everything gets to be eventual.** Uniqueness ("one booking per seat", "unique email") and money need a strong boundary: one aggregate, one transaction, one unique constraint.

## Saga orchestration vs choreography

**Q: How do you handle a transaction spanning services?**

A: You don't — a distributed transaction across services means shared locks and coupled availability. You use a **saga**: a sequence of *local* transactions, each with a **compensating action** if a later step fails.

| | **Orchestration** | **Choreography** |
|---|---|---|
| Flow | a coordinator tells each service what to do next | each service reacts to events and emits its own |
| Visibility | **the whole flow is in one place** — readable, testable | emergent; you reconstruct it from logs and tracing |
| Coupling | services are simple; the orchestrator knows everyone | services are independent; no central knowledge |
| Change | edit the state machine | change the listeners — and hope you found them all |
| Failure/compensation | explicit and centralised | each service must know how to compensate |
| Risk | orchestrator becomes a god service / SPOF | **cyclic event chains**, nobody can answer "why did this happen?" |
| Fits | complex multi-step flows (**checkout, booking, onboarding**) | simple 2–3 step reactions (order placed → send email) |

**The answer:** "Choreography for simple fan-out; **orchestration** the moment there are more than ~3 steps or any compensation, because at that point the *process itself* is a business asset and it deserves to exist explicitly in code — a MassTransit state machine — rather than being implied by who happens to subscribe to what."

**Compensating actions** — the point candidates miss: compensation is **semantic, not a rollback**. You cannot un-send an email or un-charge a card invisibly; you send an apology and issue a **refund**, which is a new transaction that appears in the ledger. Compensations must be **idempotent and retryable**, they can **fail** (needing a dead-letter/manual path), and some steps are **irreversible** — so order the saga to do reversible and risky work first and irreversible work last (reserve inventory → authorise payment → **capture** payment → ship).

```csharp
// Booking saga, orchestrated
Reserve seat (hold, TTL 10 min)  ->  Authorise payment  ->  Capture  ->  Confirm booking
      |                                    |                   |
 release hold                        void authorisation      refund      <- compensations
```

---

## Failure-Mode Drill

The interviewer's favourite format. Answer in the shape **detect → contain → degrade → recover**.

| "What happens when…" | The answer |
|---|---|
| **Redis is down?** | Fail open for cache reads (miss → DB), fail closed for locks/sessions. Short timeouts + a circuit breaker so we don't wait on a dead cache. Then brace the DB for the full read load, and warm with jittered TTLs on recovery. |
| **The broker is down?** | Publishing fails → the outbox retains the messages, so nothing is lost and business writes still commit. Consumers idle. On recovery the relay drains the backlog — expect a burst, so bound concurrency. |
| **A consumer keeps failing?** | Bounded retries with backoff+jitter → DLQ with the failure context → alert on DLQ depth → fix → replay. Distinguish poison from downstream-down. |
| **A downstream API is slow (not down)?** | Worse than down: threads and connections pile up. Timeouts, bulkhead, circuit breaker, then fallback or fail fast. |
| **The DB primary fails over?** | In-flight transactions are lost → the app must retry transient errors; connection strings must point at a listener/DNS. Uncommitted work is genuinely gone — idempotency keys make the client's retry safe. |
| **A replica lags 30s?** | Pull it from rotation on a lag threshold; route critical and read-your-own-writes traffic to the primary. |
| **A pod is OOM-killed mid-processing?** | The message wasn't acked → redelivery → at-least-once → the inbox dedupe makes it harmless. Any post-commit work not in the outbox is lost — that's why it's in the outbox. |
| **Traffic 10×'s in a minute?** | Rate limit at the edge, shed non-essential load, queue-based load levelling for writes, autoscale on queue depth (not CPU — it lags). Name the bottleneck you'd hit first: usually DB connections. |
| **Two users book the last seat simultaneously?** | Not a caching or locking problem — a **database** one: unique constraint on `(EventId, SeatId)`, or `SELECT ... FOR UPDATE` on the seat row. One wins, the other gets a clean 409. See [[16-System-Design\|the booking design]]. |
