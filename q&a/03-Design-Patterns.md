---
title: Design Patterns
aliases: [Design Patterns, GoF Patterns]
tags: [csharp, design-patterns, architecture, interview]
order: 3
---

# Design Patterns - Interview Q&A

> [!info]+ Related Notes
> [[01-OOP-Principles|OOP Principles]] · [[02-SOLID-Principles|SOLID Principles]] · [[08-Clean-Architecture|Clean Architecture]]

## Creational Patterns

### Singleton Pattern

**Q: Explain Singleton pattern?**

A: Ensures only one instance of a class exists throughout application lifetime. Provides global access point to that instance.

```csharp
// Thread-safe Singleton using Lazy<T>
public sealed class Singleton
{
    private static readonly Lazy<Singleton> _instance = 
        new Lazy<Singleton>(() => new Singleton());
    
    private Singleton()
    {
        // Private constructor prevents instantiation
    }
    
    public static Singleton Instance => _instance.Value;
    
    public void DoSomething()
    {
        Console.WriteLine("Singleton method called");
    }
}

// Usage
var singleton1 = Singleton.Instance;
var singleton2 = Singleton.Instance;
// singleton1 == singleton2 (same instance)
```

**Other implementations:**
```csharp
// Double-check locking (older approach)
public sealed class Singleton
{
    private static Singleton _instance;
    private static readonly object _lock = new object();
    
    private Singleton() { }
    
    public static Singleton Instance
    {
        get
        {
            if (_instance == null)
            {
                lock (_lock)
                {
                    if (_instance == null)
                    {
                        _instance = new Singleton();
                    }
                }
            }
            return _instance;
        }
    }
}

// Static initialization (simple but loads immediately)
public sealed class Singleton
{
    private static readonly Singleton _instance = new Singleton();
    
    static Singleton() { }
    private Singleton() { }
    
    public static Singleton Instance => _instance;
}
```

**Use cases:**
- Configuration managers
- Logging
- Database connection pools
- Caching

**Cons:**
- Makes unit testing difficult
- Can hide dependencies
- Violates Single Responsibility Principle

---

### Factory Pattern

**Q: What is Factory pattern?**

A: Creates objects without exposing creation logic. Returns objects through common interface. Encapsulates object creation.

```csharp
// Product interface
public interface INotification
{
    void Send(string message);
}

// Concrete products
public class EmailNotification : INotification
{
    public void Send(string message)
    {
        Console.WriteLine($"Email: {message}");
    }
}

public class SmsNotification : INotification
{
    public void Send(string message)
    {
        Console.WriteLine($"SMS: {message}");
    }
}

public class PushNotification : INotification
{
    public void Send(string message)
    {
        Console.WriteLine($"Push: {message}");
    }
}

// Simple Factory
public class NotificationFactory
{
    public INotification CreateNotification(string type)
    {
        return type.ToLower() switch
        {
            "email" => new EmailNotification(),
            "sms" => new SmsNotification(),
            "push" => new PushNotification(),
            _ => throw new ArgumentException($"Unknown type: {type}")
        };
    }
}

// Usage
var factory = new NotificationFactory();
INotification notification = factory.CreateNotification("email");
notification.Send("Hello!");
```

**Factory Method Pattern:**
```csharp
// Creator
public abstract class NotificationCreator
{
    public abstract INotification CreateNotification();
    
    public void Notify(string message)
    {
        var notification = CreateNotification();
        notification.Send(message);
    }
}

// Concrete creators
public class EmailNotificationCreator : NotificationCreator
{
    public override INotification CreateNotification()
    {
        return new EmailNotification();
    }
}

public class SmsNotificationCreator : NotificationCreator
{
    public override INotification CreateNotification()
    {
        return new SmsNotification();
    }
}

// Usage
NotificationCreator creator = new EmailNotificationCreator();
creator.Notify("Message");
```

---

### Abstract Factory Pattern

**Q: What is Abstract Factory pattern?**

A: Factory of factories. Creates families of related objects without specifying concrete classes.

