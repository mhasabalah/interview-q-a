---
title: Clean Architecture
aliases: [Clean Architecture]
tags: [architecture, clean-architecture, interview]
order: 8
---

# Clean Architecture - Interview Q&A

> [!info]+ Related Notes
> [[09-Onion-Architecture|Onion Architecture]] · [[07-Domain-Driven-Design|Domain-Driven Design]] · [[02-SOLID-Principles|SOLID Principles]] · [[17-Architecture-Defense|Architecture Defense]]

> [!tip] Going deeper
> **Vertical slice vs Clean/Onion**, whether MediatR earns its place, and whether to wrap EF Core in a repository are argued — with costs, not just definitions — in [[17-Architecture-Defense#Vertical Slice vs Clean/Onion|Architecture Defense]].
>
> Clean Architecture answers *how code inside one deployable is organised* — it says nothing about **how many deployables**. For that second axis, and for how the styles compare and migrate into one another, see [[20-Choosing-An-Architecture|Choosing an Architecture]] and [[19-Modular-Monolith|Modular Monolith]].

## Overview

**Q: What is Clean Architecture?**

A: Architectural pattern that separates concerns into layers with dependency rules. Inner layers don't depend on outer layers. Business logic is independent of frameworks, UI, and databases.

**Key Principles:**
- Independence of frameworks
- Testability
- Independence of UI
- Independence of database
- Independence of external agency

---

## Architecture Layers

**Q: Explain Clean Architecture layers?**

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│    (API, UI, Controllers)               │
├─────────────────────────────────────────┤
│       Infrastructure Layer              │
│  (Data Access, External Services)       │
├─────────────────────────────────────────┤
│       Application Layer                 │
│  (Use Cases, Interfaces, DTOs)          │
├─────────────────────────────────────────┤
│         Domain Layer                    │
│   (Entities, Value Objects,             │
│    Domain Logic, Interfaces)            │
└─────────────────────────────────────────┘
```

### 1. Domain Layer (Core)
- Entities
- Value Objects
- Domain Events
- Domain Services
- Domain Exceptions
- Repository Interfaces
- **No dependencies on other layers**

### 2. Application Layer
- Use Cases / Application Services
- DTOs (Data Transfer Objects)
- Interfaces for Infrastructure
- Validators
- Mappers
- **Depends only on Domain layer**

### 3. Infrastructure Layer
- Data Access (EF Core, Dapper)
- External Service Clients
- File System Access
- Email/SMS Providers
- Caching
- **Implements interfaces from Application layer**

### 4. Presentation Layer
- API Controllers
- UI Views
- SignalR Hubs
- GraphQL Resolvers
- **Depends on Application layer**

---

## Dependency Rule

**Q: What is the dependency rule in Clean Architecture?**

A: Source code dependencies must point inward. Inner circles know nothing about outer circles. Outer circles depend on inner circles through abstractions (interfaces).

```
Presentation → Application → Domain
     ↓              ↓
Infrastructure ────┘
```

**All dependencies flow toward Domain (core)**

---

## Domain Layer Implementation

**Q: How to implement Domain layer?**

```csharp
// Domain/Entities/User.cs
public class User
{
    public int Id { get; private set; }
    public string Name { get; private set; }
    public Email Email { get; private set; }
    public DateTime CreatedAt { get; private set; }
    
    private readonly List<Order> _orders = new();
    public IReadOnlyCollection<Order> Orders => _orders.AsReadOnly();
    
    // Private constructor - enforce creation through factory method
    private User() { }
    
    // Factory method
    public static User Create(string name, Email email)
    {
        var user = new User
        {
            Name = name ?? throw new ArgumentNullException(nameof(name)),
            Email = email ?? throw new ArgumentNullException(nameof(email)),
            CreatedAt = DateTime.UtcNow
        };
        
        // Raise domain event
        user.AddDomainEvent(new UserCreatedEvent(user));
        
        return user;
    }
    
    // Business logic
    public void ChangeName(string newName)
    {
        if (string.IsNullOrWhiteSpace(newName))
            throw new DomainException("Name cannot be empty");
            
        Name = newName;
    }
    
    public void AddOrder(Order order)
    {
        _orders.Add(order);
    }
}

// Domain/ValueObjects/Email.cs
public class Email : ValueObject
{
    public string Value { get; private set; }
    
    private Email() { }
    
    public static Email Create(string email)
    {
        if (string.IsNullOrWhiteSpace(email))
            throw new DomainException("Email cannot be empty");
            
        if (!email.Contains("@"))
            throw new DomainException("Invalid email format");
            
        return new Email { Value = email };
    }
    
    protected override IEnumerable<object> GetEqualityComponents()
    {
        yield return Value;
    }
}

// Domain/ValueObjects/ValueObject.cs (Base)
public abstract class ValueObject
{
    protected abstract IEnumerable<object> GetEqualityComponents();
    
    public override bool Equals(object obj)
    {
        if (obj == null || obj.GetType() != GetType())
            return false;
            
        var valueObject = (ValueObject)obj;
        
        return GetEqualityComponents()
            .SequenceEqual(valueObject.GetEqualityComponents());
    }
    
    public override int GetHashCode()
    {
        return GetEqualityComponents()
            .Aggregate(1, (current, obj) =>
            {
                unchecked
                {
                    return current * 23 + (obj?.GetHashCode() ?? 0);
                }
            });
    }
}

// Domain/Interfaces/IUserRepository.cs
public interface IUserRepository
{
    Task<User> GetByIdAsync(int id);
    Task<User> GetByEmailAsync(string email);
    Task<IEnumerable<User>> GetAllAsync();
    Task AddAsync(User user);
    Task UpdateAsync(User user);
    Task DeleteAsync(int id);
}

// Domain/Events/UserCreatedEvent.cs
public class UserCreatedEvent : DomainEvent
{
    public User User { get; }
    
    public UserCreatedEvent(User user)
    {
        User = user;
    }
}

// Domain/Exceptions/DomainException.cs
public class DomainException : Exception
{
    public DomainException(string message) : base(message)
    {
    }
}
```

---

## Application Layer Implementation

**Q: How to implement Application layer?**

```csharp
// Application/DTOs/UserDto.cs
public class UserDto
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
}

// Application/UseCases/Users/CreateUser/CreateUserCommand.cs
public class CreateUserCommand : IRequest<int>
{
    public string Name { get; set; }
    public string Email { get; set; }
}

// Application/UseCases/Users/CreateUser/CreateUserCommandHandler.cs
public class CreateUserCommandHandler : IRequestHandler<CreateUserCommand, int>
{
    private readonly IUserRepository _userRepository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IEmailService _emailService;
    private readonly ILogger<CreateUserCommandHandler> _logger;
    
    public CreateUserCommandHandler(
        IUserRepository userRepository,
        IUnitOfWork unitOfWork,
        IEmailService emailService,
        ILogger<CreateUserCommandHandler> logger)
    {
        _userRepository = userRepository;
        _unitOfWork = unitOfWork;
        _emailService = emailService;
        _logger = logger;
    }
    
    public async Task<int> Handle(CreateUserCommand request, CancellationToken cancellationToken)
    {
        // Validate
        var existingUser = await _userRepository.GetByEmailAsync(request.Email);
        if (existingUser != null)
            throw new ApplicationException("User with this email already exists");
        
        // Create domain object
        var email = Email.Create(request.Email);
        var user = User.Create(request.Name, email);
        
        // Save
        await _userRepository.AddAsync(user);
        await _unitOfWork.SaveChangesAsync(cancellationToken);
        
        // Send email (could be handled by domain event)
        await _emailService.SendWelcomeEmailAsync(user.Email.Value);
        
        _logger.LogInformation($"User {user.Id} created successfully");
        
        return user.Id;
    }
}

// Application/UseCases/Users/GetUser/GetUserQuery.cs
public class GetUserQuery : IRequest<UserDto>
{
    public int Id { get; set; }
}

// Application/UseCases/Users/GetUser/GetUserQueryHandler.cs
public class GetUserQueryHandler : IRequestHandler<GetUserQuery, UserDto>
{
    private readonly IUserRepository _userRepository;
    private readonly IMapper _mapper;
    
    public GetUserQueryHandler(IUserRepository userRepository, IMapper mapper)
    {
        _userRepository = userRepository;
        _mapper = mapper;
    }
    
    public async Task<UserDto> Handle(GetUserQuery request, CancellationToken cancellationToken)
    {
        var user = await _userRepository.GetByIdAsync(request.Id);
        
        if (user == null)
            throw new NotFoundException("User not found");
        
        return _mapper.Map<UserDto>(user);
    }
}

// Application/Interfaces/IEmailService.cs
public interface IEmailService
{
    Task SendWelcomeEmailAsync(string email);
    Task SendPasswordResetAsync(string email, string resetToken);
}

// Application/Interfaces/IUnitOfWork.cs
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}

