---
title: SOLID Principles
aliases: [SOLID, SOLID Principles]
tags: [csharp, oop, solid, architecture, interview]
order: 2
---

# SOLID Principles - Interview Q&A

> [!info]+ Related Notes
> [[01-OOP-Principles|OOP Principles]] · [[03-Design-Patterns|Design Patterns]] · [[08-Clean-Architecture|Clean Architecture]]

## Overview

**Q: What are SOLID principles?**

A: Five design principles for object-oriented programming that make software designs more understandable, flexible, and maintainable.

- **S**ingle Responsibility Principle
- **O**pen/Closed Principle
- **L**iskov Substitution Principle
- **I**nterface Segregation Principle
- **D**ependency Inversion Principle

---

## Single Responsibility Principle (SRP)

**Q: What is Single Responsibility Principle?**

A: A class should have only one reason to change. Each class should have only one responsibility or job.

### ❌ Bad Example:
```csharp
public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
    
    // Multiple responsibilities in one class
    public void SaveToDatabase()
    {
        // Database logic
        using var connection = new SqlConnection("...");
        // Save user
    }
    
    public void SendEmail(string message)
    {
        // Email logic
        var smtp = new SmtpClient();
        // Send email
    }
    
    public string GenerateReport()
    {
        // Reporting logic
        return $"User Report for {Name}";
    }
    
    public bool ValidateEmail()
    {
        // Validation logic
        return Email.Contains("@");
    }
}
```

### ✅ Good Example:
```csharp
// Entity - Only data and domain logic
public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
}

// Repository - Database operations
public interface IUserRepository
{
    void Save(User user);
    User GetById(int id);
}

public class UserRepository : IUserRepository
{
    private readonly DbContext _context;
    
    public UserRepository(DbContext context)
    {
        _context = context;
    }
    
    public void Save(User user)
    {
        _context.Users.Add(user);
        _context.SaveChanges();
    }
    
    public User GetById(int id)
    {
        return _context.Users.Find(id);
    }
}

// Email Service - Email operations
public interface IEmailService
{
    void SendEmail(string to, string message);
}

public class EmailService : IEmailService
{
    public void SendEmail(string to, string message)
    {
        var smtp = new SmtpClient();
        // Send email logic
    }
}

// Validator - Validation logic
public interface IUserValidator
{
    bool ValidateEmail(string email);
    bool ValidateUser(User user);
}

public class UserValidator : IUserValidator
{
    public bool ValidateEmail(string email)
    {
        return !string.IsNullOrEmpty(email) && email.Contains("@");
    }
    
    public bool ValidateUser(User user)
    {
        return ValidateEmail(user.Email) && !string.IsNullOrEmpty(user.Name);
    }
}

// Report Generator - Reporting logic
public interface IUserReportGenerator
{
    string GenerateReport(User user);
}

public class UserReportGenerator : IUserReportGenerator
{
    public string GenerateReport(User user)
    {
        return $"User Report\nName: {user.Name}\nEmail: {user.Email}";
    }
}

// Service - Orchestrates operations
public class UserService
{
    private readonly IUserRepository _repository;
    private readonly IEmailService _emailService;
    private readonly IUserValidator _validator;
    
    public UserService(
        IUserRepository repository, 
        IEmailService emailService,
        IUserValidator validator)
    {
        _repository = repository;
        _emailService = emailService;
        _validator = validator;
    }
    
    public void CreateUser(User user)
    {
        if (!_validator.ValidateUser(user))
            throw new ValidationException("Invalid user");
            
        _repository.Save(user);
        _emailService.SendEmail(user.Email, "Welcome!");
    }
}
```

**Benefits:**
- Easy to understand
- Easy to test
- Less coupling
- Better organization

---

## Open/Closed Principle (OCP)

**Q: What is Open/Closed Principle?**

A: Software entities should be open for extension but closed for modification. You should be able to add new functionality without changing existing code.

### ❌ Bad Example:
```csharp
public class PaymentProcessor
{
    public void ProcessPayment(string paymentType, decimal amount)
    {
        if (paymentType == "CreditCard")
        {
            // Process credit card
            Console.WriteLine($"Processing ${amount} via Credit Card");
        }
        else if (paymentType == "PayPal")
        {
            // Process PayPal
            Console.WriteLine($"Processing ${amount} via PayPal");
        }
        else if (paymentType == "Bitcoin")
        {
            // Process Bitcoin - MODIFIED existing code
            Console.WriteLine($"Processing ${amount} via Bitcoin");
        }
        // Adding new payment method requires modifying this class
    }
}
```