```csharp
// Abstract products
public interface IButton
{
    void Render();
}

public interface ITextBox
{
    void Render();
}

// Concrete products - Windows
public class WindowsButton : IButton
{
    public void Render() => Console.WriteLine("Rendering Windows button");
}

public class WindowsTextBox : ITextBox
{
    public void Render() => Console.WriteLine("Rendering Windows textbox");
}

// Concrete products - Mac
public class MacButton : IButton
{
    public void Render() => Console.WriteLine("Rendering Mac button");
}

public class MacTextBox : ITextBox
{
    public void Render() => Console.WriteLine("Rendering Mac textbox");
}

// Abstract factory
public interface IUIFactory
{
    IButton CreateButton();
    ITextBox CreateTextBox();
}

// Concrete factories
public class WindowsFactory : IUIFactory
{
    public IButton CreateButton() => new WindowsButton();
    public ITextBox CreateTextBox() => new WindowsTextBox();
}

public class MacFactory : IUIFactory
{
    public IButton CreateButton() => new MacButton();
    public ITextBox CreateTextBox() => new MacTextBox();
}

// Usage
IUIFactory factory = new WindowsFactory();
IButton button = factory.CreateButton();
ITextBox textBox = factory.CreateTextBox();
button.Render();
textBox.Render();
```

---

### Builder Pattern

**Q: What is Builder pattern?**

A: Constructs complex objects step by step. Separates construction from representation. Same construction process can create different representations.

```csharp
// Product
public class Pizza
{
    public string Dough { get; set; }
    public string Sauce { get; set; }
    public List<string> Toppings { get; set; } = new();
    
    public override string ToString()
    {
        return $"Pizza with {Dough} dough, {Sauce} sauce, " +
               $"and toppings: {string.Join(", ", Toppings)}";
    }
}

// Builder interface
public interface IPizzaBuilder
{
    IPizzaBuilder SetDough(string dough);
    IPizzaBuilder SetSauce(string sauce);
    IPizzaBuilder AddTopping(string topping);
    Pizza Build();
}

// Concrete builder
public class PizzaBuilder : IPizzaBuilder
{
    private Pizza _pizza = new();
    
    public IPizzaBuilder SetDough(string dough)
    {
        _pizza.Dough = dough;
        return this;
    }
    
    public IPizzaBuilder SetSauce(string sauce)
    {
        _pizza.Sauce = sauce;
        return this;
    }
    
    public IPizzaBuilder AddTopping(string topping)
    {
        _pizza.Toppings.Add(topping);
        return this;
    }
    
    public Pizza Build()
    {
        var result = _pizza;
        _pizza = new Pizza();  // Reset for next build
        return result;
    }
}

// Usage - Fluent API
var pizza = new PizzaBuilder()
    .SetDough("thin crust")
    .SetSauce("tomato")
    .AddTopping("mozzarella")
    .AddTopping("pepperoni")
    .AddTopping("mushrooms")
    .Build();

Console.WriteLine(pizza);
```

**With Director:**
```csharp
public class PizzaDirector
{
    private readonly IPizzaBuilder _builder;
    
    public PizzaDirector(IPizzaBuilder builder)
    {
        _builder = builder;
    }
    
    public Pizza MakeMargherita()
    {
        return _builder
            .SetDough("thin crust")
            .SetSauce("tomato")
            .AddTopping("mozzarella")
            .AddTopping("basil")
            .Build();
    }
    
    public Pizza MakePepperoni()
    {
        return _builder
            .SetDough("regular")
            .SetSauce("tomato")
            .AddTopping("mozzarella")
            .AddTopping("pepperoni")
            .Build();
    }
}

// Usage
var director = new PizzaDirector(new PizzaBuilder());
var margherita = director.MakeMargherita();
var pepperoni = director.MakePepperoni();
```

---

## Structural Patterns

### Repository Pattern

**Q: Explain Repository pattern?**

A: Mediates between domain and data mapping layers. Abstracts data access. Provides collection-like interface for accessing domain objects.

