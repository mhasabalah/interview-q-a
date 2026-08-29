---
title: Database — Part 2 (Senior Depth)
aliases: [Database Part 2, Database Senior, Database Deep Dive, Isolation Levels, Execution Plans]
tags: [database, sql, performance, concurrency, ef-core, interview, senior]
order: 21
---

# Database — Part 2 (Senior Depth)

> [!info]+ Related Notes
> [[06-Database|Database (Part 1 — fundamentals)]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]] · [[16-System-Design|System Design]] · [[04-CSharp-Fundamentals|C# Fundamentals]] · [[07-Domain-Driven-Design|Domain-Driven Design]] · [[19-Modular-Monolith|Modular Monolith]]

> [!danger]+ What this note is, and why it exists
> [[06-Database|Part 1]] covers the **73 "what is X" questions** — normalization, joins, ACID, index basics. That's the *recall* round, and it's necessary but not sufficient: every mid-level candidate can define an index.
>
> This note is the **judgement** round. The senior database interview is almost entirely three questions in disguise:
>
> 1. **"This is slow — what do you do?"** → a repeatable diagnostic method, not a guess
> 2. **"Two users do this at the same time — what happens?"** → isolation, locking, MVCC, lost updates
> 3. **"How do you change this without downtime?"** → migrations, expand-contract, backfills
>
> Everything below is organised around those three. If you can only revise one part, make it **Part 1 (concurrency)** — it's the most common senior discriminator and the one candidates fake worst.

---

# Part 1 — Concurrency, Isolation & Locking

*(the biggest gap in most candidates, and the highest-yield thing here)*

## Isolation levels — by anomaly AND by implementation

**Q: Explain the isolation levels.** *(Part 1 answers this with four bullets. That's the mid-level answer. The senior answer has two dimensions.)*

**Dimension 1 — which anomalies are prevented:**

| Level | Dirty read | Non-repeatable read | Phantom | Lost update | Write skew |
|---|---|---|---|---|---|
| **Read Uncommitted** | ✗ possible | ✗ | ✗ | ✗ | ✗ |
| **Read Committed** *(default almost everywhere)* | ✓ prevented | ✗ | ✗ | ✗ | ✗ |
| **Repeatable Read** | ✓ | ✓ | ✗ (locking) / ✓ (snapshot) | ✓ | ✗ |
| **Snapshot** | ✓ | ✓ | ✓ | ✓ (first-updater-wins) | **✗** |
| **Serializable** | ✓ | ✓ | ✓ | ✓ | ✓ |

**Dimension 2 — *how* the engine achieves it, which is what actually changes your production behaviour:**

| | **Locking (pessimistic)** | **MVCC / row versioning (optimistic)** |
|---|---|---|
| Readers vs writers | **readers block writers, writers block readers** | **readers never block writers** — they read an older version |
| Cost | blocking, lock escalation, deadlocks | version storage (PG: dead tuples + vacuum; SQL Server: tempdb version store) |
| Failure mode | timeouts and deadlocks | **serialization/update-conflict errors you must retry** |
| Used by | SQL Server default (`READ COMMITTED` with locks) | **PostgreSQL always**, SQL Server with RCSI/Snapshot |

**The engine-specific facts worth knowing cold** — these are what separate "I read a blog" from "I've operated this":

- **PostgreSQL is MVCC end to end.** `READ COMMITTED` is the default. Its **`REPEATABLE READ` is actually snapshot isolation** — it *does* prevent phantoms, unlike the ANSI definition. Its `SERIALIZABLE` is **SSI** (Serializable Snapshot Isolation), which detects dangerous read/write patterns and **aborts a transaction with `40001`** — so *any* app using it must have a retry loop.
- **SQL Server defaults to lock-based `READ COMMITTED`** — which is why blocking is the classic SQL Server pathology. Turning on **RCSI** (`ALTER DATABASE … SET READ_COMMITTED_SNAPSHOT ON`) switches it to row versioning, so readers stop blocking writers. It's usually a huge win, and the cost is **tempdb** pressure. *(Azure SQL Database has RCSI on by default — a nice detail to drop.)*
- **`NOLOCK` is not "make it fast"** — it's `READ UNCOMMITTED`: dirty reads, **rows read twice or skipped entirely** during page splits. It is not a performance strategy; it's a correctness trade you're probably making by accident. The right fix is usually RCSI or an index.

> [!tip] The sentence that lands
> *"'What isolation level?' is only half the question — the other half is 'locking or MVCC?', because that decides whether my failure mode is **blocking and deadlocks** or **serialization errors I have to retry**. Those need completely different application code."*

---

## Lost updates and write skew — the two races that reach production

**Q: Two users edit the same record. What goes wrong?**

**The lost update** — a read-modify-write race that `READ COMMITTED` does *not* protect you from:

```sql
-- Both sessions run this "safe looking" code at the same time
BEGIN;
SELECT stock FROM products WHERE id = 1;   -- both read 10
-- application computes 10 - 1 = 9
UPDATE products SET stock = 9 WHERE id = 1;
COMMIT;
-- Two sales happened. Stock says 9. One sale silently vanished.
```

**Four correct fixes, in order of preference:**

```sql
-- 1) Make it atomic — the database does the arithmetic. Best: no lock, no retry, no race.
UPDATE products SET stock = stock - 1 WHERE id = 1 AND stock > 0;
--    rows affected = 0  =>  someone beat you  =>  409

-- 2) Optimistic concurrency — a version column (the app-level default, and EF Core's model)
UPDATE products SET stock = @new, version = version + 1
 WHERE id = 1 AND version = @versionIWasShown;
--    0 rows => stale => reload and retry, or tell the user

-- 3) Pessimistic lock — hold the row for the duration
SELECT * FROM products WHERE id = 1 FOR UPDATE;          -- Postgres
SELECT * FROM products WITH (UPDLOCK, ROWLOCK) WHERE id = 1;  -- SQL Server

-- 4) Raise the isolation level — correct, but the bluntest and most expensive tool
```

**Write skew** — the subtle one, and a genuine senior discriminator:

```sql
-- Rule: "at least one doctor must remain on call."  Two doctors go off duty simultaneously.
-- Session A                                  Session B
SELECT count(*) FROM oncall WHERE active;  -- 2      SELECT count(*) FROM oncall WHERE active;  -- 2
-- "fine, 2 > 1"                                     -- "fine, 2 > 1"
UPDATE oncall SET active=false WHERE id=1;           UPDATE oncall SET active=false WHERE id=2;
COMMIT;                                              COMMIT;
-- Nobody is on call. Neither transaction saw a conflict — they wrote DIFFERENT rows.
```

**Why it matters:** snapshot isolation and Postgres `REPEATABLE READ` do **not** prevent write skew, because there's no write-write conflict — each transaction read a *set* and wrote a *different row*. Only `SERIALIZABLE` (SSI) catches it. The practical alternatives: **materialise the constraint** into something the DB can enforce (a counter row you also update, a unique index, an exclusion constraint), or lock the set explicitly.

**Q: So how do you actually stop double-booking?** *(the question this always becomes)*
A: Not with a distributed lock, and not with a cache. Make the **database** the arbiter — a unique constraint or a conditional `UPDATE` whose `WHERE` clause *is* the check. One winner, a clean 409 for the loser. See the booking write path in [[16-System-Design#42. Design a booking system for 10k concurrent users|the booking design]] and the Redlock caveats in [[18-Distributed-Systems-Reliability#Redis specifics|Redis specifics]].

---

## EF Core: optimistic and pessimistic in practice

```csharp
// OPTIMISTIC — the default choice. A concurrency token; EF adds it to the WHERE clause.
public class Product
{
    public int Id { get; set; }
    public int Stock { get; set; }
    [Timestamp] public byte[] Version { get; set; } = default!;   // rowversion / xmin in PG
}

try
{
    product.Stock -= 1;
    await _db.SaveChangesAsync(ct);      // UPDATE ... WHERE Id=@id AND Version=@version
}
catch (DbUpdateConcurrencyException ex)
{
    var entry  = ex.Entries.Single();
    var current = await entry.GetDatabaseValuesAsync(ct);        // what's actually there now
    if (current is null) return Result.Failure(Errors.Deleted);  // someone deleted it

    entry.OriginalValues.SetValues(current);   // rebase, then decide:
    // - retry automatically (safe only if the operation is commutative, e.g. stock - 1)
    // - or surface a 409 and let the user re-decide  <- usually the honest answer
}

// PESSIMISTIC — only when you must serialise a read-decide-write you cannot express as one UPDATE
await using var tx = await _db.Database.BeginTransactionAsync(ct);
var row = await _db.Products.FromSql($"SELECT * FROM products WHERE id={id} FOR UPDATE")
                            .SingleAsync(ct);
// ... decide ...
await _db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);
```

**The rule to state:** *"Optimistic by default — it costs nothing when there's no contention, which is 99% of rows. Pessimistic only for genuinely hot rows where retries would thrash. And **never** hold either across a network call."*

---

## Deadlocks: cause, diagnosis, prevention

**Q: You're getting deadlocks in production. Walk me through it.**

A deadlock is a **cycle**, not slowness: A holds X and wants Y, B holds Y and wants X. The engine picks a victim and rolls it back (SQL Server `1205`, PostgreSQL `40P01`). Distinguish it immediately from **blocking** (one waits, no cycle, ends in a timeout) — conflating the two is a tell.

| Cause | Fix |
|---|---|
| **Inconsistent access order** — one path updates Order→Customer, another Customer→Order | **Always touch tables/rows in the same order.** The single most effective fix. |
| **Long transactions** holding locks while doing other work | shorten them; never hold a transaction across an HTTP call |
| **Missing index on a filter or FK** — the engine locks far more rows than it needs (or takes a table scan) | add the index; **a missing FK index is a classic deadlock source** on cascading updates/deletes |
| **Lock escalation** — SQL Server escalates to a table lock around ~5,000 locks in a statement | batch large `UPDATE`/`DELETE` into chunks |
| **Read-then-write patterns** under lock-based read committed | `UPDLOCK` on the read, or restructure into one atomic statement |

```csharp
// You cannot eliminate deadlocks entirely — so retry them. They are transient by definition.
// EF Core: EnableRetryOnFailure covers transient errors, BUT it will not retry a transaction
// you started yourself unless you wrap it in the execution strategy:
var strategy = _db.Database.CreateExecutionStrategy();
await strategy.ExecuteAsync(async () =>
{
    await using var tx = await _db.Database.BeginTransactionAsync(ct);
    await DoWorkAsync(ct);
    await _db.SaveChangesAsync(ct);
    await tx.CommitAsync(ct);
});
```

**How to diagnose:** SQL Server → the **deadlock graph** from Extended Events (`system_health` session already captures it) or trace flag 1222. PostgreSQL → the deadlock detail is in the server log with both statements. Both tell you the exact two statements and the lock order — which usually makes the fix obvious.

---

## Long transactions: the systemic killer

**Q: Why is "just wrap it in a transaction" dangerous?**

Because a transaction's cost isn't its own duration — it's what it does to **everything else**:

- **Locks are held to commit**, not to last-statement. Everyone else queues.
- **PostgreSQL: it holds back the `xmin` horizon**, so autovacuum cannot reclaim dead tuples *anywhere in the database*. One idle-in-transaction session bloats tables it never touched. (Set `idle_in_transaction_session_timeout`.)
- **SQL Server: the version store in tempdb grows** under RCSI/snapshot for as long as the oldest transaction lives.
- **Connections are held**, so the pool drains — see [[18-Distributed-Systems-Reliability#Connection pool exhaustion and PgBouncer|pool exhaustion]].
- **Replication lag grows**, because replicas must keep the data those snapshots need.
- Rollback of a huge transaction can take **longer than the work did**.

**The rules:** open the transaction as late as possible, commit as early as possible, **never** do I/O (HTTP, email, file, message publish) inside one — that's what the [[18-Distributed-Systems-Reliability#The transactional outbox|outbox]] is for — and batch big writes into chunks with a commit per chunk.

---

# Part 2 — Indexing, beyond the basics

## Clustered vs nonclustered vs heap

| | **Clustered index** | **Nonclustered index** | **Heap** |
|---|---|---|---|
| What it is | **the table itself**, stored in key order | a separate structure: key + pointer | a table with no clustered index |
| How many | one per table | many | — |
| Leaf contains | the whole row | key + `INCLUDE`d columns + row locator | — |
| Lookup cost | direct | may need a **key lookup** back to the table | RID lookup |

**PostgreSQL has no clustered indexes** — tables are heaps, every index is secondary, and the "clustered" concept exists only as a one-off `CLUSTER` command. That difference explains a lot of cross-engine advice that doesn't transfer, and knowing it is a good signal.

**Q: What makes a good clustered key?** Narrow, static, **ever-increasing**, and unique. Which leads directly to the classic:

> [!warning] The random-GUID primary key
> A `uniqueidentifier`/UUIDv4 clustered PK inserts into **random positions**, causing constant **page splits**, fragmentation, and a much larger buffer-cache footprint. Fix: a sequential/ordered ID — **UUIDv7**, ULID, `NEWSEQUENTIALID()`, or an `int`/`bigint` identity with the GUID as a separate unique column for external exposure. This comes up constantly and most candidates only know "GUIDs are big".

## Composite indexes and the leftmost prefix rule

```sql
CREATE INDEX ix ON orders (customer_id, status, created_at);

WHERE customer_id = 1                                    -- ✓ seek
WHERE customer_id = 1 AND status = 'Paid'                -- ✓ seek
WHERE customer_id = 1 AND status = 'Paid' AND created_at > @d  -- ✓ seek + range
WHERE status = 'Paid'                                    -- ✗ can't seek: not the leading column
WHERE customer_id = 1 AND created_at > @d                -- ~ partial: seeks on customer_id, then filters
```

**Column order rule:** **equality predicates first**, then the range/sort column last. An index on `(created_at, customer_id)` is nearly useless for `customer_id = 1 AND created_at > @d`, while `(customer_id, created_at)` is perfect. Being able to say *why* — the range column ends the useful ordering — is the answer they want.

## SARGability

**Q: The column is indexed but the query still scans. Why?**

Because the predicate isn't **SARGable** — you've wrapped the column in something, so the engine can't use the index's ordering:

```sql
-- ✗ index unusable                          -- ✓ SARGable rewrite
WHERE YEAR(created_at) = 2026                WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01'
WHERE UPPER(email) = 'A@B.COM'               WHERE email = 'a@b.com'   (or a case-insensitive collation / computed+indexed column)
WHERE total * 1.2 > 100                      WHERE total > 100 / 1.2
WHERE name LIKE '%smith'                     -- leading wildcard: no B-tree can help; full-text or a reversed computed column
WHERE CAST(id AS varchar) = '42'             WHERE id = 42
```

**The invisible one — implicit conversion.** An `nvarchar` parameter compared to a `varchar` column (or a string parameter against an `int` column) makes the engine convert **the column**, killing the seek. In the plan it shows as `CONVERT_IMPLICIT` with a warning. In EF Core this usually comes from a mismatched column type mapping — it's a very common real-world "why is this suddenly slow".

## Statistics and cardinality estimation

The optimiser is a **cost estimator driven by statistics** — a histogram of value distribution. Almost every catastrophic plan is a **cardinality misestimate**: it thought 10 rows, got 2 million, so it picked a nested loop and now runs 2 million seeks.

Causes worth naming: stale statistics after a bulk load · a skewed column where the histogram can't represent the distribution · **table variables** (assume 1 row, pre-2019 SQL Server) · multi-column correlation the optimiser assumes independent · local variables/`OPTION(RECOMPILE)` differences · a big `IN` list.

## Other index knowledge that reads as senior

- **Covering index / `INCLUDE`** — key columns are for *seeking and ordering*; included columns are payload that eliminates the **key lookup**. Don't put a wide column in the key just to cover.
- **Filtered / partial index** — `CREATE INDEX ... WHERE is_deleted = false` (PG) / `WHERE IsDeleted = 0` (SQL Server). Small, hot, and the correct answer to soft-delete bloat.
- **Index the FK columns.** Not automatic in SQL Server; a missing FK index causes scans on cascade and joins, and is a common deadlock source.
- **PostgreSQL index types** — `B-tree` (default), `Hash` (equality only), **`GIN`** (jsonb, arrays, full-text), **`GiST`** (geometry, ranges), **`BRIN`** (huge naturally-ordered tables — tiny index, e.g. append-only time series). Naming BRIN and GIN with their use case is a strong differentiator.
- **Finding the bad ones:** unused indexes (`sys.dm_db_index_usage_stats` / `pg_stat_user_indexes` with `idx_scan = 0`), duplicates and near-duplicates (a prefix of another index is redundant), and **missing-index DMVs are suggestions, not instructions** — they over-recommend wide `INCLUDE` lists.
- **Maintenance:** fragmentation matters far less on SSDs than the old advice claims; **out-of-date statistics matter more than fragmentation**. Rebuild vs reorganise, and `REINDEX CONCURRENTLY` in PG.

---

# Part 3 — Reading plans and fixing slow queries

## The method (say this before touching anything)

> [!tip] Answer "this query is slow" with a **process**, never a guess
> 1. **Reproduce and measure** — how slow, p50 or p99, always or sometimes, since when?
> 2. **Find the real offender** — `pg_stat_statements` / Query Store / wait stats. *Total* time matters more than worst single execution: a 50 ms query run 10,000×/min beats a 3 s report.
> 3. **Get the actual plan** — `EXPLAIN (ANALYZE, BUFFERS)` in PG, actual execution plan in SSMS. Not the estimated one.
> 4. **Compare estimated vs actual rows.** A big divergence = a statistics/estimation problem, and it explains most bad plans.
> 5. **Find the expensive operator** — scans on big tables, key lookups in a loop, spills to disk, a hash join with no memory.
> 6. **Fix the cause, in order:** the query shape (SARGability, N+1, `SELECT *`) → the index → statistics → the plan hint (last resort).
> 7. **Re-measure, and check you didn't slow the writes down.**

**Notice what's *not* first:** adding an index. Interviewers are listening for whether you diagnose or reach.

## Reading the plan

- **Estimated vs actual rows** — the single most informative number on the page.
- **Join algorithms and what they tell you:**

| Join | How it works | Good when | The smell |
|---|---|---|---|
| **Nested loop** | for each outer row, seek the inner | small outer set + **indexed** inner | huge outer row count → millions of seeks (usually a bad estimate) |
| **Hash** | build a hash table from one side, probe with the other | large, unsorted, unindexed inputs | **spills to tempdb/disk** when memory is short |
| **Merge** | both inputs sorted, walk together | both already sorted (indexes) | an explicit `Sort` feeding it = expensive |

- **Key/RID lookup in a loop** → the index isn't covering; add `INCLUDE`.
- **Sort / Hash spill warning** → memory grant too small (often caused by a bad estimate again).
- **Parallelism** — a plan going parallel is often a *symptom* of scanning too much.
- **Buffers (PG)**: `shared hit` vs `read` tells you cache vs disk — the honest measure of work done.

## Parameter sniffing

**Q: "It was fast yesterday and nothing changed."**

A: Classic **parameter sniffing** (SQL Server) / **generic plan** (PostgreSQL). The plan is compiled for the *first* parameter values and cached. Compile it for `customer_id = <a customer with 3 orders>` and you get a nested loop; reuse that plan for the customer with 3 million and it's a disaster — and vice versa.

**Fixes, in order of bluntness:** update statistics · `OPTION (RECOMPILE)` for a genuinely skewed query (costs CPU per execution) · `OPTIMIZE FOR UNKNOWN` (takes the average — good when no plan suits everyone) · split into separate queries/procs for the skewed cases · Query Store **plan forcing** as a stopgap. In PostgreSQL, the analogous control is `plan_cache_mode` (custom vs generic plans; PG switches to generic after ~5 executions).

Also on this list: **stale statistics after a bulk load**, an **index rebuild clearing the cache**, and **data growth crossing a tipping point** where a seek+lookup becomes worse than a scan.

## What to monitor

**PostgreSQL:** `pg_stat_statements` (total time, calls, mean, rows), `pg_stat_activity` (what's running now, `wait_event`, `state = idle in transaction` ← always check this), `pg_locks`, autovacuum lag, bloat, replication lag.
**SQL Server:** Query Store, wait statistics (`PAGEIOLATCH_*` = I/O, `LCK_M_*` = blocking, `CXPACKET` = parallelism, `RESOURCE_SEMAPHORE` = memory grants), `sys.dm_exec_requests`, blocked process report.

---

# Part 4 — Schema decisions a senior owns

**Q: Surrogate or natural key?**
A: **Surrogate** by default — natural keys change (email, phone, tax ID, ISBNs get reissued), and a changing PK cascades everywhere. Keep the natural key as a **unique constraint** so the database still enforces the business rule. Exception: pure join tables, where the composite of both FKs is the right PK.

**Q: Soft deletes — what do they cost?** *(a great "have you maintained a system?" question)*
- **Every query must remember the filter.** One forgotten `WHERE is_deleted = 0` is a data-leak bug. EF Core global query filters help — and then you must remember `IgnoreQueryFilters()` for admin views.
- **Unique constraints break**: a deleted `user@x.com` blocks re-registration. Fix with a **filtered unique index** (`WHERE is_deleted = false`) or include the deletion timestamp in the key.
- **Indexes and tables carry dead weight** forever; add filtered indexes and an archive job.
- **Foreign keys still point at "deleted" rows**, so the referential story gets fuzzy.
- **The alternative:** a real delete plus an audit/history table, or a `deleted_at` with a hard-delete retention job. **Have an opinion** and know why.

**Q: When is a JSON column right?** For genuinely open-ended, sparse, per-tenant or third-party payloads you don't query relationally — audit payloads, webhook bodies, user preferences. **Wrong** for anything you filter, join, sort or constrain. Both engines can index it (PG `jsonb` + GIN; SQL Server computed columns + index), but you've traded away constraints, typing and referential integrity. "JSON because the schema might change" is how you get an EAV table with extra steps.

**Q: Money and time?** Money is **`decimal`/`numeric`**, never `float` (binary floating point can't represent 0.1) — and store the currency next to it. Time is **UTC**, stored in `timestamptz` (PG) / `datetime2` + explicit UTC convention (SQL Server); keep the original time zone as a separate column **only if** the business needs to re-render local time (scheduling, compliance).

**Q: Multi-tenancy?** *(near-certain if the product is B2B SaaS)*

| Strategy | Isolation | Cost/scale | Noisy neighbour | Per-tenant restore | Use when |
|---|---|---|---|---|---|
| **Shared schema + `tenant_id`** | weakest — one bad `WHERE` leaks data | **cheapest**, one migration | yes | painful | most SaaS; default |
| **Schema per tenant** | better | migrations × N schemas | mostly | easier | tens–hundreds of tenants |
| **Database per tenant** | strongest | **most expensive**, N migrations, N connections | no | trivial | enterprise/regulated, few large tenants |

With the shared-schema model, the two non-negotiables: `tenant_id` **leading** in every composite index, and enforcement that isn't "developers remember" — an EF Core **global query filter**, or **row-level security** in the database. A hybrid (shared by default, dedicated DB for enterprise plans) is a very credible senior answer.

---

# Part 5 — Zero-downtime migrations

**Q: How do you change a schema on a live system with rolling deploys?**

The core insight: **during a deploy, old and new code run at the same time**, so *every* schema change must be compatible with both. That forces **expand → migrate → contract** (a.k.a. parallel change):

```text
1. EXPAND    add the new thing, nullable / with a default, no destructive change
             deploy code that WRITES BOTH old and new, READS old
2. BACKFILL  fill the new column/table in batches, off-peak, with a commit per batch
3. SWITCH    deploy code that READS new (still writing both)  <- verify here
4. CONTRACT  stop writing old; a later release drops the old column/table
```

**Q: Rename a column with zero downtime?** You don't rename — that's an atomic break. Add the new column, dual-write, backfill, switch reads, drop the old one. **Four deploys, no downtime.** Saying "you can't rename, you expand and contract" is the answer.

**The specific traps to name:**

| Change | Trap | Do this instead |
|---|---|---|
| `ADD COLUMN NOT NULL DEFAULT` | on older engines rewrites the whole table under an exclusive lock | PG 11+ is metadata-only for constant defaults; otherwise add nullable → backfill → set `NOT NULL` (PG 12+ can validate with `NOT VALID` + `VALIDATE`) |
| `CREATE INDEX` on a big table | takes a write-blocking lock | **`CREATE INDEX CONCURRENTLY`** (PG — slower, can leave an `INVALID` index to clean up) / `WITH (ONLINE = ON)` (SQL Server Enterprise) |
| Changing a column type | table rewrite | new column → dual-write → backfill → switch |
| Adding a FK | validates every existing row while locking | PG: `ADD CONSTRAINT ... NOT VALID` then `VALIDATE CONSTRAINT` (takes a weaker lock) |
| One giant `UPDATE`/`DELETE` | long transaction, lock escalation, huge WAL, replication lag | batch it: `LIMIT/TOP 5000` in a loop, commit each batch, small sleep |
| Migrations at app startup | N instances race; a failed migration takes down the deploy | run in the **pipeline** as a separate gated step, or elect a single runner |

**Also say:** migrations are **forward-only** in practice (a "down" script that drops a column deletes production data — the real rollback is a new forward migration), they're **code-reviewed like code**, and every one should be tested against a **restored production-sized copy**, because a migration that takes 200 ms on your laptop can take 40 minutes on 80 million rows.

---

# Part 6 — EF Core at senior level

| Topic | What to say |
|---|---|
| **Tracking** | `AsNoTracking()` for every read-only query — it skips building the change tracker and identity map. Use `AsNoTrackingWithIdentityResolution()` when the graph has duplicates you need de-duplicated. |
| **Split queries** | Multiple `Include`s of collections produce a **cartesian explosion**; `AsSplitQuery()` issues one query per collection. Trade-off: more round trips and **no longer a single consistent snapshot** unless wrapped in a transaction. |
| **Projection** | Project to a DTO with `Select` instead of loading entities — less data, no tracking, and the query can often be covered by an index. |
| **Bulk operations** | EF 7+ `ExecuteUpdateAsync`/`ExecuteDeleteAsync` — one SQL statement, **no change tracking, no domain events, no interceptors**. Fast, and it bypasses your domain model, so use it deliberately (housekeeping, backfills), not for business writes. |
| **N+1** | Comes from lazy loading or looping over a collection. Detect by logging SQL in tests or asserting the query count; fix with `Include`/projection. Part 1 covers the definition — the senior part is **detecting it automatically** rather than discovering it in prod. |
| **Compiled queries / pooling** | `EF.CompileAsyncQuery` for genuinely hot queries; `AddDbContextPool` to avoid re-creating the context. Both are measurable-but-modest — mention them as *after profiling*, not as defaults. |
| **Retries + transactions** | `EnableRetryOnFailure` will **throw** if you start your own transaction — you must wrap the whole unit in `CreateExecutionStrategy().ExecuteAsync(...)`. A very common production trip-up. |
| **Global query filters** | The right tool for soft delete and tenant isolation — with `IgnoreQueryFilters()` as the deliberate escape hatch. |
| **Value converters / owned types** | Map value objects (`Money`, `Address`) to columns without leaking EF into the domain — the bridge to [[07-Domain-Driven-Design#Part 2 — Tactical Design\|tactical DDD]]. |
| **Raw SQL** | `FromSql($"...")` interpolation is **parameterised** (safe); `FromSqlRaw` with string concatenation is an injection hole. Drop to Dapper/raw SQL for reporting, bulk, and window-function work — and say that choosing the right tool per query is a feature, not a failure. |

**Q: "EF Core is slow."**
A: *"EF Core is rarely the bottleneck — the SQL it was asked to generate usually is. In order: is it N+1? Is it loading entities where a projection would do? Is it tracking a read-only query? Is a `Contains` on a big list generating a monstrous `IN`? Is it a cartesian explosion from multiple includes? I look at the generated SQL and its plan first. If the ORM genuinely can't express it well — window functions, recursive CTEs, bulk merges — I use Dapper for that query and keep EF for the rest."*

---

# Part 7 — Operations, HA and recovery

**Backups:** know the shapes — **full / differential / transaction log** (SQL Server) and **base backup + WAL archiving** (PostgreSQL) — both enabling **point-in-time recovery**. Then the two numbers that matter, which is what the question is really about:

- **RPO** — how much data you can afford to lose (drives backup/log frequency and sync vs async replication).
- **RTO** — how long you can be down (drives HA topology, not backup frequency).

> **"A backup you have never restored is not a backup."** Restore drills, on a schedule, timed — that sentence alone marks operational experience. Also: keep backups **off-box and immutable** (ransomware), and know that logical backups (`pg_dump`) are not a PITR strategy.

**HA:** synchronous replication = zero data loss, higher write latency, and **the primary stalls if the replica is down** — versus asynchronous = fast, with a small loss window on failover. Automatic failover needs a **quorum/witness** to avoid split-brain, and the application needs retry logic plus a listener/DNS endpoint, because in-flight transactions are lost. Read replicas scale **reads only** — every write still lands on the primary ([[18-Distributed-Systems-Reliability#Read replicas and replication lag|replication lag and read-your-own-writes]]).

**Housekeeping that shows you've operated a system:** autovacuum tuning and table bloat (PG) · index and statistics maintenance · **archiving and retention** (partition by month, then `DROP PARTITION` instead of a `DELETE` that generates gigabytes of WAL) · capacity/growth monitoring before the disk fills · connection limits and pooling.

---

# Part 8 — SQL a senior should be able to write

```sql
-- 1) KEYSET PAGINATION (deep OFFSET degrades linearly and skips rows when data shifts)
SELECT id, created_at, total FROM orders
 WHERE (created_at, id) < (@lastCreatedAt, @lastId)      -- the cursor
 ORDER BY created_at DESC, id DESC
 LIMIT 20;                                                -- needs an index on (created_at, id)

-- 2) TOP-N PER GROUP (latest order per customer) — window function, not a correlated subquery
SELECT * FROM (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) AS rn
  FROM orders o
) t WHERE rn = 1;

-- 3) DE-DUPLICATE, keeping the earliest row
WITH d AS (
  SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at) AS rn FROM users
)
DELETE FROM users WHERE id IN (SELECT id FROM d WHERE rn > 1);

-- 4) RUNNING TOTAL / moving window
SELECT day, amount,
       SUM(amount) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running,
       AVG(amount) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)        AS avg_7d
FROM daily_sales;

-- 5) UPSERT
INSERT INTO stock (product_id, qty) VALUES (@id, @qty)          -- PostgreSQL
ON CONFLICT (product_id) DO UPDATE SET qty = stock.qty + EXCLUDED.qty;
-- SQL Server: MERGE exists but has well-documented correctness/concurrency pitfalls;
-- prefer UPDATE-then-conditional-INSERT inside a transaction with UPDLOCK/HOLDLOCK.

-- 6) BATCHED DELETE (never one giant statement)
DELETE FROM events WHERE id IN (SELECT id FROM events WHERE created_at < @cutoff LIMIT 5000);
-- loop until 0 rows affected; commit each batch
```

---

# Part 9 — Diagnostic scenarios

*(Answer with **evidence → hypothesis → fix → verify**, never a guess.)*

| Scenario | How to answer |
|---|---|
| **"The app is slow every morning at 9."** | Correlated with load, so look for a tipping point: cold cache after a nightly restart/failover, a maintenance job or backup still running, stale stats after an overnight ETL, or a batch job holding locks. Evidence first: wait stats and `pg_stat_activity`/`sys.dm_exec_requests` at 09:00. |
| **"This query was fast yesterday."** | Parameter sniffing / plan change, stale statistics after a load, data crossing a tipping point, or an index that got dropped or disabled. Compare the current plan to the historical one (Query Store makes this a two-minute answer). |
| **"Timeouts, but CPU and disk are idle."** | **Blocking**, not load. Find the head blocker (`pg_stat_activity` `wait_event`, or `sys.dm_exec_requests.blocking_session_id`). Very often one long `idle in transaction` session. Adjacent cause: [[04-CSharp-Fundamentals#Sync-over-async and deadlocks\|thread-pool starvation]] or [[18-Distributed-Systems-Reliability#Connection pool exhaustion and PgBouncer\|pool exhaustion]] in the app, which looks identical from the outside. |
| **"Writes got slow after we added reporting."** | Reporting queries on the primary: long snapshots holding versions/xmin, memory pressure evicting the hot cache, escalated locks. Fix: read replica, or a separate OLAP store — don't run analytics on OLTP. |
| **"Disk is filling up."** | PG: bloat from dead tuples because autovacuum can't keep up (usually a long transaction) or WAL accumulating because a replication slot is inactive. SQL Server: the log can't truncate (`log_reuse_wait_desc`) — often no log backups in FULL recovery, or an open transaction. Not "add disk". |
| **"Two users overwrote each other."** | Lost update. Reproduce, then fix at the right level: atomic `UPDATE`, or a concurrency token with a 409. Ask whether the same race exists elsewhere — it usually does. |

---

## Rapid-Fire Drill

| # | Probe | The one-line answer |
|---|---|---|
| 1 | Default isolation level? | `READ COMMITTED` in both PG and SQL Server — but PG does it with MVCC and SQL Server with locks unless RCSI is on. |
| 2 | What does RCSI change? | Readers stop blocking writers (row versioning); the cost is tempdb. |
| 3 | Is Postgres `REPEATABLE READ` the ANSI one? | No — it's snapshot isolation and it *does* prevent phantoms. |
| 4 | What does `SERIALIZABLE` in PG cost you? | `40001` serialization failures you must **retry** — SSI is optimistic. |
| 5 | Which anomaly does snapshot isolation miss? | **Write skew** — two transactions writing different rows after reading the same set. |
| 6 | Safest fix for a lost update? | Make it one atomic `UPDATE` whose `WHERE` is the check; rows-affected 0 means you lost. |
| 7 | `NOLOCK` for performance? | It's `READ UNCOMMITTED` — dirty reads, and rows read twice or skipped. Use RCSI or an index. |
| 8 | Fastest way to stop deadlocks? | **Consistent lock ordering**, shorter transactions, index the FK — then retry, since they're transient. |
| 9 | Deadlock vs blocking? | Deadlock = a cycle, one victim rolled back. Blocking = a queue, ends in a timeout. |
| 10 | Why are long transactions so costly in PG? | They hold back the `xmin` horizon, so autovacuum can't reclaim dead tuples anywhere — bloat plus replication lag. |
| 11 | Composite index column order? | Equality columns first, range/sort column last. Leftmost prefix rule. |
| 12 | Index exists but it scans — why? | Not SARGable (function/cast on the column), implicit conversion, or the estimate says most rows match anyway. |
| 13 | Most informative thing in a plan? | **Estimated vs actual rows.** Most bad plans are cardinality misestimates. |
| 14 | Nested loop with a huge outer set means? | The optimiser expected few rows — stale or skewed statistics. |
| 15 | "Fast yesterday, slow today"? | Parameter sniffing / plan change / stale stats / a data tipping point. |
| 16 | Random-GUID clustered PK? | Page splits and fragmentation. Use UUIDv7/ULID/sequential, or an identity PK with the GUID as a unique column. |
| 17 | Cost of soft deletes? | Every query needs the filter, unique constraints break, indexes carry dead rows. Filtered indexes + retention, or audit tables instead. |
| 18 | Rename a column with zero downtime? | You don't — expand/contract: add, dual-write, backfill, switch reads, drop. |
| 19 | Index on a big live table? | `CREATE INDEX CONCURRENTLY` (PG) / `ONLINE = ON` (SQL Server Enterprise). Never a plain blocking build. |
| 20 | Migrations at app startup? | No — instances race and a failure blocks the deploy. Run it as a gated pipeline step. |
| 21 | `ExecuteUpdate` vs `SaveChanges`? | One SQL statement, no tracking, **no domain events or interceptors** — great for housekeeping, wrong for business writes. |
| 22 | Why does `EnableRetryOnFailure` throw? | You started your own transaction — wrap the unit in `CreateExecutionStrategy().ExecuteAsync(...)`. |
| 23 | Multi-tenancy default? | Shared schema + `tenant_id` leading every index, enforced by a global query filter or RLS — not by developer memory. |
| 24 | RPO vs RTO? | How much data you can lose vs how long you can be down. They drive different decisions. |
| 25 | Is a backup a backup? | Only if you've **restored** it, on a schedule, timed. |
