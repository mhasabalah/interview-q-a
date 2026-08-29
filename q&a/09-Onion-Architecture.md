---
title: Onion Architecture
aliases: [Onion Architecture]
tags: [architecture, onion-architecture, interview]
order: 9
---

# Onion Architecture Interview Q&A

> [!info]+ Related Notes
> [[08-Clean-Architecture|Clean Architecture]] · [[07-Domain-Driven-Design|Domain-Driven Design]] · [[11-Module-Communication|Module Communication]] · [[17-Architecture-Defense|Architecture Defense]]

> [!tip] Going deeper
> This note shows **how** to build it. [[17-Architecture-Defense|Architecture Defense]] is how you **justify** it under pressure: vertical slice vs layers, MediatR's pipeline, repository-over-EF, and where you sit on the CQRS spectrum.
>
> Onion, Hexagonal and Clean are the **same principle at three resolutions** — protect the domain, invert the dependencies. See the side-by-side in [[20-Choosing-An-Architecture#Axis A — Internal structure|Choosing an Architecture]], and the deployment axis it says nothing about in [[19-Modular-Monolith|Modular Monolith]].

## Fundamentals

### 1. What is Onion Architecture?
Onion Architecture is an architectural pattern that emphasizes separation of concerns through layers arranged in concentric circles (like an onion). The core principle is that dependencies point inward toward the domain model, and outer layers depend on inner layers, never the reverse.

**Created by:** Jeffrey Palermo (2008)

**Key principle:** All coupling is toward the center, and the center has no dependencies on outer layers.

### 2. What are the layers in Onion Architecture?

**From innermost to outermost:**

1. **Domain Model (Core):**
   - Entities
   - Value Objects
   - Domain Events
   - Enums
   - Exceptions
   - No dependencies

2. **Domain Services:**
   - Business logic that doesn't fit in entities
   - Domain interfaces
   - Depends only on Domain Model

3. **Application Services:**
   - Use cases / Application logic
   - Service interfaces
   - DTOs / ViewModels
   - Depends on Domain Services and Domain Model

4. **Infrastructure (Outer Layer):**
   - Data Access (Repositories)
   - External Services
   - File System
   - Email, SMS
   - Logging
   - Implements interfaces from inner layers

5. **Presentation/UI (Outer Layer):**
   - Controllers (API)
   - Views (MVC/Razor)
   - ViewModels
   - Depends on Application Services

### 3. What is the Dependency Rule in Onion Architecture?
Dependencies must point inward. Outer layers can depend on inner layers, but inner layers must never depend on outer layers. This is achieved through Dependency Inversion Principle (interfaces).

```
UI/Infrastructure → Application Services → Domain Services → Domain Model
                                                               (Core)
```

### 4. How does Onion Architecture differ from N-Tier Architecture?

**N-Tier (Traditional):**
- Linear dependency: UI → Business Logic → Data Access
- Database-centric
- Tight coupling to infrastructure
- Hard to test

**Onion Architecture:**
- Circular dependency: All point toward center
- Domain-centric
- Infrastructure isolated
- Highly testable
- Follows Dependency Inversion

### 5. What are the benefits of Onion Architecture?

**Pros:**
- **Testability:** Core business logic isolated, easy to unit test
- **Flexibility:** Easy to swap implementations (databases, frameworks)
- **Maintainability:** Clear separation of concerns
- **Domain-focused:** Business logic is central
- **Independent of frameworks:** Core doesn't depend on external libraries
- **Independent of UI:** Can change UI without affecting core
- **Independent of database:** Can change database without affecting core

**Cons:**
- Steeper learning curve
- More files and interfaces
- Can be overkill for simple CRUD apps
- Initial setup complexity

## Core Domain Layer

### 6. What belongs in the Domain Model layer?

**Domain Entities:**
```csharp
namespace MyApp.Domain.Entities
{
    public class Order
    {
        public Guid Id { get; private set; }
        public string OrderNumber { get; private set; }
        public DateTime OrderDate { get; private set; }
        public OrderStatus Status { get; private set; }
        private List<OrderItem> _items = new();
        public IReadOnlyCollection<OrderItem> Items => _items.AsReadOnly();
        
        // Domain logic
        public void AddItem(Product product, int quantity)
        {
            if (quantity <= 0)
                throw new DomainException("Quantity must be positive");
                
            var item = new OrderItem(product, quantity);
            _items.Add(item);
        }
        
        public void Submit()
        {
            if (!_items.Any())
                throw new DomainException("Cannot submit empty order");
                
            Status = OrderStatus.Submitted;
        }
        
        public decimal CalculateTotal()
        {
            return _items.Sum(i => i.Subtotal);
        }
    }
}
```

**Value Objects:**
```csharp
public class Address : ValueObject
{
    public string Street { get; private set; }
    public string City { get; private set; }
    public string ZipCode { get; private set; }
    
    public Address(string street, string city, string zipCode)
    {
        Street = street ?? throw new ArgumentNullException(nameof(street));
        City = city ?? throw new ArgumentNullException(nameof(city));
        ZipCode = zipCode ?? throw new ArgumentNullException(nameof(zipCode));
    }
    
    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Street;
        yield return City;
        yield return ZipCode;
    }
}
```

**Domain Exceptions:**
```csharp
public class DomainException : Exception
{
    public DomainException(string message) : base(message) { }
}
```

### 7. What are Domain Services?

Domain services contain business logic that doesn't naturally fit within a single entity or involves multiple entities.

```csharp
namespace MyApp.Domain.Services
{
    public interface IOrderPricingService
    {
        decimal CalculatePrice(Order order, Customer customer);
    }
    
    public class OrderPricingService : IOrderPricingService
    {
        public decimal CalculatePrice(Order order, Customer customer)
        {
            decimal baseTotal = order.CalculateTotal();
            
            // Apply customer-specific discount
            if (customer.IsPremium)
                baseTotal *= 0.9m; // 10% discount
                
            // Apply volume discount
            if (order.Items.Count > 10)
                baseTotal *= 0.95m; // 5% discount
                
            return baseTotal;
        }
    }
}
```

### 8. Should the Domain layer have any dependencies?

**NO external dependencies.** The Domain layer should:
- Have no NuGet packages (except maybe for small utility libraries)
- Not reference Entity Framework
- Not reference ASP.NET
- Not reference any infrastructure concerns
- Be pure C# / .NET

**Allowed:**
- Standard .NET types (DateTime, Guid, etc.)
- References between domain entities
- Domain interfaces (defined in domain layer)

### 9. What are Aggregates in Onion Architecture?

Aggregates are clusters of domain objects treated as a single unit. One entity is the aggregate root, and all changes go through it.

```csharp
public class Order // Aggregate Root
{
    public Guid Id { get; private set; }
    private List<OrderItem> _items = new(); // Part of aggregate
    
    // Control access through aggregate root
    public void AddItem(Product product, int quantity)
    {
        var item = new OrderItem(product, quantity);
        _items.Add(item);
    }
    
    // No direct access to modify items
    public IReadOnlyCollection<OrderItem> Items => _items.AsReadOnly();
}

public class OrderItem // Not accessible outside Order
{
    internal OrderItem(Product product, int quantity) // internal constructor
    {
        Product = product;
        Quantity = quantity;
    }
    
    public Product Product { get; private set; }
    public int Quantity { get; private set; }
    public decimal Subtotal => Product.Price * Quantity;
}
```

### 10. How do you implement Domain Events?

```csharp
// Domain Event
public class OrderSubmittedEvent : IDomainEvent
{
    public Guid OrderId { get; }
    public DateTime OccurredOn { get; }
    
    public OrderSubmittedEvent(Guid orderId)
    {
        OrderId = orderId;
        OccurredOn = DateTime.UtcNow;
    }
}

// Entity with events
public class Order
{
    private List<IDomainEvent> _domainEvents = new();
    public IReadOnlyCollection<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();
    
    public void Submit()
    {
        Status = OrderStatus.Submitted;
        _domainEvents.Add(new OrderSubmittedEvent(Id));
    }
    
    public void ClearDomainEvents()
    {
        _domainEvents.Clear();
    }
}
```

## Application Services Layer

### 11. What belongs in the Application Services layer?

**Application Services (Use Cases):**
```csharp
namespace MyApp.Application.Services
{
    public interface IOrderService
    {
        Task<OrderDto> CreateOrderAsync(CreateOrderCommand command);
        Task<OrderDto> GetOrderAsync(Guid id);
    }
    
    public class OrderService : IOrderService
    {
        private readonly IOrderRepository _orderRepository;
        private readonly IOrderPricingService _pricingService;
        private readonly IUnitOfWork _unitOfWork;
        
        public OrderService(
            IOrderRepository orderRepository,
            IOrderPricingService pricingService,
            IUnitOfWork unitOfWork)
        {
            _orderRepository = orderRepository;
            _pricingService = pricingService;
            _unitOfWork = unitOfWork;
        }
        
        public async Task<OrderDto> CreateOrderAsync(CreateOrderCommand command)
        {
            // Application logic orchestration
            var order = new Order(command.CustomerId);
            
            foreach (var item in command.Items)
            {
                order.AddItem(item.Product, item.Quantity);
            }
            
            order.Submit();
            
            await _orderRepository.AddAsync(order);
            await _unitOfWork.CommitAsync();
            
            return MapToDto(order);
        }
        
        public async Task<OrderDto> GetOrderAsync(Guid id)
        {
            var order = await _orderRepository.GetByIdAsync(id);
            return MapToDto(order);
        }
        
        private OrderDto MapToDto(Order order)
        {
            return new OrderDto
            {
                Id = order.Id,
                OrderNumber = order.OrderNumber,
                Status = order.Status.ToString(),
                Items = order.Items.Select(i => new OrderItemDto
                {
                    ProductName = i.Product.Name,
                    Quantity = i.Quantity,
                    Price = i.Subtotal
                }).ToList()
            };
        }
    }
}
```

### 12. What are DTOs and why use them?

Data Transfer Objects carry data between layers without exposing domain entities.

```csharp
namespace MyApp.Application.DTOs
{
    public class OrderDto
    {
        public Guid Id { get; set; }
        public string OrderNumber { get; set; }
        public string Status { get; set; }
        public List<OrderItemDto> Items { get; set; }
    }
    
    public class OrderItemDto
    {
        public string ProductName { get; set; }
        public int Quantity { get; set; }
        public decimal Price { get; set; }
    }
}
```

**Why use DTOs:**
- Decouple internal domain from external representation
- Control what data is exposed
- Flatten complex object graphs
- Optimize for specific use cases
- Prevent over-posting vulnerabilities

### 13. What are Commands and Queries?

**CQRS pattern often used in Application layer:**

**Commands (Write operations):**
```csharp
public class CreateOrderCommand
{
    public Guid CustomerId { get; set; }
    public List<OrderItemCommand> Items { get; set; }
}

public class OrderItemCommand
{
    public Guid ProductId { get; set; }
    public int Quantity { get; set; }
}
```

**Queries (Read operations):**
```csharp
public class GetOrderByIdQuery
{
    public Guid OrderId { get; set; }
}

public class GetOrdersByCustomerQuery
{
    public Guid CustomerId { get; set; }
    public int PageNumber { get; set; }
    public int PageSize { get; set; }
}
```

### 14. How do you implement validators in Application layer?

```csharp
using FluentValidation;

public class CreateOrderCommandValidator : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderCommandValidator()
    {
        RuleFor(x => x.CustomerId)
            .NotEmpty().WithMessage("Customer ID is required");
            
        RuleFor(x => x.Items)
            .NotEmpty().WithMessage("Order must have at least one item")
            .Must(items => items.All(i => i.Quantity > 0))
            .WithMessage("All items must have positive quantity");
    }
}

// Usage in Application Service
public async Task<OrderDto> CreateOrderAsync(CreateOrderCommand command)
{
    var validator = new CreateOrderCommandValidator();
    var validationResult = await validator.ValidateAsync(command);
    
    if (!validationResult.IsValid)
        throw new ValidationException(validationResult.Errors);
        
    // Continue with order creation...
}
```

### 15. What interfaces are defined in Application layer?

**Repository Interfaces:**
```csharp
namespace MyApp.Application.Interfaces
{
    public interface IOrderRepository
    {
        Task<Order> GetByIdAsync(Guid id);
        Task<IEnumerable<Order>> GetByCustomerAsync(Guid customerId);
        Task AddAsync(Order order);
        Task UpdateAsync(Order order);
        Task DeleteAsync(Guid id);
    }
    
    public interface IUnitOfWork
    {
        Task<int> CommitAsync();
    }
}
```

**Infrastructure Service Interfaces:**
```csharp
public interface IEmailService
{
    Task SendEmailAsync(string to, string subject, string body);
}

public interface IPaymentService
{
    Task<PaymentResult> ProcessPaymentAsync(PaymentRequest request);
}
```

## Infrastructure Layer

### 16. What belongs in the Infrastructure layer?

**Repository Implementations:**
```csharp
namespace MyApp.Infrastructure.Repositories
{
    public class OrderRepository : IOrderRepository
    {
        private readonly ApplicationDbContext _context;
        
        public OrderRepository(ApplicationDbContext context)
        {
            _context = context;
        }
        
        public async Task<Order> GetByIdAsync(Guid id)
        {
            return await _context.Orders
                .Include(o => o.Items)
                .ThenInclude(i => i.Product)
                .FirstOrDefaultAsync(o => o.Id == id);
        }
        
        public async Task AddAsync(Order order)
        {
            await _context.Orders.AddAsync(order);
        }
        
        public async Task UpdateAsync(Order order)
        {
            _context.Orders.Update(order);
        }
    }
}
```

**DbContext:**
```csharp
namespace MyApp.Infrastructure.Data
{
    public class ApplicationDbContext : DbContext, IUnitOfWork
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }
        
        public DbSet<Order> Orders { get; set; }
        public DbSet<Product> Products { get; set; }
        public DbSet<Customer> Customers { get; set; }
        
        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
        }
        
        public async Task<int> CommitAsync()
        {
            return await SaveChangesAsync();
        }
    }
}
```

**Entity Configurations:**
```csharp
public class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> builder)
    {
        builder.HasKey(o => o.Id);
        
        builder.Property(o => o.OrderNumber)
            .IsRequired()
            .HasMaxLength(50);
            
        builder.HasMany(o => o.Items)
            .WithOne()
            .HasForeignKey("OrderId")
            .OnDelete(DeleteBehavior.Cascade);
            
        builder.Ignore(o => o.DomainEvents);
    }
}
```

### 17. How do you implement External Services?

```csharp
namespace MyApp.Infrastructure.Services
{
    public class EmailService : IEmailService
    {
        private readonly IConfiguration _configuration;
        private readonly ILogger<EmailService> _logger;
        
        public EmailService(IConfiguration configuration, ILogger<EmailService> logger)
        {
            _configuration = configuration;
            _logger = logger;
        }
        
        public async Task SendEmailAsync(string to, string subject, string body)
        {
            // SMTP implementation
            using var client = new SmtpClient(_configuration["Email:Host"])
            {
                Port = int.Parse(_configuration["Email:Port"]),
                Credentials = new NetworkCredential(
                    _configuration["Email:Username"],
                    _configuration["Email:Password"]
                ),
                EnableSsl = true
            };
            
            var mailMessage = new MailMessage
            {
                From = new MailAddress(_configuration["Email:From"]),
                Subject = subject,
                Body = body,
                IsBodyHtml = true
            };
            mailMessage.To.Add(to);
            
            await client.SendMailAsync(mailMessage);
            _logger.LogInformation($"Email sent to {to}");
        }
    }
}
```

### 18. How do you configure Dependency Injection?

```csharp
namespace MyApp.Infrastructure
{
    public static class DependencyInjection
    {
        public static IServiceCollection AddInfrastructure(
            this IServiceCollection services,
            IConfiguration configuration)
        {
            // Database
            services.AddDbContext<ApplicationDbContext>(options =>
                options.UseSqlServer(
                    configuration.GetConnectionString("DefaultConnection")));
            
            // Unit of Work
            services.AddScoped<IUnitOfWork>(provider =>
                provider.GetRequiredService<ApplicationDbContext>());
            
            // Repositories
            services.AddScoped<IOrderRepository, OrderRepository>();
            services.AddScoped<IProductRepository, ProductRepository>();
            services.AddScoped<ICustomerRepository, CustomerRepository>();
            
            // External Services
            services.AddTransient<IEmailService, EmailService>();
            services.AddTransient<IPaymentService, PaymentService>();
            
            return services;
        }
    }
}
```

### 19. How do you handle database migrations?

```bash
# Add migration
dotnet ef migrations add InitialCreate --project Infrastructure --startup-project API

# Update database
dotnet ef database update --project Infrastructure --startup-project API
```

```csharp
// Seed data
public static class DatabaseSeeder
{
    public static async Task SeedAsync(ApplicationDbContext context)
    {
        if (!await context.Products.AnyAsync())
        {
            var products = new List<Product>
            {
                new Product("Laptop", 999.99m),
                new Product("Mouse", 29.99m),
                new Product("Keyboard", 79.99m)
            };
            
            await context.Products.AddRangeAsync(products);
            await context.SaveChangesAsync();
        }
    }
}
```

### 20. How do you implement caching?

```csharp
public class CachedProductRepository : IProductRepository
{
    private readonly IProductRepository _productRepository;
    private readonly IMemoryCache _cache;
    private readonly TimeSpan _cacheDuration = TimeSpan.FromMinutes(10);
    
    public CachedProductRepository(
        IProductRepository productRepository,
        IMemoryCache cache)
    {
        _productRepository = productRepository;
        _cache = cache;
    }
    
    public async Task<Product> GetByIdAsync(Guid id)
    {
        string cacheKey = $"product_{id}";
        
        if (_cache.TryGetValue(cacheKey, out Product product))
            return product;
        
        product = await _productRepository.GetByIdAsync(id);
        
        _cache.Set(cacheKey, product, _cacheDuration);
        
        return product;
    }
}
```

## Presentation Layer

### 21. How do you structure the API/Presentation layer?

```csharp
namespace MyApp.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class OrdersController : ControllerBase
    {
        private readonly IOrderService _orderService;
        private readonly ILogger<OrdersController> _logger;
        
        public OrdersController(
            IOrderService orderService,
            ILogger<OrdersController> logger)
        {
            _orderService = orderService;
            _logger = logger;
        }
        
        [HttpGet("{id}")]
        public async Task<ActionResult<OrderDto>> GetOrder(Guid id)
        {
            try
            {
                var order = await _orderService.GetOrderAsync(id);
                
                if (order == null)
                    return NotFound();
                
                return Ok(order);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error retrieving order {id}");
                return StatusCode(500, "An error occurred");
            }
        }
        
        [HttpPost]
        public async Task<ActionResult<OrderDto>> CreateOrder(CreateOrderCommand command)
        {
            try
            {
                var order = await _orderService.CreateOrderAsync(command);
                return CreatedAtAction(nameof(GetOrder), new { id = order.Id }, order);
            }
            catch (ValidationException ex)
            {
                return BadRequest(ex.Errors);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating order");
                return StatusCode(500, "An error occurred");
            }
        }
    }
}
```

### 22. How do you configure Program.cs?

```csharp
var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Application Services
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<IOrderPricingService, OrderPricingService>();

// Infrastructure
builder.Services.AddInfrastructure(builder.Configuration);

// AutoMapper
builder.Services.AddAutoMapper(typeof(Program));

// Validation
builder.Services.AddValidatorsFromAssemblyContaining<CreateOrderCommandValidator>();

// Logging
builder.Logging.AddConsole();
builder.Logging.AddDebug();

var app = builder.Build();

// Configure middleware pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

// Seed database
using (var scope = app.Services.CreateScope())
{
    var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    await context.Database.MigrateAsync();
    await DatabaseSeeder.SeedAsync(context);
}

app.Run();
```

### 23. How do you implement global exception handling?

```csharp
public class GlobalExceptionHandler : IExceptionHandler
{
    private readonly ILogger<GlobalExceptionHandler> _logger;
    
    public GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger)
    {
        _logger = logger;
    }
    
    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken)
    {
        _logger.LogError(exception, "An error occurred: {Message}", exception.Message);
        
        var (statusCode, message) = exception switch
        {
            DomainException => (StatusCodes.Status400BadRequest, exception.Message),
            ValidationException => (StatusCodes.Status400BadRequest, exception.Message),
            NotFoundException => (StatusCodes.Status404NotFound, exception.Message),
            _ => (StatusCodes.Status500InternalServerError, "An error occurred")
        };
        
        httpContext.Response.StatusCode = statusCode;
        await httpContext.Response.WriteAsJsonAsync(new
        {
            error = message,
            statusCode
        }, cancellationToken);
        
        return true;
    }
}

// Register in Program.cs
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
app.UseExceptionHandler();
```

## Testing

### 24. How do you unit test the Domain layer?

```csharp
public class OrderTests
{
    [Fact]
    public void AddItem_WithValidQuantity_ShouldAddItem()
    {
        // Arrange
        var order = new Order(Guid.NewGuid());
        var product = new Product("Test Product", 10.00m);
        
        // Act
        order.AddItem(product, 2);
        
        // Assert
        Assert.Single(order.Items);
        Assert.Equal(2, order.Items.First().Quantity);
    }
    
    [Fact]
    public void AddItem_WithZeroQuantity_ShouldThrowException()
    {
        // Arrange
        var order = new Order(Guid.NewGuid());
        var product = new Product("Test Product", 10.00m);
        
        // Act & Assert
        Assert.Throws<DomainException>(() => order.AddItem(product, 0));
    }
    
    [Fact]
    public void Submit_WithNoItems_ShouldThrowException()
    {
        // Arrange
        var order = new Order(Guid.NewGuid());
        
        // Act & Assert
        Assert.Throws<DomainException>(() => order.Submit());
    }
    
    [Fact]
    public void CalculateTotal_ShouldReturnCorrectSum()
    {
        // Arrange
        var order = new Order(Guid.NewGuid());
        order.AddItem(new Product("Product 1", 10.00m), 2);
        order.AddItem(new Product("Product 2", 5.00m), 3);
        
        // Act
        var total = order.CalculateTotal();
        
        // Assert
        Assert.Equal(35.00m, total);
    }
}
```

### 25. How do you unit test Application Services?

```csharp
public class OrderServiceTests
{
    private readonly Mock<IOrderRepository> _orderRepositoryMock;
    private readonly Mock<IUnitOfWork> _unitOfWorkMock;
    private readonly Mock<IOrderPricingService> _pricingServiceMock;
    private readonly OrderService _orderService;
    
    public OrderServiceTests()
    {
        _orderRepositoryMock = new Mock<IOrderRepository>();
        _unitOfWorkMock = new Mock<IUnitOfWork>();
        _pricingServiceMock = new Mock<IOrderPricingService>();
        
        _orderService = new OrderService(
            _orderRepositoryMock.Object,
            _pricingServiceMock.Object,
            _unitOfWorkMock.Object);
    }
    
    [Fact]
    public async Task CreateOrderAsync_WithValidCommand_ShouldCreateOrder()
    {
        // Arrange
        var command = new CreateOrderCommand
        {
            CustomerId = Guid.NewGuid(),
            Items = new List<OrderItemCommand>
            {
                new OrderItemCommand { ProductId = Guid.NewGuid(), Quantity = 2 }
            }
        };
        
        _unitOfWorkMock.Setup(x => x.CommitAsync()).ReturnsAsync(1);
        
        // Act
        var result = await _orderService.CreateOrderAsync(command);
        
        // Assert
        Assert.NotNull(result);
        _orderRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Order>()), Times.Once);
        _unitOfWorkMock.Verify(x => x.CommitAsync(), Times.Once);
    }
}
```

### 26. How do you do integration testing?

```csharp
public class OrdersControllerIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;
    private readonly WebApplicationFactory<Program> _factory;
    
    public OrdersControllerIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace with in-memory database
                var descriptor = services.SingleOrDefault(
                    d => d.ServiceType == typeof(DbContextOptions<ApplicationDbContext>));
                
                if (descriptor != null)
                    services.Remove(descriptor);
                
                services.AddDbContext<ApplicationDbContext>(options =>
                {
                    options.UseInMemoryDatabase("TestDb");
                });
            });
        });
        
        _client = _factory.CreateClient();
    }
    
    [Fact]
    public async Task GetOrder_WithValidId_ReturnsOrder()
    {
        // Arrange
        var orderId = await CreateTestOrder();
        
        // Act
        var response = await _client.GetAsync($"/api/orders/{orderId}");
        
        // Assert
        response.EnsureSuccessStatusCode();
        var order = await response.Content.ReadFromJsonAsync<OrderDto>();
        Assert.NotNull(order);
        Assert.Equal(orderId, order.Id);
    }
    
    private async Task<Guid> CreateTestOrder()
    {
        var command = new CreateOrderCommand
        {
            CustomerId = Guid.NewGuid(),
            Items = new List<OrderItemCommand>
            {
                new OrderItemCommand { ProductId = Guid.NewGuid(), Quantity = 1 }
            }
        };
        
        var response = await _client.PostAsJsonAsync("/api/orders", command);
        var order = await response.Content.ReadFromJsonAsync<OrderDto>();
        return order.Id;
    }
}
```

## Project Structure

### 27. What is the recommended folder structure?

```
Solution/
├── src/
│   ├── MyApp.Domain/                    # Core layer
│   │   ├── Entities/
│   │   │   ├── Order.cs
│   │   │   ├── Product.cs
│   │   │   └── Customer.cs
│   │   ├── ValueObjects/
│   │   │   └── Address.cs
│   │   ├── Enums/
│   │   │   └── OrderStatus.cs
│   │   ├── Exceptions/
│   │   │   └── DomainException.cs
│   │   └── Events/
│   │       └── OrderSubmittedEvent.cs
│   │
│   ├── MyApp.Domain.Services/           # Domain Services layer
│   │   └── IOrderPricingService.cs
│   │   └── OrderPricingService.cs
│   │
│   ├── MyApp.Application/               # Application layer
│   │   ├── Interfaces/
│   │   │   ├── IOrderRepository.cs
│   │   │   └── IUnitOfWork.cs
│   │   ├── Services/
│   │   │   ├── IOrderService.cs
│   │   │   └── OrderService.cs
│   │   ├── DTOs/
│   │   │   └── OrderDto.cs
│   │   ├── Commands/
│   │   │   └── CreateOrderCommand.cs
│   │   ├── Queries/
│   │   │   └── GetOrderByIdQuery.cs
│   │   └── Validators/
│   │       └── CreateOrderCommandValidator.cs
│   │
│   ├── MyApp.Infrastructure/            # Infrastructure layer
│   │   ├── Data/
│   │   │   ├── ApplicationDbContext.cs
│   │   │   └── Configurations/
│   │   │       └── OrderConfiguration.cs
│   │   ├── Repositories/
│   │   │   └── OrderRepository.cs
│   │   ├── Services/
│   │   │   ├── EmailService.cs
│   │   │   └── PaymentService.cs
│   │   └── DependencyInjection.cs
│   │
│   └── MyApp.API/                       # Presentation layer
│       ├── Controllers/
│       │   └── OrdersController.cs
│       ├── Middleware/
│       │   └── GlobalExceptionHandler.cs
│       ├── Program.cs
│       └── appsettings.json
│
└── tests/
    ├── MyApp.Domain.Tests/
    ├── MyApp.Application.Tests/
    └── MyApp.API.IntegrationTests/
```

### 28. What are the dependencies between projects?

```
API          → Application, Infrastructure
Infrastructure → Application, Domain
Application   → Domain
Domain        → (No dependencies)
```

**.csproj references:**
```xml
<!-- API -->
<ItemGroup>
  <ProjectReference Include="..\MyApp.Application\MyApp.Application.csproj" />
  <ProjectReference Include="..\MyApp.Infrastructure\MyApp.Infrastructure.csproj" />
</ItemGroup>

<!-- Infrastructure -->
<ItemGroup>
  <ProjectReference Include="..\MyApp.Application\MyApp.Application.csproj" />
  <ProjectReference Include="..\MyApp.Domain\MyApp.Domain.csproj" />
</ItemGroup>

<!-- Application -->
<ItemGroup>
  <ProjectReference Include="..\MyApp.Domain\MyApp.Domain.csproj" />
</ItemGroup>

<!-- Domain - No project references -->
```

## Advanced Patterns

### 29. How do you implement CQRS in Onion Architecture?

```csharp
// Command Handler
public interface ICommandHandler<TCommand, TResult>
{
    Task<TResult> HandleAsync(TCommand command);
}

public class CreateOrderCommandHandler : ICommandHandler<CreateOrderCommand, OrderDto>
{
    private readonly IOrderRepository _repository;
    private readonly IUnitOfWork _unitOfWork;
    
    public CreateOrderCommandHandler(IOrderRepository repository, IUnitOfWork unitOfWork)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
    }
    
    public async Task<OrderDto> HandleAsync(CreateOrderCommand command)
    {
        var order = new Order(command.CustomerId);
        // ... create order logic
        await _repository.AddAsync(order);
        await _unitOfWork.CommitAsync();
        return MapToDto(order);
    }
}

// Query Handler
public interface IQueryHandler<TQuery, TResult>
{
    Task<TResult> HandleAsync(TQuery query);
}

public class GetOrderByIdQueryHandler : IQueryHandler<GetOrderByIdQuery, OrderDto>
{
    private readonly IOrderRepository _repository;
    
    public GetOrderByIdQueryHandler(IOrderRepository repository)
    {
        _repository = repository;
    }
    
    public async Task<OrderDto> HandleAsync(GetOrderByIdQuery query)
    {
        var order = await _repository.GetByIdAsync(query.OrderId);
        return MapToDto(order);
    }
}
```

### 30. How do you implement MediatR pattern?

```csharp
// Install MediatR
// dotnet add package MediatR

// Command
public class CreateOrderCommand : IRequest<OrderDto>
{
    public Guid CustomerId { get; set; }
    public List<OrderItemCommand> Items { get; set; }
}

// Handler
public class CreateOrderCommandHandler : IRequestHandler<CreateOrderCommand, OrderDto>
{
    private readonly IOrderRepository _repository;
    private readonly IUnitOfWork _unitOfWork;
    
    public CreateOrderCommandHandler(IOrderRepository repository, IUnitOfWork unitOfWork)
    {
        _repository = repository;
        _unitOfWork = unitOfWork;
    }
    
    public async Task<OrderDto> Handle(CreateOrderCommand request, CancellationToken cancellationToken)
    {
        var order = new Order(request.CustomerId);
        // ... logic
        await _repository.AddAsync(order);
        await _unitOfWork.CommitAsync();
        return MapToDto(order);
    }
}

// Controller
[HttpPost]
public async Task<ActionResult<OrderDto>> CreateOrder(CreateOrderCommand command)
{
    var result = await _mediator.Send(command);
    return CreatedAtAction(nameof(GetOrder), new { id = result.Id }, result);
}

// Program.cs registration
builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(Program).Assembly));
```

### 31. How do you implement Specification pattern?

```csharp
// Base Specification
public interface ISpecification<T>
{
    Expression<Func<T, bool>> Criteria { get; }
    List<Expression<Func<T, object>>> Includes { get; }
}

public abstract class BaseSpecification<T> : ISpecification<T>
{
    public Expression<Func<T, bool>> Criteria { get; }
    public List<Expression<Func<T, object>>> Includes { get; } = new();
    
    protected BaseSpecification(Expression<Func<T, bool>> criteria)
    {
        Criteria = criteria;
    }
    
    protected void AddInclude(Expression<Func<T, object>> includeExpression)
    {
        Includes.Add(includeExpression);
    }
}

// Concrete Specification
public class OrdersByCustomerSpecification : BaseSpecification<Order>
{
    public OrdersByCustomerSpecification(Guid customerId)
        : base(o => o.CustomerId == customerId)
    {
        AddInclude(o => o.Items);
        AddInclude(o => o.Customer);
    }
}

// Repository with Specification
public interface IRepository<T>
{
    Task<T> GetBySpecAsync(ISpecification<T> spec);
    Task<IEnumerable<T>> ListAsync(ISpecification<T> spec);
}

public class Repository<T> : IRepository<T> where T : class
{
    private readonly ApplicationDbContext _context;
    
    public async Task<IEnumerable<T>> ListAsync(ISpecification<T> spec)
    {
        var query = _context.Set<T>().AsQueryable();
        
        if (spec.Criteria != null)
            query = query.Where(spec.Criteria);
        
        query = spec.Includes.Aggregate(query, (current, include) => current.Include(include));
        
        return await query.ToListAsync();
    }
}

// Usage
var spec = new OrdersByCustomerSpecification(customerId);
var orders = await _repository.ListAsync(spec);
```

### 32. How do you implement Unit of Work pattern?

```csharp
public interface IUnitOfWork : IDisposable
{
    IOrderRepository Orders { get; }
    IProductRepository Products { get; }
    ICustomerRepository Customers { get; }
    Task<int> CommitAsync();
    Task RollbackAsync();
}

public class UnitOfWork : IUnitOfWork
{
    private readonly ApplicationDbContext _context;
    private IOrderRepository _orders;
    private IProductRepository _products;
    private ICustomerRepository _customers;
    
    public UnitOfWork(ApplicationDbContext context)
    {
        _context = context;
    }
    
    public IOrderRepository Orders => 
        _orders ??= new OrderRepository(_context);
    
    public IProductRepository Products => 
        _products ??= new ProductRepository(_context);
    
    public ICustomerRepository Customers => 
        _customers ??= new CustomerRepository(_context);
    
    public async Task<int> CommitAsync()
    {
        return await _context.SaveChangesAsync();
    }
    
    public async Task RollbackAsync()
    {
        await _context.DisposeAsync();
    }
    
    public void Dispose()
    {
        _context.Dispose();
    }
}

// Usage
using (var unitOfWork = new UnitOfWork(context))
{
    var order = await unitOfWork.Orders.GetByIdAsync(orderId);
    order.Submit();
    
    await unitOfWork.Products.UpdateStockAsync(productId, -quantity);
    
    await unitOfWork.CommitAsync();
}
```

## Best Practices

### 33. What are Onion Architecture best practices?

1. **Keep Domain Pure:** No external dependencies
2. **Use Interfaces:** Define contracts in inner layers
3. **Dependency Inversion:** Outer layers implement inner layer interfaces
4. **Single Responsibility:** Each layer has one reason to change
5. **Immutability:** Use private setters, value objects
6. **Rich Domain Models:** Business logic in entities
7. **Thin Controllers:** Delegate to application services
8. **Use DTOs:** Don't expose domain entities to UI
9. **Aggregate Boundaries:** Maintain consistency within aggregates
10. **Test Thoroughly:** Unit test domain, integration test infrastructure

### 34. What are common mistakes to avoid?

1. **Anemic Domain Model:** Putting all logic in services
2. **Breaking Dependency Rule:** Inner layers depending on outer
3. **Exposing Entities:** Returning domain entities from API
4. **Leaky Abstractions:** Infrastructure concerns in domain
5. **God Services:** Services doing too much
6. **Ignoring Aggregates:** Direct access to child entities
7. **Overengineering:** Using Onion for simple CRUD apps
8. **Poor Testing:** Not isolating layers in tests
9. **Inconsistent Boundaries:** Mixing layer responsibilities
10. **No Validation:** Skipping input validation

### 35. When should you use Onion Architecture?

**Use Onion when:**
- Complex business logic
- Long-term maintenance expected
- Team size > 3 developers
- Domain-driven design needed
- Multiple UI or integration points
- High testability required
- Frequent technology changes

**Don't use Onion when:**
- Simple CRUD application
- Prototype or proof of concept
- Single developer, short project
- Performance is critical (overhead)
- Team unfamiliar with patterns

### 36. How does Onion compare to Clean Architecture?

**Similarities:**
- Both are domain-centric
- Dependency Inversion Principle
- Testability focus
- Layer independence

**Differences:**
- **Onion:** Emphasizes concentric circles, 4-5 layers
- **Clean:** More flexible, use cases as central concept
- **Terminology:** Different layer names
- **Strictness:** Onion is more prescriptive

**In practice:** Very similar, often used interchangeably

### 37. How do you handle cross-cutting concerns?

```csharp
// Logging with decorator pattern
public class LoggingOrderService : IOrderService
{
    private readonly IOrderService _orderService;
    private readonly ILogger<LoggingOrderService> _logger;
    
    public LoggingOrderService(IOrderService orderService, ILogger<LoggingOrderService> logger)
    {
        _orderService = orderService;
        _logger = logger;
    }
    
    public async Task<OrderDto> CreateOrderAsync(CreateOrderCommand command)
    {
        _logger.LogInformation("Creating order for customer {CustomerId}", command.CustomerId);
        
        try
        {
            var result = await _orderService.CreateOrderAsync(command);
            _logger.LogInformation("Order {OrderId} created successfully", result.Id);
            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating order");
            throw;
        }
    }
}

// Or use MediatR pipelines
public class LoggingBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
{
    private readonly ILogger<LoggingBehavior<TRequest, TResponse>> _logger;
    
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Handling {RequestName}", typeof(TRequest).Name);
        var response = await next();
        _logger.LogInformation("Handled {RequestName}", typeof(TRequest).Name);
        return response;
    }
}
```

### 38. How do you version your API?

```csharp
// Install package
// dotnet add package Asp.Versioning.Mvc

// Program.cs
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
});

// Controller
[ApiController]
[ApiVersion("1.0")]
[Route("api/v{version:apiVersion}/[controller]")]
public class OrdersController : ControllerBase
{
    // v1 endpoints
}

[ApiController]
[ApiVersion("2.0")]
[Route("api/v{version:apiVersion}/[controller]")]
public class OrdersV2Controller : ControllerBase
{
    // v2 endpoints with breaking changes
}
```

### 39. How do you implement authentication and authorization?

```csharp
// Program.cs
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]))
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("RequireAdminRole", policy => policy.RequireRole("Admin"));
});

// Controller
[Authorize]
[HttpGet("{id}")]
public async Task<ActionResult<OrderDto>> GetOrder(Guid id)
{
    // Authenticated users only
}

[Authorize(Policy = "RequireAdminRole")]
[HttpDelete("{id}")]
public async Task<ActionResult> DeleteOrder(Guid id)
{
    // Admin only
}
```

### 40. What tools and libraries complement Onion Architecture?

**Essential:**
- **Entity Framework Core:** ORM for data access
- **AutoMapper:** DTO mapping
- **FluentValidation:** Input validation
- **MediatR:** CQRS implementation
- **Serilog:** Logging

**Optional:**
- **Dapper:** Lightweight ORM for queries
- **Polly:** Resilience and retry policies
- **Hangfire:** Background jobs
- **StackExchange.Redis:** Distributed caching
- **MassTransit:** Message bus
- **Swashbuckle:** API documentation (Swagger)
- **xUnit/NUnit:** Testing frameworks
- **Moq/NSubstitute:** Mocking frameworks

```bash
# Install common packages
dotnet add package Microsoft.EntityFrameworkCore.SqlServer
dotnet add package AutoMapper.Extensions.Microsoft.DependencyInjection
dotnet add package FluentValidation.DependencyInjectionExtensions
dotnet add package MediatR
dotnet add package Serilog.AspNetCore
```
