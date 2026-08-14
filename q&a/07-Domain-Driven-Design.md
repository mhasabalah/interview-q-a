---
title: Domain-Driven Design
aliases: [DDD, Domain-Driven Design]
tags: [ddd, architecture, interview]
order: 7
---

# Domain-Driven Design (DDD) - Interview Q&A

> [!info]+ Related Notes
> [[08-Clean-Architecture|Clean Architecture]] · [[09-Onion-Architecture|Onion Architecture]] · [[06-Database|Database]]

## Overview

**Q: What is Domain-Driven Design?**

A: Approach to software development that focuses on complex domain logic. Places domain model at center of development. Emphasizes collaboration between technical and domain experts. Uses ubiquitous language.

**Core Concepts:**
- Ubiquitous Language
- Bounded Contexts
- Entities
- Value Objects
- Aggregates
- Domain Events
- Repositories
- Domain Services

---

## Ubiquitous Language

**Q: What is Ubiquitous Language?**

A: Common language shared by developers and domain experts. Used in code, conversations, and documentation. Reduces translation errors. Model directly reflects business terminology.

```csharp
// BAD: Technical terms
public class DataRecord
{
    public int RecordId { get; set; }
    public string Field1 { get; set; }
    public decimal Field2 { get; set; }
}

// GOOD: Business terms (Ubiquitous Language)
public class Order
{
    public int OrderId { get; set; }
    public Customer Customer { get; set; }
    public decimal TotalAmount { get; set; }
    public OrderStatus Status { get; set; }
}
```

---

## Building Blocks

### Entities

**Q: What is an Entity in DDD?**

A: Object with unique identity that persists over time. Defined by ID, not attributes. Mutable. Tracked throughout lifecycle.

```csharp
public class Order
{
    public int OrderId { get; private set; }  // Identity
    public DateTime OrderDate { get; private set; }
    public OrderStatus Status { get; private set; }
    
    private readonly List<OrderLine> _orderLines = new();
    public IReadOnlyCollection<OrderLine> OrderLines => _orderLines.AsReadOnly();
    
    // Constructor
    private Order() { }
    
    public static Order Create(Customer customer)
    {
        return new Order
        {
            OrderDate = DateTime.UtcNow,
            Status = OrderStatus.Pending
        };
    }
    
    // Business logic
    public void AddOrderLine(Product product, int quantity)
    {
        if (Status != OrderStatus.Pending)
            throw new DomainException("Cannot modify non-pending order");
        
        var orderLine = OrderLine.Create(product, quantity);
        _orderLines.Add(orderLine);
    }
    
    public void Submit()
    {
        if (!_orderLines.Any())
            throw new DomainException("Cannot submit empty order");
        
        Status = OrderStatus.Submitted;
        AddDomainEvent(new OrderSubmittedEvent(this));
    }
}

// Two orders with same data but different IDs are different entities
var order1 = new Order { OrderId = 1, TotalAmount = 100 };
var order2 = new Order { OrderId = 2, TotalAmount = 100 };
// order1 != order2 (different identity)
```

---

### Value Objects

**Q: What is a Value Object?**

A: Object without identity. Defined by attributes. Immutable. Equality based on value. Can be freely replaced.

```csharp
public class Money : ValueObject
{
    public decimal Amount { get; private set; }
    public string Currency { get; private set; }
    
    private Money() { }
    
    public static Money Create(decimal amount, string currency)
    {
        if (amount < 0)
            throw new DomainException("Amount cannot be negative");
        
        if (string.IsNullOrWhiteSpace(currency))
            throw new DomainException("Currency is required");
        
        return new Money { Amount = amount, Currency = currency };
    }
    
    // Value objects are immutable - return new instance
    public Money Add(Money other)
    {
        if (Currency != other.Currency)
            throw new DomainException("Cannot add different currencies");
        
        return Create(Amount + other.Amount, Currency);
    }
    
    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Amount;
        yield return Currency;
    }
}

// Usage
var price1 = Money.Create(100, "USD");
var price2 = Money.Create(100, "USD");
// price1 == price2 (same value)

var price3 = price1.Add(price2);  // Returns new Money instance
```

**More Value Objects:**
```csharp
public class Address : ValueObject
{
    public string Street { get; private set; }
    public string City { get; private set; }
    public string ZipCode { get; private set; }
    public string Country { get; private set; }
    
    public static Address Create(string street, string city, string zipCode, string country)
    {
        // Validation
        return new Address 
        { 
            Street = street, 
            City = city, 
            ZipCode = zipCode, 
            Country = country 
        };
    }
    
    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Street;
        yield return City;
        yield return ZipCode;
        yield return Country;
    }
}

public class EmailAddress : ValueObject
{
    public string Value { get; private set; }
    
    public static EmailAddress Create(string email)
    {
        if (string.IsNullOrWhiteSpace(email))
            throw new DomainException("Email cannot be empty");
        
        if (!email.Contains("@"))
            throw new DomainException("Invalid email format");
        
        return new EmailAddress { Value = email.ToLower() };
    }
    
    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Value;
    }
}
```