// Application/Validators/CreateUserCommandValidator.cs
public class CreateUserCommandValidator : AbstractValidator<CreateUserCommand>
{
    public CreateUserCommandValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Name is required")
            .MaximumLength(100).WithMessage("Name must not exceed 100 characters");
        
        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email is required")
            .EmailAddress().WithMessage("Invalid email format");
    }
}

// Application/Mappings/MappingProfile.cs
public class MappingProfile : Profile
{
    public MappingProfile()
    {
        CreateMap<User, UserDto>()
            .ForMember(d => d.Email, opt => opt.MapFrom(s => s.Email.Value));
    }
}
```

---

## Infrastructure Layer Implementation

**Q: How to implement Infrastructure layer?**

```csharp
// Infrastructure/Data/AppDbContext.cs
public class AppDbContext : DbContext, IUnitOfWork
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }
    
    public DbSet<User> Users { get; set; }
    public DbSet<Order> Orders { get; set; }
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }
    
    public override async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        // Publish domain events before saving
        var domainEvents = ChangeTracker.Entries<Entity>()
            .Select(x => x.Entity)
            .SelectMany(x => x.DomainEvents)
            .ToList();
        
        var result = await base.SaveChangesAsync(cancellationToken);
        
        // Publish events after successful save
        foreach (var domainEvent in domainEvents)
        {
            // Publish via MediatR or other event bus
        }
        
        return result;
    }
}