```csharp
// Entity
public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
}

// Repository interface
public interface IRepository<T> where T : class
{
    T GetById(int id);
    IEnumerable<T> GetAll();
    IEnumerable<T> Find(Expression<Func<T, bool>> predicate);
    void Add(T entity);
    void Update(T entity);
    void Delete(int id);
}

// Generic repository implementation
public class Repository<T> : IRepository<T> where T : class
{
    protected readonly DbContext _context;
    protected readonly DbSet<T> _dbSet;
    
    public Repository(DbContext context)
    {
        _context = context;
        _dbSet = context.Set<T>();
    }
    
    public T GetById(int id)
    {
        return _dbSet.Find(id);
    }
    
    public IEnumerable<T> GetAll()
    {
        return _dbSet.ToList();
    }
    
    public IEnumerable<T> Find(Expression<Func<T, bool>> predicate)
    {
        return _dbSet.Where(predicate).ToList();
    }
    
    public void Add(T entity)
    {
        _dbSet.Add(entity);
    }
    
    public void Update(T entity)
    {
        _dbSet.Update(entity);
    }
    
    public void Delete(int id)
    {
        var entity = _dbSet.Find(id);
        if (entity != null)
        {
            _dbSet.Remove(entity);
        }
    }
}

// Specific repository with custom methods
public interface IUserRepository : IRepository<User>
{
    User GetByEmail(string email);
    IEnumerable<User> GetActiveUsers();
}

public class UserRepository : Repository<User>, IUserRepository
{
    public UserRepository(DbContext context) : base(context)
    {
    }
    
    public User GetByEmail(string email)
    {
        return _dbSet.FirstOrDefault(u => u.Email == email);
    }
    
    public IEnumerable<User> GetActiveUsers()
    {
        return _dbSet.Where(u => u.IsActive).ToList();
    }
}

// Usage
public class UserService
{
    private readonly IUserRepository _userRepository;
    
    public UserService(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }
    
    public User GetUser(int id)
    {
        return _userRepository.GetById(id);
    }
    
    public void CreateUser(User user)
    {
        _userRepository.Add(user);
    }
}
```

---

### Unit of Work Pattern

**Q: What is Unit of Work pattern?**

A: Maintains list of objects affected by business transaction. Coordinates writing changes. Ensures all changes are committed or rolled back together.

```csharp
public interface IUnitOfWork : IDisposable
{
    IUserRepository Users { get; }
    IOrderRepository Orders { get; }
    IProductRepository Products { get; }
    
    int SaveChanges();
    Task<int> SaveChangesAsync();
}

public class UnitOfWork : IUnitOfWork
{
    private readonly AppDbContext _context;
    
    public UnitOfWork(AppDbContext context)
    {
        _context = context;
        Users = new UserRepository(_context);
        Orders = new OrderRepository(_context);
        Products = new ProductRepository(_context);
    }
    
    public IUserRepository Users { get; private set; }
    public IOrderRepository Orders { get; private set; }
    public IProductRepository Products { get; private set; }
    
    public int SaveChanges()
    {
        return _context.SaveChanges();
    }
    
    public async Task<int> SaveChangesAsync()
    {
        return await _context.SaveChangesAsync();
    }
    
    public void Dispose()
    {
        _context.Dispose();
    }
}

// Usage
public class OrderService
{
    private readonly IUnitOfWork _unitOfWork;
    
    public OrderService(IUnitOfWork unitOfWork)
    {
        _unitOfWork = unitOfWork;
    }
    
    public void CreateOrder(Order order)
    {
        // Multiple operations in one transaction
        var user = _unitOfWork.Users.GetById(order.UserId);
        var product = _unitOfWork.Products.GetById(order.ProductId);
        
        product.Stock -= order.Quantity;
        _unitOfWork.Products.Update(product);
        
        _unitOfWork.Orders.Add(order);
        
        // Single SaveChanges - transaction
        _unitOfWork.SaveChanges();
    }
}
```

---

### Adapter Pattern

**Q: What is Adapter pattern?**

A: Converts interface of class into another interface clients expect. Allows incompatible interfaces to work together.

```csharp
// Target interface (what client expects)
public interface IPaymentProcessor
{
    void ProcessPayment(decimal amount);
}

// Adaptee (existing class with incompatible interface)
public class ThirdPartyPaymentGateway
{
    public void MakePayment(double amountInDollars, string currency)
    {
        Console.WriteLine($"Processing {amountInDollars} {currency}");
    }
}

// Adapter
public class PaymentAdapter : IPaymentProcessor
{
    private readonly ThirdPartyPaymentGateway _gateway;
    
    public PaymentAdapter(ThirdPartyPaymentGateway gateway)
    {
        _gateway = gateway;
    }
    
    public void ProcessPayment(decimal amount)
    {
        // Convert and adapt
        double dollars = (double)amount;
        _gateway.MakePayment(dollars, "USD");
    }
}

// Usage
IPaymentProcessor processor = new PaymentAdapter(new ThirdPartyPaymentGateway());
processor.ProcessPayment(100.50m);
```

---

### Decorator Pattern

**Q: What is Decorator pattern?**

A: Adds behavior to objects dynamically. Wraps original object. Alternative to subclassing.

