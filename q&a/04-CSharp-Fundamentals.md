---
title: C# Fundamentals
aliases: [C# Fundamentals, CSharp Basics]
tags: [csharp, fundamentals, interview]
order: 4
---

# C# Fundamentals - Interview Q&A

> [!info]+ Related Notes
> [[01-OOP-Principles|OOP Principles]] · [[05-Data-Structures-Algorithms|Data Structures & Algorithms]]

## Value Types vs Reference Types

**Q: What are value types vs reference types?**

A: Value types store data directly (int, struct, enum) on stack. Reference types store reference to data (class, interface, delegate) on heap. Value types copy data on assignment, reference types copy reference.

```csharp
// Value type
int a = 10;
int b = a;  // Copies value
b = 20;     // a is still 10

// Reference type
var list1 = new List<int>();
var list2 = list1;  // Copies reference
list2.Add(1);       // Both list1 and list2 have the item
```

---

## Async/Await

**Q: Explain async/await?**

A: async marks method as asynchronous, await suspends execution until task completes without blocking thread. Returns control to caller, improves scalability. Task<T> represents async operation.

```csharp
public async Task<User> GetUserAsync(int id)
{
    var user = await _repository.GetByIdAsync(id);
    return user;
}

// Calling async method
var user = await GetUserAsync(1);
```

**Key Points:**
- Don't block on async code (.Result, .Wait())
- Use ConfigureAwait(false) in library code
- Always return Task/Task<T>
- Use async all the way up

---

## IEnumerable vs IQueryable

**Q: What is the difference between IEnumerable and IQueryable?**

A: IEnumerable for in-memory collections, executes queries on client. IQueryable for external data sources (DB), builds expression tree, executes queries on server (deferred execution).

```csharp
// IEnumerable - Executes on client side
IEnumerable<User> users = _context.Users.ToList();
var filtered = users.Where(u => u.Age > 18);  // Filters in memory

// IQueryable - Executes on server side
IQueryable<User> users = _context.Users;
var filtered = users.Where(u => u.Age > 18);  // Translates to SQL
var result = filtered.ToList();  // Now executes
```

---

## Delegates and Events

**Q: Explain delegates and events?**

A: Delegate is type-safe function pointer. Event is encapsulated delegate, restricts external invocation. Used for publisher-subscriber pattern.

```csharp
// Delegate
public delegate void NotifyDelegate(string message);

public class Publisher
{
    public NotifyDelegate OnNotify;
    
    public void DoSomething()
    {
        OnNotify?.Invoke("Done!");
    }
}

// Event (better encapsulation)
public class Publisher
{
    public event EventHandler<string> OnNotify;
    
    public void DoSomething()
    {
        OnNotify?.Invoke(this, "Done!");
    }
}

// Usage
var pub = new Publisher();
pub.OnNotify += (sender, msg) => Console.WriteLine(msg);
```

---

## Abstract Class vs Interface

**Q: What is the difference between abstract class and interface?**

A: Abstract class can have implementation, fields, constructors. Interface only contracts (pre-C# 8), supports multiple inheritance. Use interface for contracts, abstract for shared base.

```csharp
// Abstract class
public abstract class Animal
{
    protected string Name;  // Field
    
    protected Animal(string name)  // Constructor
    {
        Name = name;
    }
    
    public abstract void MakeSound();  // Must implement
    
    public void Sleep()  // Shared implementation
    {
        Console.WriteLine($"{Name} is sleeping");
    }
}

// Interface
public interface IFlyable
{
    void Fly();
    int WingSpan { get; set; }
}

// C# 8+ Default interface methods
public interface ILogger
{
    void Log(string message);
    
    void LogError(string message)  // Default implementation
    {
        Log($"ERROR: {message}");
    }
}
```

**When to use:**
- Abstract class: IS-A relationship, shared code
- Interface: CAN-DO relationship, multiple contracts

---

## Extension Methods

**Q: What are extension methods?**

A: Static methods that extend existing types without modifying them. First parameter uses 'this' keyword. Defined in static class.

```csharp
public static class StringExtensions
{
    public static bool IsNullOrEmpty(this string str)
    {
        return string.IsNullOrEmpty(str);
    }
    
    public static string Truncate(this string str, int maxLength)
    {
        if (str.Length <= maxLength) return str;
        return str.Substring(0, maxLength) + "...";
    }
}

// Usage
string text = "Hello World";
if (text.IsNullOrEmpty())  // Looks like instance method
{
    // ...
}
var truncated = text.Truncate(5);  // "Hello..."
```

---

## Generics and Constraints

**Q: Explain generics and constraints?**

A: Generics provide type safety with reusable code. Constraints limit type parameters (where T : class, struct, new(), BaseClass, IInterface).

```csharp
// Generic class
public class Repository<T> where T : class
{
    public void Add(T entity) { }
    public T GetById(int id) { return default(T); }
}

// Multiple constraints
public class Service<T> where T : class, IEntity, new()
{
    public T CreateNew()
    {
        return new T();  // new() constraint allows this
    }
}

// Generic method
public T Clone<T>(T source) where T : ICloneable
{
    return (T)source.Clone();
}

// Constraint types:
// where T : struct         - Value type
// where T : class          - Reference type
// where T : new()          - Public parameterless constructor
// where T : BaseClass      - Inherit from BaseClass
// where T : IInterface     - Implement IInterface
// where T : U              - T derives from U
```

---

## Reflection

**Q: What is reflection?**

A: Runtime inspection of assemblies, types, members. Used for dynamic type loading, attribute reading, late binding. Performance overhead.

```csharp
// Get type information
Type type = typeof(User);
Type type2 = user.GetType();

// Get properties
PropertyInfo[] properties = type.GetProperties();
foreach (var prop in properties)
{
    Console.WriteLine($"{prop.Name}: {prop.PropertyType}");
}

// Get and invoke method
MethodInfo method = type.GetMethod("Save");
method.Invoke(userInstance, new object[] { });

// Create instance
object instance = Activator.CreateInstance(type);

// Get attributes
var attribute = type.GetCustomAttribute<TableAttribute>();

// Get assembly
Assembly assembly = Assembly.LoadFrom("MyLibrary.dll");
Type[] types = assembly.GetTypes();
```

**Use cases:**
- Dependency Injection containers
- Serialization
- ORM mapping
- Plugin systems
- Unit testing frameworks

---

## String vs StringBuilder

**Q: Difference between String and StringBuilder?**

A: String is immutable, creates new object on modification. StringBuilder is mutable, efficient for multiple string operations.

```csharp
// String - Creates 4 string objects (inefficient)
string result = "";
result += "Hello";  // New string
result += " ";      // New string
result += "World";  // New string

// StringBuilder - More efficient
var sb = new StringBuilder();
sb.Append("Hello");
sb.Append(" ");
sb.Append("World");
string result = sb.ToString();

// Performance comparison
// Multiple concatenations
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 1000; i++)
{
    sb.Append(i);  // Fast
}

string str = "";
for (int i = 0; i < 1000; i++)
{
    str += i;  // Very slow - creates 1000 string objects
}
```

**When to use:**
- String: Few operations, immutability desired
- StringBuilder: Many concatenations, loops

---

## Records

**Q: What are records in C#?**

A: Reference types with value-based equality. Immutable by default (record class). Concise syntax for DTOs. Supports with-expressions.

```csharp
// Record declaration
public record Person(string FirstName, string LastName, int Age);

// Equivalent to:
public record Person
{
    public string FirstName { get; init; }
    public string LastName { get; init; }
    public int Age { get; init; }
}

// Usage
var person1 = new Person("John", "Doe", 30);
var person2 = new Person("John", "Doe", 30);

// Value-based equality
Console.WriteLine(person1 == person2);  // True

// With-expression (non-destructive mutation)
var person3 = person1 with { Age = 31 };

// Deconstruction
var (firstName, lastName, age) = person1;

// Record struct (value type)
public record struct Point(int X, int Y);

// Mutable record
public record MutablePerson
{
    public string Name { get; set; }
    public int Age { get; set; }
}
```

**Benefits:**
- Value equality by default
- Concise syntax
- Immutability
- Great for DTOs, value objects

---

## Nullable Reference Types

**Q: What are nullable reference types?**

A: C# 8 feature to help avoid null reference exceptions. Reference types non-nullable by default when enabled.

```csharp
#nullable enable

// Non-nullable reference type
string name = "John";
name = null;  // Warning

// Nullable reference type
string? nullableName = null;  // OK
nullableName = "John";

// Null-forgiving operator
string GetName() => null!;  // Suppresses warning

// Null-conditional operator
int? length = nullableName?.Length;

// Null-coalescing operator
string displayName = nullableName ?? "Guest";

// Pattern matching
if (nullableName is not null)
{
    Console.WriteLine(nullableName.Length);  // No warning
}
```

Enable in .csproj:
```xml
<PropertyGroup>
  <Nullable>enable</Nullable>
</PropertyGroup>
```

---

## Span<T> and Memory<T>

**Q: What are Span<T> and Memory<T>?**

A: High-performance types for working with contiguous memory. Avoid allocations, reduce memory usage. Span<T> is stack-only.

```csharp
// Span<T> - Stack only, cannot be stored in fields
Span<int> numbers = stackalloc int[100];
numbers[0] = 1;

// Working with arrays
int[] array = new int[] { 1, 2, 3, 4, 5 };
Span<int> span = array.AsSpan();
Span<int> slice = span.Slice(1, 3);  // [2, 3, 4]

// String manipulation without allocations
string text = "Hello World";
ReadOnlySpan<char> span = text.AsSpan();
ReadOnlySpan<char> hello = span.Slice(0, 5);

// Memory<T> - Can be stored in fields, async-friendly
Memory<byte> buffer = new byte[1024];
await WriteAsync(buffer);

public async Task WriteAsync(Memory<byte> buffer)
{
    await stream.WriteAsync(buffer);
}
```

**Benefits:**
- Zero allocations
- Better performance
- Safe memory access