// Infrastructure/Data/Configurations/UserConfiguration.cs
public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.ToTable("Users");
        
        builder.HasKey(x => x.Id);
        
        builder.Property(x => x.Name)
            .IsRequired()
            .HasMaxLength(100);
        
        // Value object mapping
        builder.OwnsOne(x => x.Email, email =>
        {
            email.Property(e => e.Value)
                .HasColumnName("Email")
                .IsRequired()
                .HasMaxLength(255);
        });
        
        // Relationships
        builder.HasMany(x => x.Orders)
            .WithOne()
            .HasForeignKey("UserId");
        
        // Ignore domain events
        builder.Ignore(x => x.DomainEvents);
    }
}

// Infrastructure/Repositories/UserRepository.cs
public class UserRepository : IUserRepository
{
    private readonly AppDbContext _context;
    
    public UserRepository(AppDbContext context)
    {
        _context = context;
    }
    
    public async Task<User> GetByIdAsync(int id)
    {
        return await _context.Users
            .Include(u => u.Orders)
            .FirstOrDefaultAsync(u => u.Id == id);
    }
    
    public async Task<User> GetByEmailAsync(string email)
    {
        return await _context.Users
            .FirstOrDefaultAsync(u => u.Email.Value == email);
    }
    
    public async Task<IEnumerable<User>> GetAllAsync()
    {
        return await _context.Users.ToListAsync();
    }
    
    public async Task AddAsync(User user)
    {
        await _context.Users.AddAsync(user);
    }
    
    public Task UpdateAsync(User user)
    {
        _context.Users.Update(user);
        return Task.CompletedTask;
    }
    
    public async Task DeleteAsync(int id)
    {
        var user = await GetByIdAsync(id);
        if (user != null)
        {
            _context.Users.Remove(user);
        }
    }
}

