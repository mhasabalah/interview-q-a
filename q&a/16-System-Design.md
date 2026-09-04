---
title: System Design
aliases: [System Design]
tags: [system-design, architecture, interview]
order: 16
---

# System Design Interview Q&A

> [!info]+ Related Notes
> [[06-Database|Database]] · [[11-Module-Communication|Module Communication]] · [[12-RabbitMQ-MassTransit|RabbitMQ & MassTransit]] · [[15-Azure-Cloud|Azure Cloud]] · [[14-CI-CD|CI/CD]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]] · [[17-Architecture-Defense|Architecture Defense]] · [[23-Observability|Observability]]

> [!tip]+ Doing the design round
> Jump to **[[#41. The design round — the framework that scores you|§41 the framework]]** and the worked example **[[#42. Design a booking system for 10k concurrent users|§42 booking system for 10k concurrent users]]**. Practise §42 **out loud, on a whiteboard, in 40 minutes** — the framework is worth more marks than the content.

## Fundamentals

### 1. What is System Design?
System design is the process of defining the architecture, components, modules, interfaces, and data flow for a system to satisfy specified requirements. It focuses on scalability, reliability, performance, and maintainability.

**Key aspects:**
- Scalability (horizontal/vertical)
- Performance optimization
- Load balancing
- Caching strategies
- Database design
- Microservices vs monolithic
- CAP theorem
- Consistency patterns
- Availability patterns

### 2. What are the key considerations in system design?

**Functional Requirements:**
- What features the system must support
- User stories and use cases
- Core functionality

**Non-Functional Requirements:**
- **Scalability:** Handle growing load
- **Performance:** Response time, throughput
- **Reliability:** Fault tolerance, disaster recovery
- **Availability:** Uptime percentage (99.9%, 99.99%)
- **Security:** Authentication, authorization, encryption
- **Maintainability:** Code quality, documentation
- **Cost:** Infrastructure and operational costs

### 3. What is horizontal vs vertical scaling?

**Vertical Scaling (Scale Up):**
- Add more power to existing machine (CPU, RAM, Disk)
- Easier to implement
- Limited by hardware limits
- Single point of failure
- More expensive at scale

**Horizontal Scaling (Scale Out):**
- Add more machines
- Better fault tolerance
- Unlimited scaling potential
- Requires load balancing
- More complex architecture
- Cost-effective at scale

```csharp
// Example: Horizontal scaling with load balancer
/*
                    Load Balancer
                         |
        +----------------+----------------+
        |                |                |
    Server 1         Server 2         Server 3
        |                |                |
    Database Replica Pool (Read replicas)
        |
    Master Database (Write)
*/
```

### 4. What is load balancing?
Distribution of network traffic across multiple servers to ensure no single server is overwhelmed.

**Load Balancing Algorithms:**

**1. Round Robin:**
- Distributes requests sequentially
- Simple, fair distribution
- Doesn't consider server load

**2. Least Connections:**
- Routes to server with fewest active connections
- Better for long-lived connections

**3. Least Response Time:**
- Routes to server with fastest response time

**4. IP Hash:**
- Routes based on client IP hash
- Ensures same client goes to same server (sticky sessions)

**5. Weighted Round Robin:**
- Assigns weights based on server capacity
- More capable servers get more requests

```csharp
// Simple round-robin implementation
public class LoadBalancer
{
    private readonly List<string> _servers;
    private int _currentIndex = 0;
    private readonly object _lock = new object();
    
    public LoadBalancer(List<string> servers)
    {
        _servers = servers;
    }
    
    public string GetNextServer()
    {
        lock (_lock)
        {
            string server = _servers[_currentIndex];
            _currentIndex = (_currentIndex + 1) % _servers.Count;
            return server;
        }
    }
}
```

### 5. What are the types of load balancers?

**Layer 4 (Transport Layer):**
- Routes based on IP and TCP/UDP port
- Fast, simple
- No content inspection
- Example: TCP load balancer

**Layer 7 (Application Layer):**
- Routes based on HTTP headers, cookies, URL path
- Content-aware routing
- SSL termination
- More flexible but slower
- Example: HTTP load balancer, Nginx, HAProxy

**Hardware vs Software:**
- **Hardware:** F5, Citrix NetScaler (expensive, high performance)
- **Software:** Nginx, HAProxy, AWS ELB (flexible, cost-effective)

## Caching

### 6. What is caching and why is it important?

Caching stores frequently accessed data in fast storage (memory) to reduce database load and improve response times.

**Benefits:**
- Reduced latency
- Lower database load
- Better scalability
- Cost savings
- Improved user experience

**Cache Hit vs Miss:**
- **Hit:** Data found in cache (fast)
- **Miss:** Data not in cache, fetch from DB (slow)

### 7. What are different caching strategies?

**1. Cache-Aside (Lazy Loading):**
```csharp
public async Task<User> GetUserAsync(Guid id)
{
    // Check cache first
    string cacheKey = $"user:{id}";
    var cachedUser = await _cache.GetAsync<User>(cacheKey);
    
    if (cachedUser != null)
        return cachedUser; // Cache hit
    
    // Cache miss - fetch from database
    var user = await _database.GetUserAsync(id);
    
    // Store in cache
    await _cache.SetAsync(cacheKey, user, TimeSpan.FromMinutes(10));
    
    return user;
}
```
- Application manages cache
- Cache only what's requested
- Stale data possible

**2. Write-Through:**
```csharp
public async Task UpdateUserAsync(User user)
{
    // Write to database first
    await _database.UpdateUserAsync(user);
    
    // Then update cache
    string cacheKey = $"user:{user.Id}";
    await _cache.SetAsync(cacheKey, user, TimeSpan.FromMinutes(10));
}
```
- Write to cache and database simultaneously
- Data consistency guaranteed
- Higher write latency

**3. Write-Behind (Write-Back):**
- Write to cache immediately
- Asynchronously write to database
- Faster writes
- Risk of data loss if cache fails

**4. Refresh-Ahead:**
- Proactively refresh cache before expiration
- Reduced latency for frequently accessed data
- More complex implementation

### 8. What are cache eviction policies?

**LRU (Least Recently Used):**
- Evicts least recently accessed items
- Most common, good general-purpose

**LFU (Least Frequently Used):**
- Evicts items accessed least often
- Good for long-term popular items

**FIFO (First In First Out):**
- Evicts oldest items first
- Simple but not optimal

**TTL (Time To Live):**
- Items expire after fixed time
- Good for time-sensitive data

```csharp
// LRU Cache implementation
public class LRUCache<TKey, TValue>
{
    private readonly int _capacity;
    private readonly Dictionary<TKey, LinkedListNode<CacheItem>> _cache;
    private readonly LinkedList<CacheItem> _lruList;
    
    public LRUCache(int capacity)
    {
        _capacity = capacity;
        _cache = new Dictionary<TKey, LinkedListNode<CacheItem>>();
        _lruList = new LinkedList<CacheItem>();
    }
    
    public TValue Get(TKey key)
    {
        if (_cache.TryGetValue(key, out var node))
        {
            // Move to front (most recently used)
            _lruList.Remove(node);
            _lruList.AddFirst(node);
            return node.Value.Value;
        }
        return default;
    }
    
    public void Put(TKey key, TValue value)
    {
        if (_cache.TryGetValue(key, out var node))
        {
            // Update existing
            node.Value.Value = value;
            _lruList.Remove(node);
            _lruList.AddFirst(node);
        }
        else
        {
            // Add new
            if (_cache.Count >= _capacity)
            {
                // Evict least recently used
                var lastNode = _lruList.Last;
                _cache.Remove(lastNode.Value.Key);
                _lruList.RemoveLast();
            }
            
            var newNode = new LinkedListNode<CacheItem>(new CacheItem(key, value));
            _lruList.AddFirst(newNode);
            _cache[key] = newNode;
        }
    }
    
    private class CacheItem
    {
        public TKey Key { get; }
        public TValue Value { get; set; }
        
        public CacheItem(TKey key, TValue value)
        {
            Key = key;
            Value = value;
        }
    }
}
```

### 9. What are different levels of caching?

**Client-Side Cache:**
- Browser cache
- Mobile app cache
- Fast but limited control

**CDN (Content Delivery Network):**
- Static assets (images, CSS, JS)
- Distributed globally
- Reduces latency

**Application Cache:**
- In-memory cache (Redis, Memcached)
- Shared across app servers
- Fast access to dynamic data

**Database Cache:**
- Query result cache
- Buffer pool
- Internal to database

```
Client → CDN → Load Balancer → App Server (Redis) → Database
```

### 10. What is Redis and when to use it?

Redis is an in-memory key-value store used for caching, session storage, real-time analytics.

**Use cases:**
- Session management
- Caching API responses
- Real-time leaderboards
- Rate limiting
- Pub/Sub messaging
- Distributed locks

```csharp
// Redis example with StackExchange.Redis
public class RedisCache
{
    private readonly IConnectionMultiplexer _redis;
    private readonly IDatabase _db;
    
    public RedisCache(string connectionString)
    {
        _redis = ConnectionMultiplexer.Connect(connectionString);
        _db = _redis.GetDatabase();
    }
    
    public async Task<T> GetAsync<T>(string key)
    {
        var value = await _db.StringGetAsync(key);
        if (value.IsNullOrEmpty)
            return default;
        
        return JsonSerializer.Deserialize<T>(value);
    }
    
    public async Task SetAsync<T>(string key, T value, TimeSpan expiration)
    {
        var json = JsonSerializer.Serialize(value);
        await _db.StringSetAsync(key, json, expiration);
    }
    
    public async Task<bool> DeleteAsync(string key)
    {
        return await _db.KeyDeleteAsync(key);
    }
}
```

## Database Design

### 11. What is database sharding?

Sharding is horizontal partitioning where data is split across multiple databases based on a shard key.

**Sharding Strategies:**

**1. Hash-Based:**
```csharp
int shardId = userId.GetHashCode() % numberOfShards;
```
- Even distribution
- Hard to add/remove shards

**2. Range-Based:**
```csharp
// User IDs 1-1M → Shard 1
// User IDs 1M-2M → Shard 2
```
- Easy to add shards
- Uneven distribution possible

**3. Geographic:**
- US users → US database
- EU users → EU database
- Latency optimization
- Data sovereignty compliance

**Challenges:**
- Cross-shard queries
- Distributed transactions
- Rebalancing data
- Increased complexity

### 12. What is database replication?

Copying data from master database to one or more replica databases.

**Types:**

**Master-Slave (Primary-Replica):**
```
Master (Write)
   ↓
   ├→ Slave 1 (Read)
   ├→ Slave 2 (Read)
   └→ Slave 3 (Read)
```
- Write to master only
- Read from replicas
- Scales read operations
- Eventual consistency

**Master-Master:**
```
Master 1 ↔ Master 2
```
- Write to either master
- Conflict resolution needed
- Higher availability

```csharp
// Connection string routing
public class DatabaseRouter
{
    private readonly string _masterConnection;
    private readonly List<string> _replicaConnections;
    private int _replicaIndex = 0;
    
    public string GetConnectionString(bool isWrite)
    {
        if (isWrite)
            return _masterConnection;
        
        // Round-robin read replicas
        var connection = _replicaConnections[_replicaIndex];
        _replicaIndex = (_replicaIndex + 1) % _replicaConnections.Count;
        return connection;
    }
}
```

### 13. What is SQL vs NoSQL?

**SQL (Relational):**
- Structured schema
- ACID transactions
- Complex queries (JOINs)
- Vertical scaling primarily
- Examples: PostgreSQL, MySQL, SQL Server

**NoSQL:**
- Flexible schema
- BASE (eventual consistency)
- Simple queries
- Horizontal scaling
- Types: Document, Key-Value, Column, Graph
- Examples: MongoDB, Redis, Cassandra, Neo4j

**When to use SQL:**
- Complex relationships
- ACID compliance required
- Structured data
- Complex queries

**When to use NoSQL:**
- Flexible schema
- Massive scale
- High write throughput
- Simple queries
- Denormalized data

### 14. What is the CAP theorem?

CAP theorem states distributed systems can only guarantee 2 of 3:

**Consistency:** All nodes see same data at same time

**Availability:** Every request gets response (success/failure)

**Partition Tolerance:** System continues despite network partitions

**Trade-offs:**
- **CP (Consistency + Partition Tolerance):** MongoDB, HBase
  - Sacrifice availability during partition
  
- **AP (Availability + Partition Tolerance):** Cassandra, DynamoDB
  - Sacrifice consistency (eventual consistency)
  
- **CA (Consistency + Availability):** Traditional RDBMS
  - Not realistic in distributed systems (partitions happen)

In practice, choose between CP or AP based on requirements.

### 15. What is eventual consistency?

System doesn't guarantee immediate consistency but will become consistent over time.

**Example:**
```
User posts tweet
  ↓
Master DB updated (write)
  ↓
Replicas sync asynchronously (delay: 100ms - 1s)
  ↓
Eventually all replicas consistent
```

**Use cases:**
- Social media feeds
- Product catalogs
- DNS
- Email

**Not suitable for:**
- Financial transactions
- Inventory management
- Booking systems

## Microservices

### 16. What are microservices?

Architectural style where application is composed of small, independent services that communicate over network.

**Characteristics:**
- Single responsibility
- Independently deployable
- Loosely coupled
- Own database per service
- Technology agnostic

**Monolithic vs Microservices:**

**Monolithic:**
```
Single Application
├── User Module
├── Order Module
├── Payment Module
└── Shared Database
```

**Microservices:**
```
User Service → User DB
Order Service → Order DB
Payment Service → Payment DB
(Connected via API Gateway)
```

### 17. What are the pros and cons of microservices?

**Pros:**
- Independent scaling
- Technology flexibility
- Faster deployment
- Fault isolation
- Team autonomy
- Better for large teams

**Cons:**
- Increased complexity
- Network latency
- Distributed transactions
- Testing challenges
- Monitoring complexity
- More infrastructure overhead

**When to use microservices:**
- Large application
- Multiple teams
- Different scaling needs
- Rapid deployment required

**When to use monolith:**
- Small application
- Small team
- Simple requirements
- Quick to market

### 18. How do microservices communicate?

**Synchronous Communication:**

**1. REST API:**
```csharp
// Order Service calls User Service
public async Task<User> GetUserAsync(Guid userId)
{
    var response = await _httpClient.GetAsync($"https://user-service/api/users/{userId}");
    response.EnsureSuccessStatusCode();
    return await response.Content.ReadFromJsonAsync<User>();
}
```
- Simple, widely understood
- Tight coupling
- Service must be available

**2. gRPC:**
```csharp
// Define in .proto file
service UserService {
  rpc GetUser (UserRequest) returns (UserResponse);
}

// C# client
var user = await _grpcClient.GetUserAsync(new UserRequest { UserId = userId });
```
- High performance
- Type-safe
- Binary protocol

**Asynchronous Communication:**

**1. Message Queue:**
```csharp
// Producer (Order Service)
public async Task CreateOrderAsync(Order order)
{
    await _database.SaveAsync(order);
    
    // Publish event
    await _messageQueue.PublishAsync("order.created", new OrderCreatedEvent
    {
        OrderId = order.Id,
        UserId = order.UserId,
        Total = order.Total
    });
}

// Consumer (Email Service)
public async Task HandleOrderCreatedAsync(OrderCreatedEvent evt)
{
    await _emailService.SendOrderConfirmationAsync(evt.UserId, evt.OrderId);
}
```
- Decoupled services
- Asynchronous processing
- Better fault tolerance
- Examples: RabbitMQ, Kafka, Azure Service Bus

### 19. What is an API Gateway?

Single entry point for all clients to access microservices.

**Responsibilities:**
- Request routing
- Authentication/Authorization
- Rate limiting
- Request/response transformation
- Load balancing
- Caching
- Logging/Monitoring

```
Client → API Gateway → [User Service, Order Service, Payment Service]
```

```csharp
// Using Ocelot API Gateway (configuration)
{
  "Routes": [
    {
      "DownstreamPathTemplate": "/api/users/{id}",
      "DownstreamScheme": "https",
      "DownstreamHostAndPorts": [
        { "Host": "user-service", "Port": 80 }
      ],
      "UpstreamPathTemplate": "/users/{id}",
      "UpstreamHttpMethod": [ "GET" ],
      "RateLimitOptions": {
        "EnableRateLimiting": true,
        "Period": "1s",
        "Limit": 10
      }
    }
  ]
}
```

### 20. What is service discovery?

Automatically detecting network locations of service instances.

**Client-Side Discovery:**
```csharp
// Client queries service registry
var instances = await _serviceRegistry.GetInstancesAsync("order-service");
var instance = _loadBalancer.SelectInstance(instances);
var response = await _httpClient.GetAsync($"{instance.Url}/api/orders");
```
- Client chooses instance
- Examples: Eureka, Consul

**Server-Side Discovery:**
```
Client → Load Balancer → Service Registry → Service Instances
```
- Load balancer handles routing
- Examples: AWS ELB, Kubernetes Service

### 21. What is circuit breaker pattern?

Prevents cascading failures by stopping requests to failing service.

**States:**
- **Closed:** Normal operation
- **Open:** Service failing, reject requests immediately
- **Half-Open:** Test if service recovered

```csharp
// Using Polly library
public class ResilientHttpClient
{
    private readonly HttpClient _httpClient;
    private readonly IAsyncPolicy<HttpResponseMessage> _circuitBreakerPolicy;
    
    public ResilientHttpClient(HttpClient httpClient)
    {
        _httpClient = httpClient;
        
        _circuitBreakerPolicy = Policy
            .HandleResult<HttpResponseMessage>(r => !r.IsSuccessStatusCode)
            .CircuitBreakerAsync(
                handledEventsAllowedBeforeBreaking: 3,
                durationOfBreak: TimeSpan.FromSeconds(30),
                onBreak: (result, duration) =>
                {
                    Console.WriteLine($"Circuit breaker opened for {duration}");
                },
                onReset: () =>
                {
                    Console.WriteLine("Circuit breaker reset");
                }
            );
    }
    
    public async Task<HttpResponseMessage> GetAsync(string url)
    {
        return await _circuitBreakerPolicy.ExecuteAsync(() =>
            _httpClient.GetAsync(url));
    }
}
```

### 22. What is saga pattern?

Manages distributed transactions across microservices using sequence of local transactions.

**Choreography-Based:**
```csharp
// Each service publishes/listens to events

// Order Service
await _database.CreateOrderAsync(order);
await _eventBus.PublishAsync(new OrderCreatedEvent(orderId));

// Payment Service (listens to OrderCreated)
await ProcessPaymentAsync(orderId);
await _eventBus.PublishAsync(new PaymentProcessedEvent(orderId));

// Inventory Service (listens to PaymentProcessed)
await ReserveInventoryAsync(orderId);
await _eventBus.PublishAsync(new InventoryReservedEvent(orderId));

// If payment fails - compensating transaction
await _eventBus.PublishAsync(new PaymentFailedEvent(orderId));
// Order Service listens and cancels order
```

**Orchestration-Based:**
```csharp
// Saga Orchestrator coordinates all steps
public class OrderSaga
{
    public async Task ExecuteAsync(CreateOrderCommand command)
    {
        try
        {
            var orderId = await _orderService.CreateOrderAsync(command);
            await _paymentService.ProcessPaymentAsync(orderId);
            await _inventoryService.ReserveInventoryAsync(orderId);
            await _shippingService.CreateShipmentAsync(orderId);
        }
        catch
        {
            // Rollback
            await _inventoryService.ReleaseInventoryAsync(orderId);
            await _paymentService.RefundAsync(orderId);
            await _orderService.CancelOrderAsync(orderId);
            throw;
        }
    }
}
```

## Performance & Scalability

### 23. What is rate limiting?

Controlling the number of requests a client can make in a time period.

**Algorithms:**

**1. Fixed Window:**
```csharp
public class FixedWindowRateLimiter
{
    private readonly Dictionary<string, (int count, DateTime windowStart)> _clients = new();
    private readonly int _limit;
    private readonly TimeSpan _window;
    
    public bool AllowRequest(string clientId)
    {
        var now = DateTime.UtcNow;
        
        if (!_clients.ContainsKey(clientId))
        {
            _clients[clientId] = (1, now);
            return true;
        }
        
        var (count, windowStart) = _clients[clientId];
        
        if (now - windowStart > _window)
        {
            // New window
            _clients[clientId] = (1, now);
            return true;
        }
        
        if (count >= _limit)
            return false;
        
        _clients[clientId] = (count + 1, windowStart);
        return true;
    }
}
```

**2. Sliding Window Log:**
- Track timestamp of each request
- More accurate but memory intensive

**3. Token Bucket:**
```csharp
public class TokenBucket
{
    private int _tokens;
    private readonly int _capacity;
    private readonly int _refillRate;
    private DateTime _lastRefill;
    
    public TokenBucket(int capacity, int refillRate)
    {
        _capacity = capacity;
        _tokens = capacity;
        _refillRate = refillRate;
        _lastRefill = DateTime.UtcNow;
    }
    
    public bool TryConsume()
    {
        Refill();
        
        if (_tokens > 0)
        {
            _tokens--;
            return true;
        }
        
        return false;
    }
    
    private void Refill()
    {
        var now = DateTime.UtcNow;
        var elapsed = (now - _lastRefill).TotalSeconds;
        var tokensToAdd = (int)(elapsed * _refillRate);
        
        _tokens = Math.Min(_capacity, _tokens + tokensToAdd);
        _lastRefill = now;
    }
}
```

**4. Leaky Bucket:**
- Processes requests at constant rate
- Smooths bursts

```csharp
// ASP.NET Core rate limiting
builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("fixed", opt =>
    {
        opt.PermitLimit = 10;
        opt.Window = TimeSpan.FromMinutes(1);
    });
});

app.UseRateLimiter();

// Controller
[EnableRateLimiting("fixed")]
[HttpGet]
public IActionResult Get() => Ok();
```

### 24. What is CDN (Content Delivery Network)?

Geographically distributed servers that cache static content closer to users.

**Benefits:**
- Reduced latency
- Lower bandwidth costs
- Better availability
- DDoS protection

**How it works:**
```
User in Tokyo → CDN Edge Server (Tokyo) → Origin Server (US)
                     ↓ (cached)
                Returns cached content
```

**What to cache:**
- Images, videos
- CSS, JavaScript
- Static HTML
- API responses (with cache headers)

```csharp
// Setting cache headers
[ResponseCache(Duration = 3600, Location = ResponseCacheLocation.Any)]
[HttpGet("products/{id}")]
public IActionResult GetProduct(int id)
{
    // CDN will cache for 1 hour
    return Ok(product);
}
```

### 25. What is database indexing?

Data structure that improves query performance by allowing faster data retrieval.

**Types:**

**Clustered Index:**
- Determines physical order of data
- One per table
- Usually on primary key

**Non-Clustered Index:**
- Separate structure pointing to data
- Multiple per table
- Additional storage overhead

```sql
-- Create index
CREATE INDEX idx_user_email ON Users(Email);

-- Composite index
CREATE INDEX idx_order_user_date ON Orders(UserId, OrderDate);

-- Query using index
SELECT * FROM Users WHERE Email = 'john@example.com';
-- Uses idx_user_email
```

**Trade-offs:**
- **Pros:** Faster reads
- **Cons:** Slower writes, more storage

**When to index:**
- Frequently queried columns
- Foreign keys
- Columns in WHERE, JOIN, ORDER BY

**When NOT to index:**
- Small tables
- Columns with low cardinality
- Frequently updated columns

### 26. What is database connection pooling?

Reusing database connections instead of creating new ones for each request.

```csharp
// Connection string with pooling
"Server=myServer;Database=myDB;User Id=user;Password=pwd;Min Pool Size=5;Max Pool Size=100;"

// Configuration
public static class DatabaseConfig
{
    public static IServiceCollection AddDatabase(this IServiceCollection services, string connectionString)
    {
        services.AddDbContext<AppDbContext>(options =>
            options.UseSqlServer(connectionString, sqlOptions =>
            {
                sqlOptions.EnableRetryOnFailure(
                    maxRetryCount: 3,
                    maxRetryDelay: TimeSpan.FromSeconds(5),
                    errorNumbersToAdd: null);
                    
                sqlOptions.CommandTimeout(30);
            }));
        
        return services;
    }
}
```

**Benefits:**
- Reduced connection overhead
- Better performance
- Controlled resource usage

**Best practices:**
- Set appropriate min/max pool size
- Always dispose connections
- Use connection timeout
- Monitor pool exhaustion

### 27. What is pagination?

Breaking large result sets into smaller pages.

**Offset-Based:**
```csharp
[HttpGet]
public async Task<ActionResult<PagedResult<Product>>> GetProducts(
    [FromQuery] int page = 1,
    [FromQuery] int pageSize = 20)
{
    var skip = (page - 1) * pageSize;
    
    var total = await _context.Products.CountAsync();
    var products = await _context.Products
        .Skip(skip)
        .Take(pageSize)
        .ToListAsync();
    
    return new PagedResult<Product>
    {
        Items = products,
        Page = page,
        PageSize = pageSize,
        TotalCount = total,
        TotalPages = (int)Math.Ceiling(total / (double)pageSize)
    };
}
```

**Cursor-Based (Better for large datasets):**
```csharp
[HttpGet]
public async Task<ActionResult<CursorPagedResult<Product>>> GetProducts(
    [FromQuery] Guid? cursor = null,
    [FromQuery] int limit = 20)
{
    var query = _context.Products.OrderBy(p => p.Id);
    
    if (cursor.HasValue)
        query = query.Where(p => p.Id > cursor.Value);
    
    var products = await query.Take(limit + 1).ToListAsync();
    
    var hasMore = products.Count > limit;
    if (hasMore)
        products.RemoveAt(products.Count - 1);
    
    return new CursorPagedResult<Product>
    {
        Items = products,
        NextCursor = hasMore ? products.Last().Id : (Guid?)null,
        HasMore = hasMore
    };
}
```

### 28. What is denormalization?

Adding redundant data to optimize read performance.

**Example:**
```sql
-- Normalized
Orders: OrderId, CustomerId, OrderDate
OrderItems: ItemId, OrderId, ProductId, Quantity, Price

-- Denormalized (add customer name to orders)
Orders: OrderId, CustomerId, CustomerName, OrderDate
```

**Trade-offs:**
- **Pros:** Faster queries (no JOINs), better read performance
- **Cons:** Data duplication, update anomalies, more storage

**When to denormalize:**
- Read-heavy workloads
- Performance critical queries
- Rarely updated data
- NoSQL databases

## Reliability & Availability

### 29. What is fault tolerance?

System's ability to continue operating despite failures.

**Strategies:**

**1. Redundancy:**
- Multiple instances
- No single point of failure

**2. Failover:**
```csharp
public class FailoverHttpClient
{
    private readonly List<string> _endpoints;
    private readonly HttpClient _httpClient;
    
    public async Task<HttpResponseMessage> GetAsync(string path)
    {
        foreach (var endpoint in _endpoints)
        {
            try
            {
                var response = await _httpClient.GetAsync($"{endpoint}{path}");
                if (response.IsSuccessStatusCode)
                    return response;
            }
            catch
            {
                // Try next endpoint
                continue;
            }
        }
        
        throw new Exception("All endpoints failed");
    }
}
```

**3. Graceful Degradation:**
- Return cached data if service fails
- Disable non-critical features
- Show informative error messages

**4. Retry Logic:**
```csharp
var retryPolicy = Policy
    .Handle<HttpRequestException>()
    .WaitAndRetryAsync(
        retryCount: 3,
        sleepDurationProvider: attempt => TimeSpan.FromSeconds(Math.Pow(2, attempt)),
        onRetry: (exception, timeSpan, retryCount, context) =>
        {
            Console.WriteLine($"Retry {retryCount} after {timeSpan}");
        });

await retryPolicy.ExecuteAsync(() => _httpClient.GetAsync(url));
```

### 30. What is a health check?

Monitoring endpoint that reports service health.

```csharp
// Program.cs
builder.Services.AddHealthChecks()
    .AddDbContextCheck<AppDbContext>()
    .AddRedis(builder.Configuration["Redis:ConnectionString"])
    .AddCheck("External API", () =>
    {
        // Custom health check
        return HealthCheckResult.Healthy();
    });

app.MapHealthChecks("/health");

// Custom health check
public class DatabaseHealthCheck : IHealthCheck
{
    private readonly AppDbContext _context;
    
    public DatabaseHealthCheck(AppDbContext context)
    {
        _context = context;
    }
    
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await _context.Database.CanConnectAsync(cancellationToken);
            return HealthCheckResult.Healthy("Database is healthy");
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy("Database is unhealthy", ex);
        }
    }
}
```

**Kubernetes liveness/readiness probes:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 80
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 31. What is monitoring and observability?

**Monitoring:** Collecting metrics, logs, traces to understand system behavior.

**Three Pillars:**

**1. Metrics:**
```csharp
// Using App Metrics
public class MetricsService
{
    private readonly IMetrics _metrics;
    
    public void TrackRequest(string endpoint, int statusCode, long duration)
    {
        _metrics.Measure.Counter.Increment(new CounterOptions
        {
            Name = "http_requests_total",
            Tags = new MetricTags("endpoint", endpoint)
        });
        
        _metrics.Measure.Histogram.Update(new HistogramOptions
        {
            Name = "http_request_duration_ms"
        }, duration);
    }
}
```

**2. Logs:**
```csharp
// Structured logging with Serilog
Log.Information("User {UserId} created order {OrderId} with total {Total}",
    userId, orderId, total);
```

**3. Distributed Tracing:**
```csharp
// Using OpenTelemetry
var activity = Activity.Current;
activity?.SetTag("user.id", userId);
activity?.SetTag("order.total", total);
```

**Tools:**
- **Metrics:** Prometheus, Grafana
- **Logs:** ELK Stack (Elasticsearch, Logstash, Kibana), Seq
- **Tracing:** Jaeger, Zipkin
- **APM:** Application Insights, New Relic, Datadog

### 32. What are SLAs, SLOs, and SLIs?

**SLI (Service Level Indicator):**
- Quantitative measure of service level
- Example: Response time, error rate, uptime

**SLO (Service Level Objective):**
- Target value for SLI
- Example: 99.9% uptime, p95 latency < 200ms

**SLA (Service Level Agreement):**
- Contract with consequences for not meeting SLO
- Example: 99.95% uptime or customer gets refund

```
Uptime Percentage → Downtime per year
99%      → 3.65 days
99.9%    → 8.76 hours
99.95%   → 4.38 hours
99.99%   → 52.56 minutes
99.999%  → 5.26 minutes (five nines)
```

## Security

### 33. What is authentication vs authorization?

**Authentication:** Verifying who you are (identity)
- Username/password
- OAuth, JWT
- Multi-factor authentication

**Authorization:** Verifying what you can do (permissions)
- Role-based (RBAC)
- Claims-based
- Policy-based

```csharp
// Authentication - JWT
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = configuration["Jwt:Issuer"],
            ValidAudience = configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(configuration["Jwt:Key"]))
        };
    });

// Authorization - Policy-based
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"));
        
    options.AddPolicy("CanDeleteOrder", policy =>
        policy.RequireClaim("permission", "order.delete"));
});

// Controller
[Authorize(Policy = "CanDeleteOrder")]
[HttpDelete("{id}")]
public async Task<IActionResult> DeleteOrder(Guid id)
{
    // Only users with order.delete permission
}
```

### 34. What is OAuth 2.0 and OpenID Connect?

**OAuth 2.0:** Authorization framework for delegated access

**OpenID Connect (OIDC):** Authentication layer on top of OAuth 2.0

**Flow:**
```
User → Client App → Authorization Server (Login) → Access Token → Resource Server
```

**Token Types:**
- **Access Token:** Authorization to access resources
- **Refresh Token:** Get new access token
- **ID Token (OIDC):** User identity information

```csharp
// ASP.NET Core with Auth0/Azure AD
builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.Authority = "https://your-auth-server.com";
    options.Audience = "your-api";
});
```

### 35. What is encryption at rest vs in transit?

**At Rest:** Encrypting stored data
```csharp
// Database encryption (SQL Server)
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'password';
CREATE CERTIFICATE MyCert WITH SUBJECT = 'Data Encryption';
CREATE SYMMETRIC KEY MyKey WITH ALGORITHM = AES_256
    ENCRYPTION BY CERTIFICATE MyCert;

// File encryption
public class EncryptionService
{
    public byte[] Encrypt(byte[] data, string key)
    {
        using var aes = Aes.Create();
        aes.Key = Encoding.UTF8.GetBytes(key);
        aes.GenerateIV();
        
        using var encryptor = aes.CreateEncryptor();
        var encrypted = encryptor.TransformFinalBlock(data, 0, data.Length);
        
        return aes.IV.Concat(encrypted).ToArray();
    }
}
```

**In Transit:** Encrypting data during transmission
- HTTPS/TLS
- VPN
- Message encryption

```csharp
// Force HTTPS
builder.Services.AddHttpsRedirection(options =>
{
    options.RedirectStatusCode = StatusCodes.Status308PermanentRedirect;
    options.HttpsPort = 443;
});

app.UseHttpsRedirection();
```

## Real-World System Design Examples

### 36. Design a URL shortener (like bit.ly)

**Requirements:**
- Shorten long URLs to short codes
- Redirect short URLs to original
- Track click analytics
- High read:write ratio (100:1)

**Design:**

```csharp
// 1. Generate short code
public class UrlShortener
{
    private const string Base62Chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    
    public string GenerateShortCode(long id)
    {
        var code = new StringBuilder();
        while (id > 0)
        {
            code.Insert(0, Base62Chars[(int)(id % 62)]);
            id /= 62;
        }
        return code.ToString().PadLeft(7, '0'); // 7 chars = 62^7 = 3.5 trillion URLs
    }
    
    public async Task<string> ShortenUrl(string longUrl)
    {
        // Check if URL already exists
        var existing = await _cache.GetAsync<string>(longUrl);
        if (existing != null)
            return existing;
        
        // Get next ID from database (auto-increment)
        var id = await _database.GetNextIdAsync();
        var shortCode = GenerateShortCode(id);
        
        // Store mapping
        await _database.SaveAsync(new UrlMapping
        {
            Id = id,
            ShortCode = shortCode,
            LongUrl = longUrl,
            CreatedAt = DateTime.UtcNow
        });
        
        // Cache for quick lookup
        await _cache.SetAsync(shortCode, longUrl, TimeSpan.FromDays(7));
        
        return shortCode;
    }
    
    public async Task<string> GetLongUrl(string shortCode)
    {
        // Check cache first
        var cached = await _cache.GetAsync<string>(shortCode);
        if (cached != null)
        {
            // Track analytics asynchronously
            _ = Task.Run(() => _analytics.TrackClickAsync(shortCode));
            return cached;
        }
        
        // Fetch from database
        var mapping = await _database.GetByShortCodeAsync(shortCode);
        if (mapping == null)
            return null;
        
        // Cache it
        await _cache.SetAsync(shortCode, mapping.LongUrl, TimeSpan.FromDays(7));
        
        // Track analytics
        _ = Task.Run(() => _analytics.TrackClickAsync(shortCode));
        
        return mapping.LongUrl;
    }
}

// 2. Controller
[HttpPost("shorten")]
public async Task<IActionResult> Shorten([FromBody] ShortenRequest request)
{
    var shortCode = await _urlShortener.ShortenUrl(request.Url);
    return Ok(new { shortUrl = $"https://short.ly/{shortCode}" });
}

[HttpGet("{shortCode}")]
public async Task<IActionResult> Redirect(string shortCode)
{
    var longUrl = await _urlShortener.GetLongUrl(shortCode);
    if (longUrl == null)
        return NotFound();
    
    return Redirect(longUrl);
}
```

**Architecture:**
```
Client → Load Balancer → API Servers (stateless)
                              ↓
                         Redis Cache
                              ↓
                      Database (sharded)
                              ↓
                      Analytics Service (async)
```

### 37. Design a rate limiter

**Requirements:**
- Limit API calls per user
- Multiple limits (per second, per minute, per day)
- Distributed system

**Design:**

```csharp
public class DistributedRateLimiter
{
    private readonly IDatabase _redis;
    
    public DistributedRateLimiter(IConnectionMultiplexer redis)
    {
        _redis = redis.GetDatabase();
    }
    
    public async Task<bool> AllowRequestAsync(
        string userId,
        string resource,
        int limit,
        TimeSpan window)
    {
        var key = $"ratelimit:{userId}:{resource}:{window.TotalSeconds}";
        var now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        
        // Sliding window log with Redis sorted set
        var transaction = _redis.CreateTransaction();
        
        // Remove old entries
        transaction.SortedSetRemoveRangeByScoreAsync(key, 0, now - window.TotalSeconds);
        
        // Count current requests
        var countTask = transaction.SortedSetLengthAsync(key);
        
        // Add new request
        transaction.SortedSetAddAsync(key, now, now);
        
        // Set expiration
        transaction.KeyExpireAsync(key, window);
        
        await transaction.ExecuteAsync();
        
        var count = await countTask;
        return count < limit;
    }
}

// Middleware
public class RateLimitMiddleware
{
    private readonly RequestDelegate _next;
    private readonly DistributedRateLimiter _rateLimiter;
    
    public async Task InvokeAsync(HttpContext context)
    {
        var userId = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value ?? "anonymous";
        var path = context.Request.Path;
        
        var allowed = await _rateLimiter.AllowRequestAsync(
            userId,
            path,
            limit: 100,
            window: TimeSpan.FromMinutes(1));
        
        if (!allowed)
        {
            context.Response.StatusCode = 429; // Too Many Requests
            await context.Response.WriteAsync("Rate limit exceeded");
            return;
        }
        
        await _next(context);
    }
}
```

### 38. Design a notification system

**Requirements:**
- Send email, SMS, push notifications
- Handle millions of notifications
- Support priority levels
- Track delivery status

**Design:**

```csharp
// 1. Notification models
public enum NotificationType { Email, SMS, Push }
public enum Priority { Low, Normal, High, Urgent }

public class Notification
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public NotificationType Type { get; set; }
    public Priority Priority { get; set; }
    public string Subject { get; set; }
    public string Body { get; set; }
    public Dictionary<string, string> Metadata { get; set; }
}

// 2. Notification service
public class NotificationService
{
    private readonly IMessageQueue _messageQueue;
    
    public async Task SendAsync(Notification notification)
    {
        // Validate
        await ValidateAsync(notification);
        
        // Save to database
        await _database.SaveAsync(notification);
        
        // Queue for processing
        var queueName = GetQueueName(notification.Priority);
        await _messageQueue.EnqueueAsync(queueName, notification);
    }
    
    private string GetQueueName(Priority priority)
    {
        return priority switch
        {
            Priority.Urgent => "notifications-urgent",
            Priority.High => "notifications-high",
            Priority.Normal => "notifications-normal",
            Priority.Low => "notifications-low",
            _ => "notifications-normal"
        };
    }
}

// 3. Background worker
public class NotificationWorker : BackgroundService
{
    private readonly IMessageQueue _messageQueue;
    private readonly INotificationProvider _emailProvider;
    private readonly INotificationProvider _smsProvider;
    private readonly INotificationProvider _pushProvider;
    
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // Process different priority queues
        var tasks = new[]
        {
            ProcessQueueAsync("notifications-urgent", stoppingToken),
            ProcessQueueAsync("notifications-high", stoppingToken),
            ProcessQueueAsync("notifications-normal", stoppingToken),
            ProcessQueueAsync("notifications-low", stoppingToken)
        };
        
        await Task.WhenAll(tasks);
    }
    
    private async Task ProcessQueueAsync(string queueName, CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            var notification = await _messageQueue.DequeueAsync<Notification>(queueName);
            
            if (notification != null)
            {
                await SendNotificationAsync(notification);
            }
            else
            {
                await Task.Delay(1000, cancellationToken);
            }
        }
    }
    
    private async Task SendNotificationAsync(Notification notification)
    {
        try
        {
            var provider = GetProvider(notification.Type);
            await provider.SendAsync(notification);
            
            // Update status
            await _database.UpdateStatusAsync(notification.Id, "Sent");
        }
        catch (Exception ex)
        {
            // Retry logic with exponential backoff
            await HandleFailureAsync(notification, ex);
        }
    }
}
```

**Architecture:**
```
API Server → Message Queue (RabbitMQ/SQS)
                    ↓
            [Urgent Queue]    → Worker Pool → Email Provider
            [High Queue]      → Worker Pool → SMS Provider
            [Normal Queue]    → Worker Pool → Push Provider
            [Low Queue]       → Worker Pool
                    ↓
            Status Database
```

### 39. Design a chat system

**Requirements:**
- Real-time messaging
- One-to-one and group chat
- Message history
- Online status
- Read receipts

**Design:**

```csharp
// 1. WebSocket connection
public class ChatHub : Hub
{
    private readonly IChatService _chatService;
    private readonly IPresenceService _presenceService;
    
    public override async Task OnConnectedAsync()
    {
        var userId = Context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        await _presenceService.SetOnlineAsync(userId);
        await base.OnConnectedAsync();
    }
    
    public override async Task OnDisconnectedAsync(Exception exception)
    {
        var userId = Context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        await _presenceService.SetOfflineAsync(userId);
        await base.OnDisconnectedAsync(exception);
    }
    
    public async Task SendMessage(string recipientId, string message)
    {
        var senderId = Context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        
        // Save message
        var chatMessage = await _chatService.SaveMessageAsync(new ChatMessage
        {
            SenderId = senderId,
            RecipientId = recipientId,
            Content = message,
            Timestamp = DateTime.UtcNow
        });
        
        // Send to recipient if online
        await Clients.User(recipientId).SendAsync("ReceiveMessage", chatMessage);
        
        // Send confirmation to sender
        await Clients.Caller.SendAsync("MessageSent", chatMessage.Id);
    }
    
    public async Task SendGroupMessage(string groupId, string message)
    {
        var senderId = Context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        
        var chatMessage = await _chatService.SaveGroupMessageAsync(groupId, new ChatMessage
        {
            SenderId = senderId,
            GroupId = groupId,
            Content = message,
            Timestamp = DateTime.UtcNow
        });
        
        // Broadcast to all group members
        await Clients.Group(groupId).SendAsync("ReceiveMessage", chatMessage);
    }
    
    public async Task MarkAsRead(string messageId)
    {
        var userId = Context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        await _chatService.MarkAsReadAsync(messageId, userId);
        
        // Notify sender
        var message = await _chatService.GetMessageAsync(messageId);
        await Clients.User(message.SenderId).SendAsync("MessageRead", messageId, userId);
    }
}

// 2. Message storage with partitioning
public class ChatService
{
    private readonly IDatabase _database;
    private readonly ICacheService _cache;
    
    public async Task<ChatMessage> SaveMessageAsync(ChatMessage message)
    {
        message.Id = Guid.NewGuid();
        
        // Partition by date for efficient queries
        var partition = message.Timestamp.ToString("yyyyMM");
        await _database.SaveAsync($"messages_{partition}", message);
        
        // Cache recent messages
        var cacheKey = $"chat:{message.SenderId}:{message.RecipientId}";
        await _cache.ListPushAsync(cacheKey, message, TimeSpan.FromHours(24));
        
        return message;
    }
    
    public async Task<List<ChatMessage>> GetChatHistoryAsync(
        string userId1,
        string userId2,
        int pageSize = 50,
        DateTime? before = null)
    {
        // Try cache first
        var cacheKey = $"chat:{userId1}:{userId2}";
        var cached = await _cache.ListRangeAsync<ChatMessage>(cacheKey, 0, pageSize);
        
        if (cached.Any())
            return cached;
        
        // Fetch from database across partitions
        var messages = await _database.QueryAsync<ChatMessage>(@"
            SELECT * FROM messages_*
            WHERE (SenderId = @userId1 AND RecipientId = @userId2)
               OR (SenderId = @userId2 AND RecipientId = @userId1)
            ORDER BY Timestamp DESC
            LIMIT @pageSize",
            new { userId1, userId2, pageSize });
        
        return messages;
    }
}
```

**Architecture:**
```
Clients (WebSocket) → Load Balancer (Sticky Sessions)
                           ↓
                      API Servers (SignalR)
                           ↓
                      Redis (Backplane)
                           ↓
                  ┌─────────┴─────────┐
                  ↓                   ↓
          Message Database      Presence Service
          (Partitioned)         (Redis)
```

### 40. What are key takeaways for system design interviews?

**Process:**
1. **Clarify requirements:** Functional and non-functional
2. **Estimate scale:** Users, requests, storage
3. **High-level design:** Draw architecture diagram
4. **Deep dive:** Focus on 2-3 components
5. **Trade-offs:** Discuss alternatives
6. **Bottlenecks:** Identify and address

**Key concepts to know:**
- Load balancing
- Caching strategies
- Database scaling (sharding, replication)
- CAP theorem
- Microservices patterns
- Message queues
- CDN
- Rate limiting
- Monitoring

**Communication tips:**
- Think out loud
- Ask clarifying questions
- Start simple, then scale
- Discuss trade-offs
- No perfect solution exists
- Show breadth and depth

**Common mistakes:**
- Jumping to solution too fast
- Over-engineering
- Ignoring scalability
- Not considering trade-offs
- Missing edge cases
- Poor time management

---

## The Design Round

### 41. The design round — the framework that scores you

> [!danger] The single most important thing
> **The framework matters more than the content.** Two candidates can produce the same architecture; the one who *drove the conversation in a visible order* passes. And **talk continuously** — silence reads as not knowing. Narrate even your uncertainty: *"I'm deciding between X and Y; the deciding factor is Z, so I'll take X."*

**The seven steps, with time budget for a 45-minute round:**

| # | Step | Time | What you must produce |
|---|---|---|---|
| 1 | **Clarify requirements** | 5 min | 3–5 functional features, explicitly **out of scope** items, and the non-functionals that matter |
| 2 | **Estimate scale** | 5 min | rps (read vs write), storage, bandwidth — round numbers, out loud |
| 3 | **Define the API contract** | 5 min | 4–6 endpoints with the fields that matter |
| 4 | **Data model** | 5 min | tables/entities, keys, the indexes the access patterns demand |
| 5 | **High-level components** | 10 min | the box diagram: client → CDN → LB → app → cache → DB → queue → workers → storage |
| 6 | **Find the bottleneck and deep-dive** | 10 min | pick the *hard* part yourself and solve it properly |
| 7 | **Trade-offs, failure modes, scale-out** | 5 min | what you'd do at 10× and what breaks first |

**Step 1 — the questions to actually ask** (asking these *is* points):
- Who uses it and for what? Read-heavy or write-heavy?
- How many users — total vs **concurrent**? What's the peak-to-average ratio?
- What must be **strongly consistent**, and what can be stale? (This one question shapes everything.)
- Latency target? Global or single-region? Mobile clients?
- What's **out of scope** — auth, payments, admin, analytics? *Say it out loud and get agreement.*

**Step 2 — estimation cheatsheet** (nobody checks your arithmetic; they check that you *do* it):

```text
concurrent users -> rps:   rps ≈ concurrent / think_time_seconds
                           10,000 concurrent, ~10s between actions -> ~1,000 rps average
peak:                      3–5× average -> plan for ~3,000–5,000 rps
read:write:                browse-style products are 100:1 or worse
storage:                   rows × row_size × retention, then × 2–3 for indexes
bandwidth:                 rps × response_size
handy numbers:             1M rows × 1KB = 1GB · 1 day ≈ 86,400s ≈ 100k s
                           memory read ~100ns · SSD ~100µs · DB query 1–10ms
                           network same-DC <1ms · cross-region 50–150ms
one commodity Postgres:    ~5k–10k simple reads/s, ~1k–5k writes/s (then: cache, replicas, shard)
one app pod:               ~500–2,000 rps for I/O-bound .NET work
```

**Step 6 — the move that gets you hired:** *pick the bottleneck yourself before they ask.* "The interesting problem here isn't the CRUD — it's that N users compete for the same seat. Let me solve that." That sentence converts a generic design into a senior one.

**Step 7 — trade-off vocabulary** to use explicitly: strong vs eventual consistency · latency vs throughput · normalise vs denormalise · sync vs async · cache freshness vs DB load · consistency vs availability under partition · cost vs complexity. Every choice, say **"I'm choosing X, which costs me Y, and I accept it because Z."**

**Anti-patterns that lose marks:** designing before clarifying · reciting Kafka/Kubernetes/microservices with no reason ("we have 30 writes/s — one Postgres and a cache is the right answer, and I'd say so") · going silent while thinking · ignoring failure modes · no numbers · refusing to commit to a decision.

---

### 42. Design a booking system for 10k concurrent users

*(A listing + booking platform — rooms/events/appointments. Practise this one out loud; it exercises every reliability primitive.)*

#### Step 1 — Requirements

**Functional (in scope):** search/browse listings with filters (city, date range, price) · view a listing with availability · **book** a listing for a date range · pay · cancel · view my bookings.
**Out of scope (state it):** reviews, messaging, host onboarding, pricing engine, admin, analytics.

**Non-functional:**
- 10,000 concurrent users; browse-heavy.
- Search p95 < 300 ms; booking confirm p95 < 1 s.
- **No double-booking. Ever.** ← the one hard requirement; everything else is negotiable.
- Availability 99.9%; browsing may serve slightly stale data, **inventory may not**.
- Single region initially, multi-region later.

#### Step 2 — Estimation (say the numbers)

```text
10,000 concurrent, ~10s think time      -> ~1,000 rps average; peak 3×  -> ~3,000 rps
read:write ≈ 100:1                      -> ~2,970 reads/s, ~30 writes/s
  => this is a READ problem with a small, brutally contended WRITE core

Data: 1M listings × 2KB                  -> 2 GB metadata (fits in RAM — cache aggressively)
      1M listings × 365 days availability -> 365M rows -> partition by month
      10M bookings/yr × 1KB              -> 10 GB/yr
      5M images × 500KB                  -> 2.5 TB -> object storage + CDN, never the app servers
Bandwidth: 3,000 rps × 50KB JSON         -> ~150 MB/s dynamic + images offloaded to the CDN
```

**Conclusion to state:** "30 writes/s is trivial for one Postgres. The difficulty is not throughput — it's **contention on a few hot rows** at peak, and read fan-out. So I'll keep a single primary for correctness, and spend my effort on caching, search, and the booking transaction."

#### Step 3 — API contract

```http
GET  /api/listings?city=cairo&from=2026-09-01&to=2026-09-05&guests=2&page=1
     -> 200 { items:[{id,title,thumb,pricePerNight,rating}], nextCursor }   # cursor, not OFFSET

GET  /api/listings/{id}                  -> 200 { ...details, photos[] }
GET  /api/listings/{id}/availability?from=&to=  -> 200 { dates:[{date,remaining,price}] }  # advisory only

POST /api/bookings                       # Idempotency-Key: <client-generated guid>   <-- say this
     { listingId, from, to, guests }
     -> 201 { bookingId, status:"PendingPayment", holdExpiresAt }
     -> 409 { code:"NO_AVAILABILITY" }

POST /api/bookings/{id}/payment          # Idempotency-Key
     -> 202 { status:"Processing" }      # async confirm; poll or webhook/SignalR push

GET  /api/bookings/{id}                  -> 200 { status: Pending|Confirmed|Failed|Cancelled }
POST /api/bookings/{id}/cancel           -> 200
```

**Two decisions to justify:** cursor pagination (deep `OFFSET` degrades linearly and skips rows when data shifts) and **client-generated idempotency keys** on every mutation (a retried booking must not create two bookings — see [[18-Distributed-Systems-Reliability#Idempotency|Idempotency]]).

#### Step 4 — Data model

```sql
listings(id PK, host_id, city, geo, title, description, price_per_night, capacity, status)
  INDEX (city, status) INCLUDE (price_per_night)      -- the browse path

availability(listing_id, date, total_units, booked_units, price)
  PRIMARY KEY (listing_id, date)                      -- clustered: a date range = one range scan
  PARTITION BY RANGE (date)                           -- drop old partitions instead of DELETE

bookings(id PK, listing_id, user_id, from_date, to_date, status,
         idempotency_key UNIQUE, hold_expires_at, total, row_version)
  INDEX (user_id, created_at DESC)                    -- "my bookings"
  INDEX (status, hold_expires_at) WHERE status='PendingPayment'   -- the expiry sweeper

payments(id PK, booking_id, provider_ref UNIQUE, status, amount)
outbox(id PK, type, payload, occurred_on, processed_on NULL)
inbox(message_id PK, processed_on)                    -- consumer dedupe
```

#### Step 5 — Components

```text
                    ┌── CDN (images, static, cached listing pages) ──┐
   Clients ─────────┤                                                 │
                    └── Load Balancer (L7, TLS, health checks) ───────┘
                                   │  round-robin, NO sticky sessions
                    ┌──────────────┴───────────────┐
                    │  Stateless API pods (.NET)   │  autoscale on rps/queue depth
                    └──┬────────┬────────┬─────────┘
                       │        │        │
         Redis ────────┘        │        └──── Elasticsearch/OpenSearch
   (cache, sessions,            │              (search & filters, fed by outbox;
    rate limit, seat hold)      │               eventually consistent — that's fine)
                                │
                    ┌───────────┴────────────┐
                    │ Postgres PRIMARY       │  ← ALL writes, and any read that decides money
                    │  + 2 read replicas     │  ← browse/detail reads
                    └───────────┬────────────┘
                                │ outbox relay
                          RabbitMQ ──► workers: payments, email, search indexing,
                                                hold-expiry sweeper (Hangfire cron)
                    Object storage (S3/Blob) ──► images, served via CDN
```

#### Step 6 — The bottleneck: preventing double-booking

**Name it first:** "Every request path here is cacheable and boring except one — two users booking the last unit at the same instant. That's where I'll spend the time."

**What does *not* work, and why (say these; rejecting wrong answers scores):**

```csharp
// ❌ Check-then-act: a textbook race. Both requests read remaining=1, both book.
var a = await _db.Availability.FirstAsync(...);
if (a.BookedUnits < a.TotalUnits) { a.BookedUnits++; await _db.SaveChangesAsync(); }

// ❌ Redis distributed lock as the source of truth: not safe for correctness.
// A GC pause or failover longer than the TTL means you "hold" a lock you've lost.
// Fine as an optimisation, never as the guarantee. -> see the Redlock caveats.

// ❌ Caching availability and trusting it: the cache is stale by definition.
//    Cache it for DISPLAY, never for the DECISION.
```

**What does work — let the database be the arbiter:**

```sql
-- Atomic conditional update: the WHERE clause IS the check. One statement, no race,
-- no explicit lock, no lost update. Rows-affected = 0 means "someone else got it" -> 409.
UPDATE availability
   SET booked_units = booked_units + 1
 WHERE listing_id = @id
   AND date BETWEEN @from AND @to
   AND booked_units < total_units;
-- rows affected must equal the number of nights, or ROLLBACK.
```

```csharp
// The full write path — deliberately tiny, and it never leaves the database
await using var tx = await _db.Database.BeginTransactionAsync(IsolationLevel.ReadCommitted, ct);

var nights = (to - from).Days;
var claimed = await _db.Database.ExecuteSqlInterpolatedAsync($@"
    UPDATE availability SET booked_units = booked_units + 1
     WHERE listing_id = {id} AND date >= {from} AND date < {to}
       AND booked_units < total_units", ct);

if (claimed != nights) { await tx.RollbackAsync(ct); return Conflict("NO_AVAILABILITY"); }

_db.Bookings.Add(new Booking { ..., Status = PendingPayment,
                               HoldExpiresAt = now.AddMinutes(10),
                               IdempotencyKey = key });        // UNIQUE index = retry-safe
_db.Outbox.Add(new OutboxMessage(nameof(BookingHeld), payload)); // same transaction
await _db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);        // total lock hold: single-digit milliseconds
```

**The three rules to state explicitly:**
1. **The transaction contains no network call.** Payment happens *after* commit, driven by the outbox. Holding a DB transaction open across a 2-second payment gateway call is how you turn 30 writes/s into an outage — locks pile up, the connection pool drains, and the whole API stalls. See [[18-Distributed-Systems-Reliability#Connection pool exhaustion and PgBouncer|pool exhaustion]].
2. **Hold-then-confirm.** The booking is created as `PendingPayment` with a 10-minute TTL; inventory is *reserved*, not sold. A Hangfire sweeper releases expired holds (`UPDATE ... booked_units - 1 WHERE status='PendingPayment' AND hold_expires_at < now()`), and it must be idempotent — releasing twice would oversell.
3. **Payment is a saga.** `hold → authorise → capture → confirm`, with compensations: release hold, void authorisation, refund. Compensation is semantic, not a rollback. See [[18-Distributed-Systems-Reliability#Saga orchestration vs choreography|sagas]].

**"What if one listing goes viral?"** (the follow-up you should invite): that's **hot-row contention** — every writer serialises on the same rows.
- Measure first: even 100 rps on one row is survivable if the transaction is 3 ms.
- **Queue that listing's writes** — a single-partition FIFO per listing turns contention into throughput and gives fair ordering; the client sees `202 Accepted` and polls or gets a SignalR push.
- **Split the counter** into N sub-rows (`unit_bucket 0..9`) and claim from a random one, falling back to a scan of the rest. Removes the single hot row at the cost of a more complex claim.
- **Shed load early**: a token/waiting-room in Redis so 50k people don't queue for 100 units.
- **Never** solve it by caching availability — a cache cannot enforce an invariant.

#### Step 6b — The read path (the other 99% of traffic)

- **CDN** for images and, where allowed, whole listing pages with a short TTL. Cheapest possible win — offloads the majority of bytes before your app is involved.
- **Redis cache-aside** for listing details: `listing:{id}` with a **60s TTL + jitter**, invalidated explicitly when the host edits. Single-flight the rebuild so a viral listing expiring doesn't stampede the DB.
- **Search** in Elasticsearch, fed asynchronously from the outbox. **State the trade-off:** search results lag by seconds and may show a listing that was just booked out — acceptable, because availability is re-checked at booking time and the DB is the arbiter.
- **Read replicas** for browse/detail. Writes and any read that affects a booking go to the **primary**. After a user books, pin them to the primary for ~30s so "My bookings" shows the new booking — [[18-Distributed-Systems-Reliability#Read replicas and replication lag|read-your-own-writes]].
- **Don't cache the availability numbers used for the decision** — cache them for display with a 5s TTL and label them advisory in the API.

#### Step 7 — Failure modes, trade-offs, and 10×

**Failure modes (be ready for any of these):**

| Failure | Behaviour |
|---|---|
| Redis down | Cache reads fail open → DB takes the full read load, so pods must have a small L1 cache + rate limiting; sessions/holds fail closed. Warm on recovery. |
| Payment provider down | Circuit breaker → bookings stay `PendingPayment`; the hold TTL protects inventory automatically. Tell the user honestly. |
| Payment succeeded, our confirm crashed | The outbox + `provider_ref UNIQUE` make the retry idempotent; a reconciliation job compares provider charges to bookings — **money always gets a reconciliation job**. |
| Broker down | Business writes still commit (outbox retains); confirmations and emails are delayed, not lost. |
| Pod dies mid-request | Stateless + idempotency key: the client retries and gets the *same* booking back, not a second one. |
| Replica lag spikes | Drop it from rotation above threshold; critical reads already go to the primary. |

**Trade-offs to state out loud:**
- **One Postgres primary** rather than sharding: 30 writes/s doesn't justify it, and it buys me real transactions for the one invariant that matters. Cost: a single write ceiling and a failover window. I'd shard by `listing_id` (or by city/region) only when writes actually approach the limit.
- **Eventual consistency in search**, strong consistency in inventory — deliberately split, because they have different costs of being wrong.
- **Hold-then-confirm** costs inventory utilisation (units are reserved for people who never pay) and buys a payment flow that can't oversell.
- **Async payment (202)** costs UI complexity and buys short transactions and resilience to a slow provider.

**At 10× (100k concurrent):** more read replicas and heavier CDN/edge caching first · Redis cluster · **partition/shard writes by listing or region** · multi-region with the write primary in one region and reads local · queue-based load levelling for all writes · a waiting room for hot inventory. **Say what breaks first:** database connections and the hot-row transaction — not CPU.

> [!tip] The closing line that lands
> "If I had one more hour, I'd spend it on the payment saga's compensations and the reconciliation job — that's where correctness bugs actually cost money, and it's the part most designs hand-wave."
