---
title: Module Communication
aliases: [Module Communication, Inter-Module Communication]
tags: [architecture, microservices, interview]
order: 11
---

# Module Communication Interview Questions & Answers

> [!info]+ Related Notes
> [[12-RabbitMQ-MassTransit|RabbitMQ & MassTransit]] · [[13-Real-Time-Communication|Real-Time Communication]] · [[09-Onion-Architecture|Onion Architecture]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]] · [[17-Architecture-Defense|Architecture Defense]]

> [!tip] Going deeper
> For communication **between modules inside one deployable** — facades, in-process integration events shaped like broker messages, and why that makes extraction a transport swap — see [[19-Modular-Monolith#Communication between modules|Modular Monolith]].
>
> This note covers **what** each pattern is. For the senior follow-ups — *why dual-write is broken*, *why exactly-once delivery is a lie*, *backoff + jitter*, *DLQ and poison messages*, *idempotency keys and the inbox* — see [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]]. For *domain events vs integration events* and dispatch ordering, see [[17-Architecture-Defense#Domain events vs integration events|Architecture Defense]].

## What is inter-module communication?
**Answer:** Inter-module communication is the exchange of data and messages between different modules, services, or components in a distributed system using synchronous or asynchronous patterns.

## What is the difference between synchronous and asynchronous communication?
**Answer:**
- **Synchronous:** Caller waits for response (blocking), tight coupling, immediate response (HTTP, gRPC)
- **Asynchronous:** Caller doesn't wait (non-blocking), loose coupling, eventual consistency (messaging queues, events)

## When should you use synchronous communication?
**Answer:**
- Immediate response required
- Simple request-response operations
- Data consistency is critical
- Real-time validation needed
- Examples: User authentication, payment processing, querying data

## When should you use asynchronous communication?
**Answer:**
- Long-running operations
- Fire-and-forget scenarios
- High scalability needed
- Loose coupling required
- Examples: Email notifications, order processing, background jobs

## What is REST API communication?
**Answer:** REST is a synchronous HTTP-based communication using standard methods (GET, POST, PUT, DELETE) with JSON/XML payloads for resource manipulation.

```csharp
public class OrderService
{
    private readonly HttpClient _httpClient;

    public async Task<Product> GetProduct(int id)
    {
        var response = await _httpClient.GetAsync($"api/products/{id}");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<Product>();
    }
}
```

## What is gRPC?
**Answer:** gRPC is a high-performance, synchronous RPC framework using HTTP/2 and Protocol Buffers (binary serialization) for efficient service-to-service communication.

```protobuf
service ProductService {
    rpc GetProduct(ProductRequest) returns (ProductResponse);
}

message ProductRequest {
    int32 id = 1;
}

message ProductResponse {
    int32 id = 1;
    string name = 2;
    double price = 3;
}
```

## What are the advantages of gRPC over REST?
**Answer:**
- Faster (binary Protocol Buffers vs JSON)
- Strongly typed contracts
- Bidirectional streaming
- Built-in code generation
- HTTP/2 multiplexing

## What is message-based communication?
**Answer:** Message-based communication uses message brokers (RabbitMQ, Azure Service Bus) to send messages asynchronously between services with queues and topics.

```csharp
public class OrderCreatedEvent
{
    public int OrderId { get; set; }
    public DateTime CreatedAt { get; set; }
}

// Publisher
await _publishEndpoint.Publish(new OrderCreatedEvent 
{ 
    OrderId = 123, 
    CreatedAt = DateTime.UtcNow 
});

// Consumer
public class OrderCreatedConsumer : IConsumer<OrderCreatedEvent>
{
    public async Task Consume(ConsumeContext<OrderCreatedEvent> context)
    {
        var order = context.Message;
        // Process order
    }
}
```

## What is event-driven architecture?
**Answer:** Event-driven architecture uses events to trigger and communicate between services. Services publish events when state changes, and other services subscribe to react.

```csharp
public class OrderService
{
    private readonly IEventBus _eventBus;

    public async Task CreateOrder(OrderDto order)
    {
        // Save order
        await _repository.SaveAsync(order);

        // Publish event
        await _eventBus.PublishAsync(new OrderCreatedEvent 
        { 
            OrderId = order.Id 
        });
    }
}
```

## What is the difference between commands and events?
**Answer:**
- **Commands:** Direct instruction to do something, one handler, imperative (CreateOrder)
- **Events:** Something that happened, multiple handlers, past tense (OrderCreated)

## What is the Request-Response pattern?
**Answer:** Client sends a request and waits for a response. Used in synchronous communication.

```csharp
// Synchronous HTTP
var product = await _httpClient.GetFromJsonAsync<Product>($"api/products/{id}");

// Asynchronous messaging with reply
var response = await _requestClient.GetResponse<ProductResponse>(
    new GetProductRequest { Id = 123 });
```

## What is the Fire-and-Forget pattern?
**Answer:** Client sends a message without waiting for a response. Used for notifications and background processing.

```csharp
public async Task SendNotification(string email, string message)
{
    await _publishEndpoint.Publish(new SendEmailCommand
    {
        Email = email,
        Message = message
    });
    // Don't wait for email to be sent
}
```

## What is the Publish-Subscribe pattern?
**Answer:** Publisher broadcasts messages to multiple subscribers without knowing who they are, enabling loose coupling.

```csharp
// Publisher
await _publishEndpoint.Publish(new OrderShippedEvent { OrderId = 123 });

// Multiple subscribers
public class EmailNotificationConsumer : IConsumer<OrderShippedEvent> { }
public class SmsNotificationConsumer : IConsumer<OrderShippedEvent> { }
public class AnalyticsConsumer : IConsumer<OrderShippedEvent> { }
```

## What is the Point-to-Point pattern?
**Answer:** Message sent to a queue is consumed by exactly one consumer. Used for task distribution.

```csharp
// Send to specific queue
await _sendEndpoint.Send(new ProcessOrderCommand { OrderId = 123 });

// One consumer processes it
public class ProcessOrderConsumer : IConsumer<ProcessOrderCommand>
{
    public async Task Consume(ConsumeContext<ProcessOrderCommand> context)
    {
        // Process order
    }
}
```

## What is the Saga pattern?
**Answer:** Saga manages distributed transactions across services using choreography (events) or orchestration (central coordinator).

```csharp
// Choreography-based saga
public class OrderSaga :
    ISaga,
    InitiatedBy<OrderCreated>,
    Orchestrates<PaymentProcessed>,
    Orchestrates<InventoryReserved>
{
    public Guid CorrelationId { get; set; }
    
    public async Task Consume(ConsumeContext<OrderCreated> context)
    {
        // Start saga
        await context.Publish(new ProcessPayment { OrderId = context.Message.OrderId });
    }

    public async Task Consume(ConsumeContext<PaymentProcessed> context)
    {
        await context.Publish(new ReserveInventory { OrderId = context.Message.OrderId });
    }

    public async Task Consume(ConsumeContext<InventoryReserved> context)
    {
        // Complete saga
    }
}
```

## What is compensating transaction?
**Answer:** Compensating transaction undoes completed operations when a distributed transaction fails.

```csharp
public class OrderSaga : ISaga
{
    public async Task Consume(ConsumeContext<PaymentFailed> context)
    {
        // Compensate: Release inventory
        await context.Publish(new ReleaseInventory { OrderId = context.Message.OrderId });
        
        // Compensate: Cancel order
        await context.Publish(new CancelOrder { OrderId = context.Message.OrderId });
    }
}
```

## What is circuit breaker pattern?
**Answer:** Circuit breaker prevents calls to failing services, failing fast and allowing recovery time.

```csharp
public class ProductService
{
    private readonly IHttpClientFactory _httpClientFactory;

    public async Task<Product> GetProduct(int id)
    {
        var client = _httpClientFactory.CreateClient("ProductService");
        
        // Polly circuit breaker
        var response = await client.GetAsync($"api/products/{id}");
        return await response.Content.ReadFromJsonAsync<Product>();
    }
}

// Startup configuration
services.AddHttpClient("ProductService")
    .AddTransientHttpErrorPolicy(policy => 
        policy.CircuitBreakerAsync(5, TimeSpan.FromSeconds(30)));
```

## What is retry pattern?
**Answer:** Retry pattern automatically retries failed operations with configurable delays and attempts.

```csharp
// Polly retry policy
services.AddHttpClient("PaymentService")
    .AddTransientHttpErrorPolicy(policy => 
        policy.WaitAndRetryAsync(3, retryAttempt => 
            TimeSpan.FromSeconds(Math.Pow(2, retryAttempt))));

// MassTransit retry
cfg.ReceiveEndpoint("order-queue", e =>
{
    e.UseMessageRetry(r => r.Intervals(
        TimeSpan.FromSeconds(1),
        TimeSpan.FromSeconds(5),
        TimeSpan.FromSeconds(10)
    ));
});
```

## What is the Outbox pattern?
**Answer:** Outbox pattern ensures atomicity between database operations and message publishing by storing messages in the database and publishing them later.

```csharp
public class OrderService
{
    private readonly OrderDbContext _context;

    public async Task CreateOrder(Order order)
    {
        using var transaction = await _context.Database.BeginTransactionAsync();
        
        // Save order
        _context.Orders.Add(order);
        
        // Save outbox message
        _context.OutboxMessages.Add(new OutboxMessage
        {
            Type = nameof(OrderCreatedEvent),
            Data = JsonSerializer.Serialize(new OrderCreatedEvent { OrderId = order.Id })
        });
        
        await _context.SaveChangesAsync();
        await transaction.CommitAsync();
    }
}

// Background service publishes outbox messages
public class OutboxProcessor : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var messages = await _context.OutboxMessages
                .Where(m => !m.Published)
                .ToListAsync();

            foreach (var message in messages)
            {
                await _publishEndpoint.Publish(message.Data);
                message.Published = true;
            }

            await _context.SaveChangesAsync();
            await Task.Delay(1000, stoppingToken);
        }
    }
}
```

## What is the Inbox pattern?
**Answer:** Inbox pattern ensures idempotent message processing by tracking processed message IDs.

```csharp
public class OrderConsumer : IConsumer<OrderCreatedEvent>
{
    private readonly OrderDbContext _context;

    public async Task Consume(ConsumeContext<OrderCreatedEvent> context)
    {
        var messageId = context.MessageId.ToString();

        // Check if already processed
        if (await _context.ProcessedMessages.AnyAsync(m => m.MessageId == messageId))
            return;

        // Process message
        await ProcessOrder(context.Message);

        // Mark as processed
        _context.ProcessedMessages.Add(new ProcessedMessage 
        { 
            MessageId = messageId,
            ProcessedAt = DateTime.UtcNow 
        });
        
        await _context.SaveChangesAsync();
    }
}
```

## What is message correlation?
**Answer:** Message correlation links related messages using correlation IDs to track workflows across services.

```csharp
public class OrderService
{
    public async Task CreateOrder(Order order)
    {
        var correlationId = Guid.NewGuid();

        await _publishEndpoint.Publish(new OrderCreatedEvent
        {
            OrderId = order.Id,
            CorrelationId = correlationId
        });
    }
}

public class PaymentConsumer : IConsumer<OrderCreatedEvent>
{
    public async Task Consume(ConsumeContext<OrderCreatedEvent> context)
    {
        await context.Publish(new ProcessPaymentCommand
        {
            OrderId = context.Message.OrderId,
            CorrelationId = context.Message.CorrelationId // Maintain correlation
        });
    }
}
```

## What is API Gateway pattern?
**Answer:** API Gateway is a single entry point for clients, routing requests to microservices, handling authentication, rate limiting, and aggregation.

```csharp
// Ocelot configuration
{
  "Routes": [
    {
      "DownstreamPathTemplate": "/api/products/{id}",
      "DownstreamScheme": "https",
      "DownstreamHostAndPorts": [
        { "Host": "product-service", "Port": 80 }
      ],
      "UpstreamPathTemplate": "/products/{id}",
      "UpstreamHttpMethod": [ "Get" ]
    }
  ]
}
```

## What is Backend for Frontend (BFF) pattern?
**Answer:** BFF creates separate backends for different client types (web, mobile, desktop), each tailored to specific client needs.

```csharp
// Mobile BFF
public class MobileBFFController : ControllerBase
{
    [HttpGet("dashboard")]
    public async Task<MobileDashboard> GetDashboard()
    {
        // Optimized for mobile: minimal data
        var orders = await _orderService.GetRecentOrders(5);
        var summary = await _orderService.GetSummary();
        
        return new MobileDashboard { Orders = orders, Summary = summary };
    }
}

// Web BFF
public class WebBFFController : ControllerBase
{
    [HttpGet("dashboard")]
    public async Task<WebDashboard> GetDashboard()
    {
        // Rich data for web
        var orders = await _orderService.GetAllOrders();
        var analytics = await _analyticsService.GetAnalytics();
        var charts = await _chartService.GetCharts();
        
        return new WebDashboard { Orders = orders, Analytics = analytics, Charts = charts };
    }
}
```

## What is service mesh?
**Answer:** Service mesh (Istio, Linkerd) manages service-to-service communication with features like load balancing, encryption, observability, and traffic control without code changes.

## What is eventual consistency?
**Answer:** Eventual consistency means data becomes consistent across services over time, not immediately, common in asynchronous communication.

```csharp
// Service A: Create order
await _repository.SaveOrder(order);
await _eventBus.Publish(new OrderCreated { OrderId = order.Id });

// Service B: Update inventory (eventually)
public class InventoryConsumer : IConsumer<OrderCreated>
{
    public async Task Consume(ConsumeContext<OrderCreated> context)
    {
        // Eventually updates inventory
        await _inventoryRepository.DecreaseStock(context.Message.ProductId);
    }
}
```

## What is CQRS (Command Query Responsibility Segregation)?
**Answer:** CQRS separates read (queries) and write (commands) operations, often using different data models and databases.

```csharp
// Command side (write)
public class CreateOrderCommandHandler : IRequestHandler<CreateOrderCommand>
{
    public async Task Handle(CreateOrderCommand command)
    {
        var order = new Order { /* ... */ };
        await _writeRepository.AddAsync(order);
        
        await _eventBus.Publish(new OrderCreatedEvent { OrderId = order.Id });
    }
}

// Query side (read)
public class GetOrderQueryHandler : IRequestHandler<GetOrderQuery, OrderDto>
{
    public async Task<OrderDto> Handle(GetOrderQuery query)
    {
        // Read from optimized read model
        return await _readRepository.GetOrderAsync(query.OrderId);
    }
}
```

## How do you handle timeouts in synchronous communication?
**Answer:**
```csharp
// HttpClient timeout
var client = new HttpClient
{
    Timeout = TimeSpan.FromSeconds(30)
};

// Polly timeout policy
services.AddHttpClient("ProductService")
    .AddPolicyHandler(Policy.TimeoutAsync<HttpResponseMessage>(10));

// CancellationToken
public async Task<Product> GetProduct(int id, CancellationToken cancellationToken)
{
    var response = await _httpClient.GetAsync($"api/products/{id}", cancellationToken);
    return await response.Content.ReadFromJsonAsync<Product>(cancellationToken: cancellationToken);
}
```

## What is the difference between orchestration and choreography?
**Answer:**
- **Orchestration:** Central coordinator controls workflow (Order Service coordinates payment → inventory → shipping)
- **Choreography:** Services react to events independently (OrderCreated → Payment listens → PaymentProcessed → Inventory listens)

## How do you monitor inter-service communication?
**Answer:**
- Distributed tracing (OpenTelemetry, Application Insights)
- Correlation IDs
- Structured logging
- Health checks
- Metrics (latency, error rates)

```csharp
// Distributed tracing with Activity
using var activity = ActivitySource.StartActivity("ProcessOrder");
activity?.SetTag("orderId", orderId);

try
{
    await ProcessOrder(orderId);
}
catch (Exception ex)
{
    activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
    throw;
}
```

## What is idempotency and why is it important?
**Answer:** Idempotency ensures processing the same request multiple times produces the same result. Critical for retries in distributed systems.

```csharp
[HttpPost("orders")]
public async Task<IActionResult> CreateOrder([FromHeader] string idempotencyKey, OrderDto order)
{
    // Check if already processed
    var existing = await _repository.GetByIdempotencyKeyAsync(idempotencyKey);
    if (existing != null)
        return Ok(existing); // Return existing result

    // Process new order
    var newOrder = await _orderService.CreateAsync(order, idempotencyKey);
    return CreatedAtAction(nameof(GetOrder), new { id = newOrder.Id }, newOrder);
}
```