### ✅ Good Example:
```csharp
// Abstract base
public abstract class PaymentProcessor
{
    public abstract void ProcessPayment(decimal amount);
    
    public void LogPayment(decimal amount)
    {
        Console.WriteLine($"Payment of ${amount} logged");
    }
}

// Concrete implementations - EXTEND without MODIFYING
public class CreditCardProcessor : PaymentProcessor
{
    public override void ProcessPayment(decimal amount)
    {
        Console.WriteLine($"Processing ${amount} via Credit Card");
        // Credit card specific logic
    }
}

public class PayPalProcessor : PaymentProcessor
{
    public override void ProcessPayment(decimal amount)
    {
        Console.WriteLine($"Processing ${amount} via PayPal");
        // PayPal specific logic
    }
}

// NEW payment method - NO modification to existing code
public class BitcoinProcessor : PaymentProcessor
{
    public override void ProcessPayment(decimal amount)
    {
        Console.WriteLine($"Processing ${amount} via Bitcoin");
        // Bitcoin specific logic
    }
}

// Usage
public class CheckoutService
{
    private readonly PaymentProcessor _processor;
    
    public CheckoutService(PaymentProcessor processor)
    {
        _processor = processor;
    }
    
    public void Checkout(decimal amount)
    {
        _processor.ProcessPayment(amount);
        _processor.LogPayment(amount);
    }
}
```

**Using Strategy Pattern:**
```csharp
public interface IPaymentStrategy
{
    void Pay(decimal amount);
}

public class CreditCardPayment : IPaymentStrategy
{
    public void Pay(decimal amount)
    {
        Console.WriteLine($"Paid ${amount} with Credit Card");
    }
}

public class PayPalPayment : IPaymentStrategy
{
    public void Pay(decimal amount)
    {
        Console.WriteLine($"Paid ${amount} with PayPal");
    }
}

public class ShoppingCart
{
    private readonly IPaymentStrategy _paymentStrategy;
    
    public ShoppingCart(IPaymentStrategy paymentStrategy)
    {
        _paymentStrategy = paymentStrategy;
    }
    
    public void Pay(decimal amount)
    {
        _paymentStrategy.Pay(amount);
    }
}

// Usage - easily extend with new payment methods
var cart = new ShoppingCart(new CreditCardPayment());
cart.Pay(100);
```

---

## Liskov Substitution Principle (LSP)

**Q: What is Liskov Substitution Principle?**

A: Derived classes must be substitutable for their base classes. Subtype must honor the contract of base type. If S is subtype of T, objects of type T can be replaced with objects of type S without breaking the application.

### ❌ Bad Example:
```csharp
public class Rectangle
{
    public virtual int Width { get; set; }
    public virtual int Height { get; set; }
    
    public int CalculateArea()
    {
        return Width * Height;
    }
}

public class Square : Rectangle
{
    // Violates LSP - Square changes behavior
    public override int Width
    {
        get => base.Width;
        set
        {
            base.Width = value;
            base.Height = value;  // Forces height to equal width
        }
    }
    
    public override int Height
    {
        get => base.Height;
        set
        {
            base.Width = value;   // Forces width to equal height
            base.Height = value;
        }
    }
}

// This breaks LSP
void TestRectangle(Rectangle rect)
{
    rect.Width = 5;
    rect.Height = 4;
    
    // Expected: 20, but with Square: 16
    Console.WriteLine(rect.CalculateArea());  // Unexpected behavior!
}

Rectangle rect = new Rectangle();
TestRectangle(rect);  // Works: 20

Rectangle square = new Square();
TestRectangle(square);  // Breaks: 16 (expected 20)
```

### ✅ Good Example:
```csharp
// Use composition instead
public abstract class Shape
{
    public abstract int CalculateArea();
}

public class Rectangle : Shape
{
    public int Width { get; set; }
    public int Height { get; set; }
    
    public override int CalculateArea()
    {
        return Width * Height;
    }
}

public class Square : Shape
{
    public int Side { get; set; }
    
    public override int CalculateArea()
    {
        return Side * Side;
    }
}

// Both can be used interchangeably as Shape
void PrintArea(Shape shape)
{
    Console.WriteLine($"Area: {shape.CalculateArea()}");
}

Shape rect = new Rectangle { Width = 5, Height = 4 };
Shape square = new Square { Side = 5 };

PrintArea(rect);    // 20
PrintArea(square);  // 25
```

**Another Example:**
```csharp
// ❌ Bad: ReadOnlyCollection inheriting from Collection
public class Collection
{
    private List<string> _items = new();
    
    public virtual void Add(string item) => _items.Add(item);
    public virtual void Remove(string item) => _items.Remove(item);
}

public class ReadOnlyCollection : Collection
{
    // Violates LSP - throws exceptions
    public override void Add(string item)
    {
        throw new NotSupportedException("Cannot add to read-only collection");
    }
    
    public override void Remove(string item)
    {
        throw new NotSupportedException("Cannot remove from read-only collection");
    }
}

// ✅ Good: Separate interfaces
public interface IReadableCollection
{
    IEnumerable<string> GetAll();
}

public interface IWritableCollection : IReadableCollection
{
    void Add(string item);
    void Remove(string item);
}

public class Collection : IWritableCollection
{
    private List<string> _items = new();
    
    public IEnumerable<string> GetAll() => _items;
    public void Add(string item) => _items.Add(item);
    public void Remove(string item) => _items.Remove(item);
}

public class ReadOnlyCollection : IReadableCollection
{
    private readonly List<string> _items;
    
    public ReadOnlyCollection(List<string> items)
    {
        _items = items;
    }
    
    public IEnumerable<string> GetAll() => _items;
}
```

