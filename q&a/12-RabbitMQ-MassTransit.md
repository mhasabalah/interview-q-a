---
title: RabbitMQ & MassTransit
aliases: [RabbitMQ, MassTransit]
tags: [messaging, rabbitmq, masstransit, interview]
order: 12
---

# RabbitMQ & MassTransit Interview Questions & Answers

> [!info]+ Related Notes
> [[11-Module-Communication|Module Communication]] · [[16-System-Design|System Design]]

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