---

### Aggregates & Aggregate Root

**Q: What is an Aggregate?**

A: Cluster of domain objects (entities and value objects) treated as single unit. Ensures consistency. Has clear boundary. Aggregate Root is entry point.

**Q: What is Aggregate Root?**

A: Entity that serves as entry point to aggregate. Only object external code can reference. Enforces invariants for entire aggregate.

```csharp
// Aggregate Root
public class Order  // Aggregate Root
{
    public int OrderId { get; private set; }
    public Customer Customer { get; private set; }
    public OrderStatus Status { get; private set; }
    
    // Internal entities - only accessible through root
    private readonly List<OrderLine> _orderLines = new();
    public IReadOnlyCollection<OrderLine> OrderLines => _orderLines.AsReadOnly();
    
    // Value object
    public Money TotalAmount => Money.Create(
        _orderLines.Sum(ol => ol.Price.Amount * ol.Quantity), 
        "USD"
    );
    
    // Only way to modify aggregate
    public void AddOrderLine(Product product, int quantity)
    {
        // Enforce invariants
        if (Status != OrderStatus.Pending)
            throw new DomainException("Cannot modify submitted order");
        
        if (quantity <= 0)
            throw new DomainException("Quantity must be positive");
        
        var orderLine = OrderLine.Create(product, quantity);
        _orderLines.Add(orderLine);
        
        // Maintain consistency - check business rules
        if (TotalAmount.Amount > 10000)
            throw new DomainException("Order exceeds maximum amount");
    }
    
    public void RemoveOrderLine(int orderLineId)
    {
        if (Status != OrderStatus.Pending)
            throw new DomainException("Cannot modify submitted order");
        
        var orderLine = _orderLines.FirstOrDefault(ol => ol.Id == orderLineId);
        if (orderLine != null)
        {
            _orderLines.Remove(orderLine);
        }
    }
    
    public void Submit()
    {
        if (!_orderLines.Any())
            throw new DomainException("Cannot submit empty order");
        
        Status = OrderStatus.Submitted;
        AddDomainEvent(new OrderSubmittedEvent(this));
    }
}

// Entity within aggregate - only accessible through Order
public class OrderLine
{
    public int Id { get; private set; }
    public Product Product { get; private set; }
    public int Quantity { get; private set; }
    public Money Price { get; private set; }
    
    private OrderLine() { }
    
    internal static OrderLine Create(Product product, int quantity)
    {
        return new OrderLine
        {
            Product = product,
            Quantity = quantity,
            Price = product.Price
        };
    }
}

// Usage - Always through Aggregate Root
var order = Order.Create(customer);
order.AddOrderLine(product, 5);  // Through root
order.RemoveOrderLine(1);        // Through root
order.Submit();                  // Through root

// NOT ALLOWED - cannot modify OrderLine directly
// var orderLine = order.OrderLines.First();
// orderLine.Quantity = 10;  // Readonly collection prevents this
```

**Aggregate Rules:**
1. Reference other aggregates by ID only
2. One transaction per aggregate
3. Small aggregates (2-3 entities max)
4. Enforce invariants within boundary
5. Only aggregate root has repository

```csharp
// Good: Reference by ID
public class Order
{
    public int CustomerId { get; private set; }  // Reference by ID
    // Not: public Customer Customer { get; set; }
}

// Load related aggregate separately
var order = await _orderRepository.GetByIdAsync(orderId);
var customer = await _customerRepository.GetByIdAsync(order.CustomerId);
```

---

### Domain Events

**Q: What are Domain Events?**

A: Represent something that happened in the domain. Captures business events. Enables decoupling. Supports eventual consistency.