**Rules for LSP:**
- Don't throw unexpected exceptions
- Don't strengthen preconditions
- Don't weaken postconditions
- Honor base class invariants

---

## Interface Segregation Principle (ISP)

**Q: What is Interface Segregation Principle?**

A: Clients should not be forced to depend on interfaces they don't use. Many specific interfaces are better than one general-purpose interface.

### ❌ Bad Example:
```csharp
// Fat interface - forces implementation of unused methods
public interface IWorker
{
    void Work();
    void Eat();
    void Sleep();
    void GetPaid();
}

public class HumanWorker : IWorker
{
    public void Work() => Console.WriteLine("Working");
    public void Eat() => Console.WriteLine("Eating");
    public void Sleep() => Console.WriteLine("Sleeping");
    public void GetPaid() => Console.WriteLine("Getting paid");
}

public class RobotWorker : IWorker
{
    public void Work() => Console.WriteLine("Working");
    
    // Forced to implement irrelevant methods
    public void Eat() => throw new NotImplementedException();
    public void Sleep() => throw new NotImplementedException();
    public void GetPaid() => throw new NotImplementedException();
}
```

### ✅ Good Example:
```csharp
// Segregated interfaces
public interface IWorkable
{
    void Work();
}

public interface IFeedable
{
    void Eat();
}

public interface ISleepable
{
    void Sleep();
}

public interface IPayable
{
    void GetPaid();
}

// Implement only needed interfaces
public class HumanWorker : IWorkable, IFeedable, ISleepable, IPayable
{
    public void Work() => Console.WriteLine("Working");
    public void Eat() => Console.WriteLine("Eating");
    public void Sleep() => Console.WriteLine("Sleeping");
    public void GetPaid() => Console.WriteLine("Getting paid");
}

public class RobotWorker : IWorkable
{
    public void Work() => Console.WriteLine("Working");
    // No need to implement irrelevant methods
}

public class Manager : IWorkable, IPayable
{
    public void Work() => Console.WriteLine("Managing");
    public void GetPaid() => Console.WriteLine("Getting paid");
}

// Usage - depend only on what you need
public class WorkManager
{
    public void ManageWork(IWorkable worker)
    {
        worker.Work();  // Only needs IWorkable
    }
}

public class PayrollSystem
{
    public void ProcessPayroll(IPayable employee)
    {
        employee.GetPaid();  // Only needs IPayable
    }
}
```

**Repository Example:**
```csharp
// ❌ Bad: God interface
public interface IRepository<T>
{
    T GetById(int id);
    IEnumerable<T> GetAll();
    void Add(T entity);
    void Update(T entity);
    void Delete(int id);
    IEnumerable<T> Search(string criteria);
    void BulkInsert(IEnumerable<T> entities);
    Task<T> GetByIdAsync(int id);
    // ... many more methods
}

// ✅ Good: Segregated interfaces
public interface IReadRepository<T>
{
    T GetById(int id);
    IEnumerable<T> GetAll();
}

public interface IWriteRepository<T>
{
    void Add(T entity);
    void Update(T entity);
    void Delete(int id);
}

public interface ISearchRepository<T>
{
    IEnumerable<T> Search(string criteria);
}

// Implement what you need
public class UserRepository : IReadRepository<User>, IWriteRepository<User>
{
    public User GetById(int id) { /* ... */ }
    public IEnumerable<User> GetAll() { /* ... */ }
    public void Add(User entity) { /* ... */ }
    public void Update(User entity) { /* ... */ }
    public void Delete(int id) { /* ... */ }
}

// Read-only repository
public class ReadOnlyProductRepository : IReadRepository<Product>
{
    public Product GetById(int id) { /* ... */ }
    public IEnumerable<Product> GetAll() { /* ... */ }
}
```

---

## Dependency Inversion Principle (DIP)

**Q: What is Dependency Inversion Principle?**

A: 
1. High-level modules should not depend on low-level modules. Both should depend on abstractions.
2. Abstractions should not depend on details. Details should depend on abstractions.

