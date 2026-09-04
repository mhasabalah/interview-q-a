# LinkedIn profile — as applied 2026-08-30

Live at linkedin.com/in/mohamed-hasabalah. Source: `CV-Mohamed-Hasabalah-Senior-Software-Engineer.md`,
except employment dates, where LinkedIn's own record was treated as authoritative.

## Headline (152 chars)
Software Engineer @ MicrotecSaudi | .NET & Distributed Systems | ASP.NET Core · RabbitMQ · MassTransit · Azure · DDD | Enterprise ERP & Modular Monolith

## About
.NET engineer with 5+ years building enterprise ERP, real-estate and e-commerce platforms across Egypt and Saudi Arabia. I currently work on decomposing a multi-team ERP monolith into independently deployable modules — schema-per-module ownership, public contracts, and an event-driven backbone that holds under at-least-once delivery.

What I do day to day:

- Design module boundaries with Domain-Driven Design — bounded contexts and aggregates that enforce their own invariants, not anemic models behind a service layer.
- Build the messaging that connects them: RabbitMQ and MassTransit, Azure Service Bus, transactional outbox, idempotent consumers, dead-letter queues, retry with backoff and jitter.
- Own domains end to end — API design in ASP.NET Core and Minimal APIs, EF Core data modelling, background work on Hangfire, then Azure deployment, CI/CD and production hardening.
- Keep systems observable — OpenTelemetry into Prometheus, Grafana and Loki, plus Serilog, Seq and Application Insights.
- Prove changes safe before release — xUnit unit tests on domain logic and integration tests against real containers via Testcontainers.

Some results: cut month-end ERP reporting from roughly 45 minutes to under 10 by rewriting the heaviest Oracle queries and correcting indexing; reduced new-report delivery from a full release cycle to same-day configuration; established code review as a team practice that cut bugs by 15%.

Stack: C#, .NET 9/10, ASP.NET Core, EF Core, Blazor, Vue.js, TypeScript, gRPC, .NET Aspire | RabbitMQ, MassTransit, Azure Service Bus, Redis, Hangfire | PostgreSQL, SQL Server, Oracle, MongoDB, EventStoreDB | Azure, Docker, Bicep, GitHub Actions, Azure DevOps | OpenTelemetry, Grafana, Serilog, Seq | Keycloak, OAuth2, OpenID Connect

Open to .NET and backend engineering roles — hybrid in Cairo or the Gulf, or fully remote.

GitHub: github.com/mhasabalah

## What was applied
| Section | Change |
|---|---|
| Headline | replaced |
| About | replaced (was generic full-stack copy naming .NET Framework) |
| MicrotecSaudi | 9 bullets added (was empty), skills: Microservices, RabbitMQ, MassTransit |
| MSDC | 4 bullets replaced. Dates LEFT as Oct 2023 - Nov 2024 |
| iNNOTECH full-time | 5 bullets replaced. Dates untouched (Nov 2021 - Jul 2023) |
| iNNOTECH internship | 2 bullets polished. Kept, dates untouched (Aug 2021 - Nov 2021) |
| Skills | ~35 added, total now 74. NOTHING removed |
| Projects | 3 added (BateCom, Flight Booking, Modular E-Commerce). Total now 5 |
| Education | Field -> "Computer Engineering and Automatic Control"; Grade -> "Very Good (Honours)" |
| Freelancer.com | UNTOUCHED - user deletes personally |
| EL-SAFA | NOT added to LinkedIn (stays on CV only) |

"Share with your network" / "Notify network" was OFF for every edit - no notifications sent.

## Known divergence from the CV (deliberate)
- CV says iNNOTECH Mar 2020 - May 2022; LinkedIn says Aug 2021 - Jul 2023. User confirmed LinkedIn is correct.
  **The CV needs correcting.**
- CV says MSDC Sep 2023 - Oct 2024; LinkedIn left at Oct 2023 - Nov 2024.
- CV says "6+ years"; LinkedIn About says "5+ years" to match the visible Aug 2021 start.
- EL-SAFA (Jun 2022 - Jun 2023) is on the CV only.

## Skill-name notes
LinkedIn's taxonomy has no "Docker", "GitHub Actions", "CQRS" or "Event-Driven Architecture" entities.
Applied canonical equivalents: "Docker Products", "GitHub", "Command Query Responsibility Segregation", "Event-driven".
One stray entry, "CQS", was added before the correct CQRS entry was found - harmless, removable if wanted.

## Still open
- Featured section: pin GitHub + CV PDF (needs a public URL)
- Project repo links (media/URL) not attached
- Banner image is generic stock
- Activity is all reposts; no original technical posts