```csharp
// Base domain event
public abstract class DomainEvent
{
    public DateTime OccurredOn { get; protected set; }
    
    protected DomainEvent()
    {
        OccurredOn = DateTime.UtcNow;
    }
}

// Specific domain events
public class OrderSubmittedEvent : DomainEvent
{
    public int OrderId { get; }
    public int CustomerId { get; }
    public decimal TotalAmount { get; }
    
    public OrderSubmittedEvent(Order order)
    {
        OrderId = order.OrderId;
        CustomerId = order.Customer.Id;
        TotalAmount = order.TotalAmount.Amount;
    }
}

public class PaymentProcessedEvent : DomainEvent
{
    public int OrderId { get; }
    public decimal Amount { get; }
    
    public PaymentProcessedEvent(int orderId, decimal amount)
    {
        OrderId = orderId;
        Amount = amount;
    }
}

// Entity with domain events
public abstract class Entity
{
    private readonly List<DomainEvent> _domainEvents = new();
    public IReadOnlyCollection<DomainEvent> DomainEvents => _domainEvents.AsReadOnly();
    
    protected void AddDomainEvent(DomainEvent domainEvent)
    {
        _domainEvents.Add(domainEvent);
    }
    
    public void ClearDomainEvents()
    {
        _domainEvents.Clear();
    }
}

// Usage in aggregate
public class Order : Entity
{
    public void Submit()
    {
        // Business logic
        Status = OrderStatus.Submitted;
        
        // Raise domain event
        AddDomainEvent(new OrderSubmittedEvent(this));
    }
}

// Domain event handler
public class OrderSubmittedEventHandler : INotificationHandler<OrderSubmittedEvent>
{
    private readonly IEmailService _emailService;
    private readonly IInventoryService _inventoryService;
    
    public async Task Handle(OrderSubmittedEvent notification, CancellationToken cancellationToken)
    {
        // Send confirmation email
        await _emailService.SendOrderConfirmationAsync(notification.OrderId);
        
        // Reserve inventory
        await _inventoryService.ReserveItemsAsync(notification.OrderId);
        
        // Can trigger other processes...
    }
}

// Publishing events after SaveChanges
public override async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
{
    var domainEntities = ChangeTracker.Entries<Entity>()
        .Where(x => x.Entity.DomainEvents.Any())
        .ToList();
    
    var domainEvents = domainEntities
        .SelectMany(x => x.Entity.DomainEvents)
        .ToList();
    
    // Clear events before saving
    domainEntities.ForEach(entity => entity.Entity.ClearDomainEvents());
    
    // Save changes
    var result = await base.SaveChangesAsync(cancellationToken);
    
    // Publish events after successful save
    foreach (var domainEvent in domainEvents)
    {
        await _mediator.Publish(domainEvent, cancellationToken);
    }
    
    return result;
}
```

---

### Repositories

**Q: What is Repository in DDD?**

A: Provides collection-like interface for accessing aggregates. Abstracts persistence. One repository per aggregate root. Returns fully formed aggregates.

```csharp
// Repository interface - in Domain layer
public interface IOrderRepository
{
    Task<Order> GetByIdAsync(int id);
    Task<IEnumerable<Order>> GetByCustomerIdAsync(int customerId);
    Task AddAsync(Order order);
    Task UpdateAsync(Order order);
    Task DeleteAsync(int id);
}

// Repository implementation - in Infrastructure layer
public class OrderRepository : IOrderRepository
{
    private readonly AppDbContext _context;
    
    public OrderRepository(AppDbContext context)
    {
        _context = context;
    }
    
    public async Task<Order> GetByIdAsync(int id)
    {
        // Load entire aggregate
        return await _context.Orders
            .Include(o => o.OrderLines)
            .ThenInclude(ol => ol.Product)
            .FirstOrDefaultAsync(o => o.OrderId == id);
    }
    
    public async Task<IEnumerable<Order>> GetByCustomerIdAsync(int customerId)
    {
        return await _context.Orders
            .Include(o => o.OrderLines)
            .Where(o => o.CustomerId == customerId)
            .ToListAsync();
    }
    
    public async Task AddAsync(Order order)
    {
        await _context.Orders.AddAsync(order);
    }
    
    public Task UpdateAsync(Order order)
    {
        _context.Orders.Update(order);
        return Task.CompletedTask;
    }
    
    public async Task DeleteAsync(int id)
    {
        var order = await GetByIdAsync(id);
        if (order != null)
        {
            _context.Orders.Remove(order);
        }
    }
}

// Usage
public class OrderService
{
    private readonly IOrderRepository _orderRepository;
    private readonly IUnitOfWork _unitOfWork;
    
    public async Task ProcessOrderAsync(int orderId)
    {
        var order = await _orderRepository.GetByIdAsync(orderId);
        
        order.Submit();  // Business logic
        
        await _orderRepository.UpdateAsync(order);
        await _unitOfWork.SaveChangesAsync();
    }
}
```

---

### Domain Services

**Q: What is a Domain Service?**

A: Encapsulates domain logic that doesn't naturally fit in entity or value object. Stateless. Operates on multiple aggregates. Contains complex business logic.