### ❌ Bad Example:
```csharp
// Low-level module
public class EmailService
{
    public void SendEmail(string to, string message)
    {
        Console.WriteLine($"Sending email to {to}: {message}");
    }
}

// High-level module depends on concrete implementation
public class UserService
{
    private readonly EmailService _emailService;  // Tight coupling
    
    public UserService()
    {
        _emailService = new EmailService();  // Creates dependency
    }
    
    public void RegisterUser(string email)
    {
        // Register logic
        _emailService.SendEmail(email, "Welcome!");
    }
}

// Cannot easily switch to SMS or push notification
```

### ✅ Good Example:
```csharp
// Abstraction
public interface INotificationService
{
    void SendNotification(string to, string message);
}

// Low-level modules - implement abstraction
public class EmailService : INotificationService
{
    public void SendNotification(string to, string message)
    {
        Console.WriteLine($"Sending email to {to}: {message}");
    }
}

public class SmsService : INotificationService
{
    public void SendNotification(string to, string message)
    {
        Console.WriteLine($"Sending SMS to {to}: {message}");
    }
}

public class PushNotificationService : INotificationService
{
    public void SendNotification(string to, string message)
    {
        Console.WriteLine($"Sending push notification to {to}: {message}");
    }
}

// High-level module - depends on abstraction
public class UserService
{
    private readonly INotificationService _notificationService;
    
    // Dependency injected
    public UserService(INotificationService notificationService)
    {
        _notificationService = notificationService;
    }
    
    public void RegisterUser(string contact)
    {
        // Register logic
        _notificationService.SendNotification(contact, "Welcome!");
    }
}

// Dependency Injection Container configuration
services.AddScoped<INotificationService, EmailService>();
// Easy to switch:
// services.AddScoped<INotificationService, SmsService>();

// Usage
var userService = new UserService(new EmailService());
userService.RegisterUser("user@example.com");

// Easy to switch notification method
var userServiceWithSms = new UserService(new SmsService());
userServiceWithSms.RegisterUser("+1234567890");
```

**Repository Pattern Example:**
```csharp
// Abstraction
public interface IUserRepository
{
    User GetById(int id);
    void Save(User user);
}

// Low-level - SQL implementation
public class SqlUserRepository : IUserRepository
{
    private readonly SqlConnection _connection;
    
    public SqlUserRepository(SqlConnection connection)
    {
        _connection = connection;
    }
    
    public User GetById(int id)
    {
        // SQL logic
        return new User();
    }
    
    public void Save(User user)
    {
        // SQL logic
    }
}

// Low-level - NoSQL implementation
public class MongoUserRepository : IUserRepository
{
    private readonly IMongoDatabase _database;
    
    public MongoUserRepository(IMongoDatabase database)
    {
        _database = database;
    }
    
    public User GetById(int id)
    {
        // MongoDB logic
        return new User();
    }
    
    public void Save(User user)
    {
        // MongoDB logic
    }
}

// High-level - depends on abstraction
public class UserBusinessLogic
{
    private readonly IUserRepository _repository;
    
    public UserBusinessLogic(IUserRepository repository)
    {
        _repository = repository;
    }
    
    public void ProcessUser(int userId)
    {
        var user = _repository.GetById(userId);
        // Business logic
        _repository.Save(user);
    }
}

// Configuration - easily switch implementations
// services.AddScoped<IUserRepository, SqlUserRepository>();
services.AddScoped<IUserRepository, MongoUserRepository>();
```

**Benefits of DIP:**
- Loose coupling
- Easy to test (mock dependencies)
- Easy to change implementations
- Better maintainability
- Enables dependency injection

---

## SOLID Summary

| Principle | Description | Key Benefit |
|-----------|-------------|-------------|
| **SRP** | One class, one responsibility | Easy to understand and maintain |
| **OCP** | Open for extension, closed for modification | Add features without breaking code |
| **LSP** | Subtypes must be substitutable | Reliable inheritance hierarchies |
| **ISP** | Many specific interfaces > one general | No unused dependencies |
| **DIP** | Depend on abstractions, not concretions | Flexible, testable, decoupled |

**All together:**
```csharp
// SRP - Single responsibility
public class User { /* Only user data */ }

// OCP - Can extend with new validators without modifying
public interface IValidator<T> { bool Validate(T entity); }

// LSP - All validators can be substituted
public class EmailValidator : IValidator<string> { /* ... */ }

// ISP - Specific interfaces
public interface IReadRepository<T> { T GetById(int id); }
public interface IWriteRepository<T> { void Save(T entity); }

// DIP - Depend on abstractions
public class UserService
{
    private readonly IReadRepository<User> _readRepo;
    private readonly IWriteRepository<User> _writeRepo;
    private readonly IValidator<User> _validator;
    
    public UserService(
        IReadRepository<User> readRepo,
        IWriteRepository<User> writeRepo,
        IValidator<User> validator)
    {
        _readRepo = readRepo;
        _writeRepo = writeRepo;
        _validator = validator;
    }
}
```