```csharp
// Component interface
public interface INotifier
{
    void Send(string message);
}

// Concrete component
public class EmailNotifier : INotifier
{
    public void Send(string message)
    {
        Console.WriteLine($"Email: {message}");
    }
}

// Base decorator
public abstract class NotifierDecorator : INotifier
{
    protected readonly INotifier _notifier;
    
    protected NotifierDecorator(INotifier notifier)
    {
        _notifier = notifier;
    }
    
    public virtual void Send(string message)
    {
        _notifier.Send(message);
    }
}

// Concrete decorators
public class SmsDecorator : NotifierDecorator
{
    public SmsDecorator(INotifier notifier) : base(notifier)
    {
    }
    
    public override void Send(string message)
    {
        base.Send(message);
        Console.WriteLine($"SMS: {message}");
    }
}

public class SlackDecorator : NotifierDecorator
{
    public SlackDecorator(INotifier notifier) : base(notifier)
    {
    }
    
    public override void Send(string message)
    {
        base.Send(message);
        Console.WriteLine($"Slack: {message}");
    }
}

// Usage - wrap decorators
INotifier notifier = new EmailNotifier();
notifier = new SmsDecorator(notifier);
notifier = new SlackDecorator(notifier);
notifier.Send("Important message");
// Sends via Email, SMS, and Slack
```

---

## Behavioral Patterns

### Strategy Pattern

**Q: What is Strategy pattern?**

A: Defines family of algorithms, encapsulates each, makes them interchangeable. Strategy varies independently from clients.

```csharp
// Strategy interface
public interface ISortStrategy
{
    void Sort(List<int> list);
}

// Concrete strategies
public class QuickSort : ISortStrategy
{
    public void Sort(List<int> list)
    {
        Console.WriteLine("Sorting using QuickSort");
        list.Sort();  // Simplified
    }
}

public class MergeSort : ISortStrategy
{
    public void Sort(List<int> list)
    {
        Console.WriteLine("Sorting using MergeSort");
        list.Sort();  // Simplified
    }
}

public class BubbleSort : ISortStrategy
{
    public void Sort(List<int> list)
    {
        Console.WriteLine("Sorting using BubbleSort");
        list.Sort();  // Simplified
    }
}

// Context
public class Sorter
{
    private ISortStrategy _strategy;
    
    public void SetStrategy(ISortStrategy strategy)
    {
        _strategy = strategy;
    }
    
    public void Sort(List<int> list)
    {
        _strategy.Sort(list);
    }
}

// Usage
var sorter = new Sorter();
var numbers = new List<int> { 5, 2, 8, 1, 9 };

sorter.SetStrategy(new QuickSort());
sorter.Sort(numbers);

sorter.SetStrategy(new MergeSort());
sorter.Sort(numbers);
```

---

### Observer Pattern

**Q: What is Observer pattern?**

A: Defines one-to-many dependency. When one object changes state, dependents are notified automatically.

```csharp
// Subject interface
public interface ISubject
{
    void Attach(IObserver observer);
    void Detach(IObserver observer);
    void Notify();
}

// Observer interface
public interface IObserver
{
    void Update(ISubject subject);
}

// Concrete subject
public class Stock : ISubject
{
    private List<IObserver> _observers = new();
    private string _symbol;
    private decimal _price;
    
    public string Symbol
    {
        get => _symbol;
        set
        {
            _symbol = value;
            Notify();
        }
    }
    
    public decimal Price
    {
        get => _price;
        set
        {
            _price = value;
            Notify();
        }
    }
    
    public void Attach(IObserver observer)
    {
        _observers.Add(observer);
    }
    
    public void Detach(IObserver observer)
    {
        _observers.Remove(observer);
    }
    
    public void Notify()
    {
        foreach (var observer in _observers)
        {
            observer.Update(this);
        }
    }
}

// Concrete observers
public class StockDisplay : IObserver
{
    private string _name;
    
    public StockDisplay(string name)
    {
        _name = name;
    }
    
    public void Update(ISubject subject)
    {
        if (subject is Stock stock)
        {
            Console.WriteLine($"{_name}: {stock.Symbol} is now ${stock.Price}");
        }
    }
}

// Usage
var stock = new Stock { Symbol = "AAPL", Price = 150 };

var display1 = new StockDisplay("Display 1");
var display2 = new StockDisplay("Display 2");

stock.Attach(display1);
stock.Attach(display2);

stock.Price = 155;  // Both displays notified
stock.Price = 160;  // Both displays notified
```

