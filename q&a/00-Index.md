---
title: Q&A Index
aliases: [Index, MOC, Interview Q&A]
tags: [moc, interview]
---

# Interview Q&A — Map of Content


A structured path through the interview-prep notes, grouped by theme and ordered for study. Each note has a **Related Notes** callout linking it to neighboring topics.

## Language & OOP Fundamentals
1. [[01-OOP-Principles|OOP Principles]]
2. [[02-SOLID-Principles|SOLID Principles]]
3. [[03-Design-Patterns|Design Patterns]]
4. [[04-CSharp-Fundamentals|C# Fundamentals]]
5. [[05-Data-Structures-Algorithms|Data Structures & Algorithms]]

## Data
6. [[06-Database|Database]] — fundamentals (73 Q&A: normalization, joins, ACID, index basics)
21. [[21-Database-Part-2|Database — Part 2 (Senior Depth)]] — concurrency & isolation, execution plans, zero-downtime migrations, EF Core, operations

## Architecture
7. [[07-Domain-Driven-Design|Domain-Driven Design]] — [[07-Domain-Driven-Design#Part 1 — Strategic Design|strategic]] (subdomains, bounded contexts, context maps, EventStorming, the design method) then [[07-Domain-Driven-Design#Part 2 — Tactical Design|tactical]] (entities, aggregates, events)
8. [[08-Clean-Architecture|Clean Architecture]]
9. [[09-Onion-Architecture|Onion Architecture]]
19. [[19-Modular-Monolith|Modular Monolith]] — the default topology: module rules, schema per module, boundary enforcement, extraction recipe
20. [[20-Choosing-An-Architecture|Choosing an Architecture]] — **all styles compared**, what a senior picks, what to start with, and every migration path

## Cross-Cutting & Communication
10. [[10-Middlewares|ASP.NET Core Middlewares]]
11. [[11-Module-Communication|Module Communication]]
12. [[12-RabbitMQ-MassTransit|RabbitMQ & MassTransit]]
13. [[13-Real-Time-Communication|Real-Time Communication]]
22. [[22-Event-Sourcing-And-EDA|Event Sourcing & Event-Driven Architecture]] — EDA's three flavours, rehydration, expected-version concurrency, projections, EventStoreDB, and when NOT to event source

## DevOps & Cloud
14. [[14-CI-CD|CI/CD]]
15. [[15-Azure-Cloud|Azure Cloud]]
23. [[23-Observability|Observability]] — logs/metrics/traces, OpenTelemetry, trace propagation across the broker, sampling, health checks, alerting on symptoms

## Senior Defense
17. [[17-Architecture-Defense|Architecture Defense]] — vertical slice vs Clean, MediatR, repository over EF Core, CQRS spectrum, DDD tactical, domain vs integration events
18. [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]] — idempotency, outbox, retries/backoff/jitter, DLQ, caching & Redis, scaling, saga

## Capstone
16. [[16-System-Design|System Design]] — includes [[16-System-Design#41. The design round — the framework that scores you|the design-round framework]] and [[16-System-Design#42. Design a booking system for 10k concurrent users|the booking system walkthrough]]

---

## Final-Week Sprint

The last days are not for new material — they're for **saying answers out loud**. Notes 17, 18 and §41–42 of 16 are written as *spoken* answers, not reference material.

| Day   | Focus                               | Notes                                                                                                                                                           | Done when you can…                                                                                |
| ----- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 1–2   | Language depth                      | [[04-CSharp-Fundamentals\|C# Fundamentals]]                                                                                                                     | answer the 20-question rapid-fire drill without looking                                           |
| 3     | OOP / SOLID / patterns              | [[01-OOP-Principles\|OOP]] · [[02-SOLID-Principles\|SOLID]] · [[03-Design-Patterns\|Patterns]]                                                                  | name a pattern you used **and** its cost                                                          |
| 4     | Data                                | [[06-Database\|Database]] · **[[21-Database-Part-2\|Database Part 2]]**                                                                                                                                       | explain an execution plan and an index choice                                                     |
| 5     | Messaging & modules                 | [[11-Module-Communication\|Module Communication]] · [[12-RabbitMQ-MassTransit\|RabbitMQ]] · **[[22-Event-Sourcing-And-EDA\|Event Sourcing & EDA]]** | explain at-least-once and what it forces on consumers                                             |
| **6** | **Defending your own architecture** | **[[17-Architecture-Defense\|Architecture Defense]]** · [[20-Choosing-An-Architecture\|Choosing an Architecture]] · [[19-Modular-Monolith\|Modular Monolith]] | give an **opinion + cost + when I'd choose otherwise** for VSA, MediatR, repository, CQRS, events — and name your default topology plus the driver that would change it |
| **7** | **Distributed systems**             | **[[18-Distributed-Systems-Reliability\|Distributed Systems & Reliability]]** · [[23-Observability\|Observability]] | answer the failure-mode drill cold: "what happens when Redis / the broker / the primary is down?" |
| 8     | Design round                        | [[16-System-Design#41. The design round — the framework that scores you\|§41]] + [[16-System-Design#42. Design a booking system for 10k concurrent users\|§42]] | run the booking design **out loud in 40 min**, talking continuously                               |
| 9     | Weak spots                          | whatever you stumbled on                                                                                                                                        | fix the two answers that came out worst                                                           |
| 10    | Light review                        | rapid-fire tables in 04, 17, 18                                                                                                                                 | rest — no new material                                                                            |
