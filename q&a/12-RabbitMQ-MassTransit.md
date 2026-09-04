---
title: RabbitMQ & MassTransit
aliases: [RabbitMQ, MassTransit]
tags: [messaging, rabbitmq, masstransit, interview]
order: 12
---

# RabbitMQ & MassTransit Interview Questions & Answers

> [!info]+ Related Notes
> [[11-Module-Communication|Module Communication]] · [[16-System-Design|System Design]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]] · [[22-Event-Sourcing-And-EDA|Event Sourcing & EDA]] · [[23-Observability|Observability]]

> [!tip] Going deeper
> Delivery guarantees, the retry ladder (immediate → delayed → DLQ), poison-vs-downstream-down, the outbox/inbox pair, and **Hangfire vs a real broker** are covered in [[18-Distributed-Systems-Reliability#1. Reliability Primitives|Distributed Systems & Reliability]].

## What is RabbitMQ?
**Answer:** RabbitMQ is an open-source message broker implementing AMQP (Advanced Message Queuing Protocol) for asynchronous communication between distributed systems using queues, exchanges, and routing.

## What is MassTransit?
**Answer:** MassTransit is a .NET distributed application framework that abstracts message transport (RabbitMQ, Azure Service Bus, Amazon SQS) with features like sagas, scheduling, and retry policies.

## What are the key components of RabbitMQ?
**Answer:**
- **Producer:** Sends messages
- **Exchange:** Routes messages based on rules
- **Queue:** Stores messages until consumed
- **Consumer:** Receives messages
- **Binding:** Links exchange to queue with routing key

## What are the types of exchanges in RabbitMQ?
**Answer:**
- **Direct:** Routes by exact routing key match
- **Fanout:** Broadcasts to all bound queues
- **Topic:** Routes by pattern matching (wildcards)
- **Headers:** Routes by message header attributes

## What is the difference between Queue and Topic?
**Answer:**
- **Queue:** Point-to-point, one consumer processes each message
- **Topic (Publish-Subscribe):** Multiple consumers receive copies of each message via fanout or topic exchanges

## What is message acknowledgment?
**Answer:** Message acknowledgment confirms the consumer successfully processed the message. Manual ack requires explicit confirmation; auto-ack acknowledges immediately upon delivery.

## What is a Dead Letter Exchange (DLX)?
**Answer:** A DLX handles messages that cannot be delivered or processed (rejected, expired, queue full). Messages route to a dead-letter queue for inspection or reprocessing.

## What is message durability?
**Answer:** Durable messages persist to disk, surviving broker restarts. Requires both durable queues and persistent message delivery mode.

## What is prefetch count?
**Answer:** Prefetch count limits how many unacknowledged messages a consumer can receive, preventing overwhelming slow consumers and ensuring fair distribution.

## How do you implement retry logic in MassTransit?
**Answer:**
```csharp
cfg.ReceiveEndpoint("order-queue", e =>
{
    e.UseMessageRetry(r => r.Intervals(
        TimeSpan.FromSeconds(5),
        TimeSpan.FromSeconds(15),
        TimeSpan.FromSeconds(30)
    ));
    e.ConfigureConsumer<OrderConsumer>(context);
});
```

## What is a saga in MassTransit?
**Answer:** A saga is a long-running stateful workflow coordinating multiple services in a distributed transaction. It maintains state across events and handles compensation for failures.

## How do you implement a saga?
**Answer:**
```csharp
public class OrderStateMachine : MassTransitStateMachine<OrderState>
{
    public State Submitted { get; private set; }
    public State Completed { get; private set; }
    
    public Event<OrderSubmitted> OrderSubmitted { get; private set; }
    public Event<OrderCompleted> OrderCompleted { get; private set; }

    public OrderStateMachine()
    {
        InstanceState(x => x.CurrentState);

        Event(() => OrderSubmitted);
        Event(() => OrderCompleted);

        Initially(
            When(OrderSubmitted)
                .TransitionTo(Submitted));

        During(Submitted,
            When(OrderCompleted)
                .TransitionTo(Completed));
    }
}
```

## What is the difference between Send and Publish in MassTransit?
**Answer:**
- **Send:** Point-to-point to a specific endpoint (queue)
- **Publish:** Broadcast to all subscribers (topic/exchange)

## How do you configure MassTransit with RabbitMQ?
**Answer:**
```csharp
services.AddMassTransit(x =>
{
    x.AddConsumer<OrderConsumer>();

    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.Host("rabbitmq://localhost", h =>
        {
            h.Username("guest");
            h.Password("guest");
        });

        cfg.ReceiveEndpoint("order-queue", e =>
        {
            e.ConfigureConsumer<OrderConsumer>(context);
        });
    });
});
```

## What is a consumer in MassTransit?
**Answer:** A consumer processes messages from a queue:
```csharp
public class OrderConsumer : IConsumer<OrderMessage>
{
    public async Task Consume(ConsumeContext<OrderMessage> context)
    {
        var order = context.Message;
        // Process order
        await context.Publish(new OrderProcessed { OrderId = order.Id });
    }
}
```

## What is idempotency in messaging?
**Answer:** Idempotency ensures processing the same message multiple times produces the same result. Implement using unique message IDs and deduplication logic.

## What is the Outbox Pattern?
**Answer:** The Outbox Pattern stores messages in a database transaction with business data, then reliably publishes them, ensuring atomicity between database changes and message publishing.

## How do you implement the Outbox Pattern in MassTransit?
**Answer:**
```csharp
services.AddMassTransit(x =>
{
    x.AddEntityFrameworkOutbox<OrderDbContext>(o =>
    {
        o.UseSqlServer();
        o.UseBusOutbox();
    });
});
```

## What is message routing?
**Answer:** Message routing determines how messages flow from producers to consumers using exchanges, routing keys, and bindings in RabbitMQ.

## What is a competing consumer pattern?
**Answer:** Multiple consumers read from the same queue, distributing workload for parallel processing and scalability. RabbitMQ round-robins messages among consumers.

## What is request-response pattern in MassTransit?
**Answer:**
```csharp
// Client
var response = await client.GetResponse<OrderResponse>(new OrderRequest { Id = 1 });

// Consumer
public class OrderRequestConsumer : IConsumer<OrderRequest>
{
    public async Task Consume(ConsumeContext<OrderRequest> context)
    {
        await context.RespondAsync(new OrderResponse { Status = "Completed" });
    }
}
```

## What is message TTL (Time-To-Live)?
**Answer:** TTL defines how long a message stays in a queue before expiration. Expired messages route to a DLX or are discarded.

## What is circuit breaker in messaging?
**Answer:** Circuit breaker stops sending messages to a failing service temporarily, preventing cascading failures. MassTransit supports circuit breaker policies.

## How do you handle poison messages?
**Answer:** Poison messages repeatedly fail processing. Handle with retry limits, dead-letter queues, and error monitoring. Move to a separate queue for manual inspection.

## What is message priority?
**Answer:** RabbitMQ supports priority queues where higher-priority messages are delivered first, useful for urgent tasks.

## What is lazy queue in RabbitMQ?
**Answer:** Lazy queues move messages to disk immediately, reducing memory usage for large queues at the cost of slight latency.

## How do you implement scheduled messages in MassTransit?
**Answer:**
```csharp
await scheduler.ScheduleMessage(
    DateTime.UtcNow.AddMinutes(5),
    new OrderReminder { OrderId = 123 });
```

## What is the difference between transient and persistent messages?
**Answer:**
- **Transient:** Stored in memory, lost on broker restart
- **Persistent:** Written to disk, survives restarts

## What is publisher confirms?
**Answer:** Publisher confirms are RabbitMQ acknowledgments from broker to publisher that messages were received and routed, ensuring reliable publishing.

## How do you monitor RabbitMQ?
**Answer:** Use RabbitMQ Management UI, Prometheus exporters, or monitoring tools to track queue depth, message rates, consumer count, and connection status.

## What are virtual hosts in RabbitMQ?
**Answer:** Virtual hosts provide logical grouping and isolation of exchanges, queues, and bindings, enabling multi-tenancy within a single RabbitMQ instance.

---

# Senior Add-On — Azure Service Bus vs RabbitMQ

> [!danger] Why this section exists
> Your CV lists **both** RabbitMQ and Azure Service Bus. That guarantees the question **"you've used both — how did you choose?"** A feature list is the mid-level answer; the senior answer is a *decision* with a driver behind it.

## The comparison

| | **RabbitMQ** | **Azure Service Bus** |
|---|---|---|
| Model | **AMQP broker with exchanges** — you own the routing topology | **managed PaaS**: queues + topics/subscriptions with rules |
| Routing | exchange types (direct, topic, fanout, headers) + bindings | topic **subscriptions with SQL/correlation filters** |
| You operate | the cluster, disks, upgrades, HA policy, quorum queues | **nothing** — Microsoft runs it |
| Consume model | push via `basic.consume` + prefetch, ack/nack | **peek-lock** (lock, process, complete) or receive-and-delete |
| Retry/DLQ | you configure (MassTransit retry + DLX) | **built in**: `MaxDeliveryCount` → auto dead-letter, with a real DLQ per entity |
| Ordering | per queue | per queue, and **FIFO with sessions** |
| Dedupe | you implement (inbox) | **built-in duplicate detection** over a time window |
| Scheduling | plugin / MassTransit scheduler | **native scheduled + deferred messages** |
| Throughput | very high, low latency, cheap on your own metal | good, but **quota-shaped** and priced per operation/tier |
| Message size | large, tunable | 256 KB standard / **100 MB premium** |
| Cost model | infrastructure + your time | per-operation + tier; **premium is a real monthly number** |
| Best at | high throughput, complex routing, self-hosted, cost control | Azure-native, enterprise integration, low ops burden |

## Azure Service Bus concepts to name

- **Peek-lock** — the message is invisible to others while locked, and you `Complete`, `Abandon` (immediate retry), `DeadLetter` (explicit), or `Defer` it. If you crash, the **lock expires** and it's redelivered — that's the at-least-once mechanism. Long handlers need **lock renewal**, or the message reappears while you're still processing it and you get a duplicate.
- **`MaxDeliveryCount`** — after N deliveries it dead-letters automatically. No custom poison-message code needed, which is a genuine advantage over RabbitMQ.
- **Sessions** — FIFO plus per-session state, and a session is processed by exactly one consumer at a time. This is how you get **ordering per aggregate** without giving up parallelism (session id = aggregate id) — the strongest ASB feature and worth naming.
- **Duplicate detection** — a broker-side dedupe window keyed on `MessageId`. It reduces (never removes) the need for an idempotent consumer, because it can't see the *effects* of processing, only the message.
- **Topics + subscriptions with filters** — one publish, many subscriptions, each with its own SQL filter/rule, its own DLQ and its own delivery count. Server-side filtering rather than routing keys.
- **Scheduled & deferred messages** — native `ScheduledEnqueueTime`, and deferral for "I can't handle this yet, park it by sequence number".
- **Auto-forward, transactions across entities, geo-DR** — enterprise features worth knowing exist.

## RabbitMQ concepts that pair with them

Exchanges and bindings (routing lives in the topology, not in filters) · **prefetch** as your concurrency and fairness control · **quorum queues** for replicated durability (the modern default over mirrored classic queues) · **lazy queues** for huge backlogs on disk · **DLX** — you wire dead-lettering yourself · **shovel/federation** for cross-cluster links · publisher confirms for reliable publishing.

## The answer to "how did you choose?"

> *"They're not competing on features for me, they're competing on **who operates it**. Inside our own infrastructure — high throughput, complex routing, cost sensitive — RabbitMQ, because I control the topology and the per-message cost is effectively zero. Where the workload was already Azure-native and I wanted zero broker operations plus built-in dead-lettering, sessions and duplicate detection, Service Bus earned the price. MassTransit made that a **transport decision, not an architecture decision** — the consumers and contracts are identical, so the choice was reversible."*

Then volunteer the caveat, because it's the mature part: **the abstraction leaks where the guarantees differ.** Sessions, duplicate detection and native scheduling have no RabbitMQ equivalent, so anything that relies on them isn't portable. And regardless of broker, both are **at-least-once** — [[18-Distributed-Systems-Reliability#At-least-once, at-most-once, and why exactly-once is a lie|exactly-once delivery doesn't exist]], so idempotent consumers and the [[18-Distributed-Systems-Reliability#The transactional outbox|outbox]] are required either way.

**One more differentiator, if they push:** *"I don't put ordering requirements on the broker if I can avoid it. Sessions solve it in ASB, but the more portable answer is to make consumers order-insensitive with a version guard — then the broker choice never constrains the domain."*