**Using C# events:**
```csharp
public class Stock
{
    public event EventHandler<decimal> PriceChanged;
    
    private decimal _price;
    
    public decimal Price
    {
        get => _price;
        set
        {
            _price = value;
            OnPriceChanged(value);
        }
    }
    
    protected virtual void OnPriceChanged(decimal newPrice)
    {
        PriceChanged?.Invoke(this, newPrice);
    }
}

// Usage
var stock = new Stock();
stock.PriceChanged += (sender, price) => Console.WriteLine($"Price: ${price}");
stock.Price = 150;
```

---

### Command Pattern

**Q: What is Command pattern?**

A: Encapsulates request as object. Parameterizes clients with different requests. Supports undo/redo operations.

```csharp
// Command interface
public interface ICommand
{
    void Execute();
    void Undo();
}

// Receiver
public class Light
{
    public void TurnOn()
    {
        Console.WriteLine("Light is ON");
    }
    
    public void TurnOff()
    {
        Console.WriteLine("Light is OFF");
    }
}

// Concrete commands
public class TurnOnCommand : ICommand
{
    private readonly Light _light;
    
    public TurnOnCommand(Light light)
    {
        _light = light;
    }
    
    public void Execute()
    {
        _light.TurnOn();
    }
    
    public void Undo()
    {
        _light.TurnOff();
    }
}

public class TurnOffCommand : ICommand
{
    private readonly Light _light;
    
    public TurnOffCommand(Light light)
    {
        _light = light;
    }
    
    public void Execute()
    {
        _light.TurnOff();
    }
    
    public void Undo()
    {
        _light.TurnOn();
    }
}

// Invoker
public class RemoteControl
{
    private Stack<ICommand> _commandHistory = new();
    
    public void ExecuteCommand(ICommand command)
    {
        command.Execute();
        _commandHistory.Push(command);
    }
    
    public void UndoLastCommand()
    {
        if (_commandHistory.Count > 0)
        {
            var command = _commandHistory.Pop();
            command.Undo();
        }
    }
}

// Usage
var light = new Light();
var remote = new RemoteControl();

remote.ExecuteCommand(new TurnOnCommand(light));   // Light ON
remote.ExecuteCommand(new TurnOffCommand(light));  // Light OFF
remote.UndoLastCommand();                          // Light ON
```

---

### Mediator Pattern (MediatR)

**Q: Explain Mediator pattern and MediatR?**

A: Reduces coupling between components. Components communicate through mediator. Used with CQRS pattern.

```csharp
// Install: MediatR and MediatR.Extensions.Microsoft.DependencyInjection

// Command
public class CreateUserCommand : IRequest<int>
{
    public string Name { get; set; }
    public string Email { get; set; }
}

// Command handler
public class CreateUserCommandHandler : IRequestHandler<CreateUserCommand, int>
{
    private readonly IUserRepository _repository;
    private readonly ILogger<CreateUserCommandHandler> _logger;
    
    public CreateUserCommandHandler(
        IUserRepository repository,
        ILogger<CreateUserCommandHandler> logger)
    {
        _repository = repository;
        _logger = logger;
    }
    
    public async Task<int> Handle(CreateUserCommand request, CancellationToken cancellationToken)
    {
        _logger.LogInformation($"Creating user: {request.Name}");
        
        var user = new User
        {
            Name = request.Name,
            Email = request.Email
        };
        
        _repository.Add(user);
        await _repository.SaveAsync(cancellationToken);
        
        return user.Id;
    }
}

// Query
public class GetUserQuery : IRequest<UserDto>
{
    public int Id { get; set; }
}

// Query handler
public class GetUserQueryHandler : IRequestHandler<GetUserQuery, UserDto>
{
    private readonly IUserRepository _repository;
    
    public GetUserQueryHandler(IUserRepository repository)
    {
        _repository = repository;
    }
    
    public async Task<UserDto> Handle(GetUserQuery request, CancellationToken cancellationToken)
    {
        var user = await _repository.GetByIdAsync(request.Id);
        
        return new UserDto
        {
            Id = user.Id,
            Name = user.Name,
            Email = user.Email
        };
    }
}

// Startup configuration
services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(Program).Assembly));

// Usage in controller
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IMediator _mediator;
    
    public UsersController(IMediator mediator)
    {
        _mediator = mediator;
    }
    
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateUserCommand command)
    {
        var userId = await _mediator.Send(command);
        return Ok(userId);
    }
    
    [HttpGet("{id}")]
    public async Task<IActionResult> Get(int id)
    {
        var user = await _mediator.Send(new GetUserQuery { Id = id });
        return Ok(user);
    }
}
```

**Benefits:**
- Decoupled handlers
- Single responsibility per handler
- Easy to test
- Cross-cutting concerns via behaviors