```csharp
public interface IOrderPricingService
{
    Money CalculateTotalPrice(Order order, Customer customer);
}

public class OrderPricingService : IOrderPricingService
{
    public Money CalculateTotalPrice(Order order, Customer customer)
    {
        decimal subtotal = order.OrderLines.Sum(ol => 
            ol.Product.Price.Amount * ol.Quantity);
        
        // Apply customer discount
        decimal discount = customer.IsVip ? 0.10m : 0;
        subtotal = subtotal * (1 - discount);
        
        // Apply tax
        decimal tax = subtotal * 0.08m;
        
        // Add shipping
        decimal shipping = subtotal > 100 ? 0 : 10;
        
        decimal total = subtotal + tax + shipping;
        
        return Money.Create(total, "USD");
    }
}

// Usage
public class Order
{
    public Money CalculateTotal(IOrderPricingService pricingService, Customer customer)
    {
        return pricingService.CalculateTotalPrice(this, customer);
    }
}
```

**Another Example:**
```csharp
public interface ITransferService
{
    Task TransferAsync(Account fromAccount, Account toAccount, Money amount);
}

public class TransferService : ITransferService
{
    public async Task TransferAsync(Account fromAccount, Account toAccount, Money amount)
    {
        // Domain logic involving multiple aggregates
        if (fromAccount.Currency != toAccount.Currency)
            throw new DomainException("Currency mismatch");
        
        fromAccount.Withdraw(amount);
        toAccount.Deposit(amount);
        
        // Both changes saved together via Unit of Work
    }
}
```

---

## Bounded Context

**Q: What is a Bounded Context?**

A: Explicit boundary within which domain model applies. Different contexts can have different models for same concept. Reduces complexity. Enables team autonomy.

```csharp
// Sales Context
namespace Sales
{
    public class Customer
    {
        public int CustomerId { get; set; }
        public string Name { get; set; }
        public decimal CreditLimit { get; set; }
        public List<Order> Orders { get; set; }
    }
}

// Shipping Context - Different Customer model
namespace Shipping
{
    public class Customer
    {
        public int CustomerId { get; set; }
        public string Name { get; set; }
        public Address ShippingAddress { get; set; }
        // No CreditLimit - not relevant in shipping context
    }
}

// Support Context - Different Customer model
namespace Support
{
    public class Customer
    {
        public int CustomerId { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public List<Ticket> Tickets { get; set; }
        // Different concerns - support history
    }
}
```

**Context Mapping:**
- Shared Kernel: Shared code between contexts
- Customer/Supplier: One context depends on another
- Conformist: Downstream conforms to upstream
- Anti-Corruption Layer: Translates between contexts

```csharp
// Anti-Corruption Layer
public class SalesCustomerAdapter
{
    public Sales.Customer ToSalesCustomer(Shipping.Customer shippingCustomer)
    {
        return new Sales.Customer
        {
            CustomerId = shippingCustomer.CustomerId,
            Name = shippingCustomer.Name,
            // Map only relevant fields
        };
    }
}
```

---

## DDD Best Practices

1. **Always use factory methods for creation**
```csharp
public static Order Create(Customer customer) { /* ... */ }
```

2. **Make constructors private**
```csharp
private Order() { }
```

3. **Use private setters**
```csharp
public int OrderId { get; private set; }
```

4. **Validate in domain objects**
```csharp
if (amount <= 0) throw new DomainException("...");
```

5. **Encapsulate collections**
```csharp
private readonly List<OrderLine> _orderLines = new();
public IReadOnlyCollection<OrderLine> OrderLines => _orderLines.AsReadOnly();
```

6. **Use value objects for concepts without identity**
```csharp
public Money Price { get; private set; }
```

7. **Keep aggregates small**
8. **Reference other aggregates by ID**
9. **Use domain events for cross-aggregate communication**
10. **Put business logic in domain layer**

---

## Common Mistakes

❌ **Anemic Domain Model** - All logic in services
```csharp
// BAD
public class Order
{
    public int OrderId { get; set; }
    public decimal Total { get; set; }
}

public class OrderService
{
    public void SubmitOrder(Order order)
    {
        // All logic in service
    }
}
```

✅ **Rich Domain Model** - Logic in entities
```csharp
// GOOD
public class Order
{
    public int OrderId { get; private set; }
    
    public void Submit()
    {
        // Business logic here
    }
}
```

❌ **Direct aggregate modification**
```csharp
order.OrderLines.Add(new OrderLine());  // BAD
```

✅ **Through aggregate root**
```csharp
order.AddOrderLine(product, quantity);  // GOOD
```
