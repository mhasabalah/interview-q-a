# MOHAMED HASABALAH

Software Engineer | .NET

New Cairo, Cairo, Egypt | +20 109 974 6971 | mohamedhasabalaah@gmail.com
linkedin.com/in/mohamed-hasabalah | github.com/mhasabalah

## Professional Summary

.NET engineer with 6+ years architecting enterprise ERP, logistics and real-estate platforms across Egypt and Saudi Arabia, currently decomposing a multi-team ERP monolith into independently deployable modules. Builds event-driven systems that hold under at-least-once delivery: schema-per-module boundaries, RabbitMQ and MassTransit messaging, transactional outbox, and idempotent consumers. Owns domains end to end, from DDD modelling and API design through Azure deployment, CI/CD, observability and production hardening.

## Technical Skills

Languages and Frameworks: C#, .NET 9/10, ASP.NET Core, Minimal APIs, REST APIs, Entity Framework Core, .NET Aspire, gRPC, SQL, Blazor, Vue.js, TypeScript

Architecture: Modular Monolith, Vertical Slice Architecture, Domain-Driven Design, CQRS (MediatR, FluentValidation), Event Sourcing, Clean Architecture, Event-Driven Architecture, Microservices

Distributed Systems: RabbitMQ, MassTransit, Azure Service Bus, Hangfire, Transactional Outbox, Inbox Pattern, Idempotent Consumers, Optimistic Concurrency, Saga Orchestration, Dead-Letter Queues, Retry with Backoff and Jitter, Redis

Cloud and DevOps: Azure (App Service, Functions, Service Bus, Key Vault, Application Insights), Bicep IaC, Docker, Docker Compose, GitHub Actions, GitHub Container Registry, Azure DevOps, CI/CD, Zero-Downtime Deployment

Data: PostgreSQL, SQL Server, Oracle, MongoDB, EventStoreDB, Redis, Query Tuning, Execution Plan Analysis, Indexing, Replication

Observability and Testing: OpenTelemetry, Prometheus, Grafana, Loki, Serilog, Seq, Application Insights, xUnit, NSubstitute, Testcontainers, Integration and E2E Testing

Security: Keycloak, OAuth2, OpenID Connect, JWT, Secrets Management

Practices: Agile, Scrum, Kanban, Code Review, Technical Mentoring

## Experience

### Software Engineer

MicrotecSaudi | Cairo, Egypt | Nov 2024 - Present

- Re-architected 6 core ERP modules from a shared-database monolith into independently deployable services with schema-per-module ownership and public contracts, eliminating cross-schema coupling.
- Replaced synchronous calls with an event-driven backbone on RabbitMQ, MassTransit and Azure Service Bus, using competing consumers, jittered backoff and dead-letter queues to prevent cascades.
- Moved 2 workloads, bulk imports and notification dispatch, onto Hangfire background jobs with retries and scheduled runs, so failures recover without blocking users.
- Operated the platform on 4 Azure services (App Service, Functions, Key Vault, Application Insights), with environments provisioned in Bicep and containers on Docker Compose.
- Cut new-report delivery from a release cycle to same-day configuration with a reporting service driven by runtime definitions, absorbing 15+ report requests a month.
- Owned Accounting and HR modules end to end, alongside the Blazor Admin Portal.
- Standardised UI across 6+ product teams with a reusable Blazor component and services package published as internal NuGet.
- Proved each module extraction safe before release with unit tests on domain logic and integration tests across boundaries.
- Set the review standard for module boundaries and messaging patterns, and mentored 6 engineers onboarding onto the distributed codebase.

### Software Engineer

MSDC | Cairo, Egypt | Sep 2023 - Oct 2024

- Modelled ERP domains with Domain-Driven Design using bounded contexts and aggregates that enforce their own invariants, then decomposed them into services over RabbitMQ.
- Cut month-end reporting from roughly 45 minutes to under 10 by rewriting the heaviest Oracle queries, correcting indexing and eliminating full scans.
- Automated document generation with QuestPDF across 10 document types, eliminating roughly 6 hours per week of manual report preparation.

### Software Engineer

EL-SAFA | Cairo, Egypt | Jun 2022 - Jun 2023

- Built a logistics platform across five modules covering policies, shipments, invoices and real-time tracking, processing 1,000+ invoices and 200+ shipments daily.
- Took releases from monthly and manual to several per week with CI/CD on GitHub Actions, removing a recurring source of production errors.
- Untangled a legacy codebase into clear service boundaries and made them part of the code-review standard, lowering the cost of every feature that followed.

### Software Engineer

INNOTECH | Tanta, Egypt | Mar 2020 - May 2022

- Built ASP.NET Core services and Blazor WebAssembly interfaces, modelling the SQL Server schema behind 25+ application features.
- Established code review as a team practice and standardised C# conventions across the codebase, raising consistency as the team grew.
- Owned features end to end, from data model and API through to UI, testing and deployment.

## Projects

### BateCom - Real-Estate Platform (.NET 9)

Product, delivery and operations.

- Built a real-estate marketplace across 6 modules (Properties, Developers, Agents, Subscriptions, Attachment, Identity) where developers and agents publish listings behind subscription billing.
- Offloaded listing imports and notification dispatch to Hangfire background jobs, keeping long-running work off the request path.
- Consolidated local development onto a .NET Aspire AppHost orchestrating 4 resources: API, PostgreSQL, Redis and Seq.
- Mirrored it in production with a 3-file Docker Compose split into core, observability and dev-only tooling, so environments never drift.
- Automated delivery with 7 GitHub Actions workflows on a self-hosted runner: tests, image publishing to GHCR, scheduled database backups, health monitoring and one-click rollback.
- Scripted zero-downtime releases with pre-deploy backup, deploy and rollback behind nginx TLS termination, with health checks reverting a bad release automatically.
- Hardened production with read-only Docker secrets, localhost-bound service ports behind nginx, and an internal-only database network.
- Instrumented with OpenTelemetry into 3 backends (Prometheus, Tempo, Loki), surfaced in Grafana alongside Serilog logging in Seq.

### Flight Booking Platform (.NET 10)

Data consistency and concurrency.

- Built an airline reservation system across 4 modules (Flight, Passenger, Booking, Identity), each owning its data and communicating over typed gRPC contracts.
- Separated read and write sides across 2 stores, PostgreSQL for writes and MongoDB for reads, kept current by integration events.
- Persisted the Booking aggregate to EventStoreDB as an append-only stream, giving a full audit trail and rebuildable projections.
- Prevented double-booked seats using EF Core optimistic concurrency on a row version, returning 409 Conflict on stale writes with an explicit client retry contract.
- Verified with integration tests running 3 real containers (PostgreSQL, MongoDB, EventStoreDB) through Testcontainers.

### Modular E-Commerce (.NET 8)

Messaging reliability and access control.

- Implemented the transactional outbox in 2 modules, Basket and Ordering, so a state change and its integration event commit atomically under at-least-once delivery.
- Made consumers idempotent through message deduplication, so a broker redelivery cannot place a duplicate order or double-apply a basket change.
- Secured the platform with Keycloak (OAuth2, OpenID Connect) and cut repeat catalogue reads with Redis caching on the hottest query paths.

## Education

Bachelor of Engineering, Computer Engineering and Automatic Control
Tanta University | Tanta, Egypt | 2018 - 2023
Graduated with Very Good honours.

## Languages

Arabic (Native) | English (Professional Working Proficiency)