// Infrastructure/Services/EmailService.cs
public class EmailService : IEmailService
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<EmailService> _logger;
    
    public EmailService(IConfiguration configuration, ILogger<EmailService> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }
    
    public async Task SendWelcomeEmailAsync(string email)
    {
        _logger.LogInformation($"Sending welcome email to {email}");
        
        // Actual email sending logic
        using var client = new SmtpClient();
        // Configure and send
        
        await Task.CompletedTask;
    }
    
    public async Task SendPasswordResetAsync(string email, string resetToken)
    {
        _logger.LogInformation($"Sending password reset email to {email}");
        
        // Email sending logic
        
        await Task.CompletedTask;
    }
}
```

---

## Presentation Layer Implementation

**Q: How to implement Presentation layer?**

```csharp
// Presentation/Controllers/UsersController.cs
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IMediator _mediator;
    
    public UsersController(IMediator mediator)
    {
        _mediator = mediator;
    }
    
    [HttpGet]
    public async Task<ActionResult<IEnumerable<UserDto>>> GetAll()
    {
        var users = await _mediator.Send(new GetAllUsersQuery());
        return Ok(users);
    }
    
    [HttpGet("{id}")]
    public async Task<ActionResult<UserDto>> Get(int id)
    {
        try
        {
            var user = await _mediator.Send(new GetUserQuery { Id = id });
            return Ok(user);
        }
        catch (NotFoundException)
        {
            return NotFound();
        }
    }
    
    [HttpPost]
    public async Task<ActionResult<int>> Create([FromBody] CreateUserCommand command)
    {
        var userId = await _mediator.Send(command);
        return CreatedAtAction(nameof(Get), new { id = userId }, userId);
    }
    
    [HttpPut("{id}")]
    public async Task<ActionResult> Update(int id, [FromBody] UpdateUserCommand command)
    {
        if (id != command.Id)
            return BadRequest();
        
        await _mediator.Send(command);
        return NoContent();
    }
    
    [HttpDelete("{id}")]
    public async Task<ActionResult> Delete(int id)
    {
        await _mediator.Send(new DeleteUserCommand { Id = id });
        return NoContent();
    }
}

// Presentation/Program.cs
var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Application services
builder.Services.AddMediatR(cfg => 
    cfg.RegisterServicesFromAssembly(typeof(CreateUserCommand).Assembly));
builder.Services.AddAutoMapper(typeof(MappingProfile).Assembly);
builder.Services.AddValidatorsFromAssembly(typeof(CreateUserCommandValidator).Assembly);

// Infrastructure services
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IUnitOfWork>(provider => provider.GetRequiredService<AppDbContext>());
builder.Services.AddScoped<IEmailService, EmailService>();

var app = builder.Build();

// Configure pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
```

---

## DTOs vs Domain Models

**Q: Why use DTOs?**

A: DTOs decouple domain models from API contracts.

```csharp
// Domain Model - Internal representation
public class User
{
    public int Id { get; private set; }
    public string Name { get; private set; }
    public Email Email { get; private set; }
    public byte[] PasswordHash { get; private set; }
    public DateTime CreatedAt { get; private set; }
    public bool IsDeleted { get; private set; }
    
    // Domain logic, private setters, etc.
}

// DTO - External representation
public class UserDto
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
    // No sensitive data (password, internal flags)
    // Simple structure, easy to serialize
}
```

**Benefits:**
- Security (hide sensitive data)
- Versioning (different API versions)
- Performance (select only needed fields)
- Decoupling (change domain without breaking API)

---

## Benefits of Clean Architecture

1. **Independent of Frameworks** - Business logic doesn't depend on frameworks
2. **Testable** - Business logic can be tested without UI, database
3. **Independent of UI** - Change UI without changing business logic
4. **Independent of Database** - Swap databases easily
5. **Independent of External Services** - Business logic doesn't know about external systems

---

## Common Questions

**Q: Where do I put validation?**
A: 
- Domain validation (business rules) → Domain entities
- Input validation (format, required) → Application layer (FluentValidation)
- Authorization → Application layer or Presentation layer

**Q: Should repositories return DTOs or entities?**
A: Repositories should return domain entities. Mapping to DTOs happens in Application layer.

**Q: Where do I put AutoMapper profiles?**
A: Application layer (maps domain entities to DTOs)

**Q: Can Infrastructure reference Application?**
A: Yes, Infrastructure implements interfaces defined in Application layer.

**Q: Can Application reference Infrastructure?**
A: No! Application defines interfaces, Infrastructure implements them. Dependency injection resolves at runtime.
