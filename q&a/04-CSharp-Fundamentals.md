---
title: C# Fundamentals
aliases: [C# Fundamentals, CSharp Basics]
tags: [csharp, fundamentals, interview]
order: 4
---

# C# Fundamentals - Interview Q&A

> [!info]+ Related Notes
> [[01-OOP-Principles|OOP Principles]] · [[05-Data-Structures-Algorithms|Data Structures & Algorithms]] · [[17-Architecture-Defense|Architecture Defense]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]]

> [!abstract]+ How this note is organised
> Nobody senior asks "what is async". They ask **what the compiler generated**, **what breaks under load**, and **what you'd measure**. Five parts, in learning order:
>
> | Part | Covers | Priority |
> |---|---|---|
> | 1. [[#Part 1 — Type System & Language Core\|Type System & Language Core]] | value vs reference, class/struct/record, `ref`/`out`/`in`, **equality & `GetHashCode`**, generics & **variance**, delegates, **exceptions vs the Result pattern**, nullability, **modern C#** | foundation — expected, not scoring |
> | 2. [[#Part 2 — Memory & Garbage Collection\|Memory & GC]] | boxing, generations & LOH, `IDisposable`/`IAsyncDisposable`, **DI lifetimes**, `Span<T>` | mid-high |
> | 3. [[#Part 3 — Async & Concurrency\|Async & Concurrency]] | state machine, `Task` vs `ValueTask`, `ConfigureAwait`, cancellation, `SemaphoreSlim`/`Interlocked`/`Channel<T>`, starvation | **highest — start here** |
> | 4. [[#Part 4 — Collections, Iterators & LINQ\|Collections, Iterators & LINQ]] | `IQueryable`, **`yield`**, **`IAsyncEnumerable`**, deferred execution, closure capture | **high** |
> | 5. [[#Part 5 — Rapid-Fire Drill\|Rapid-Fire Drill]] | 37 one-line answers to say out loud, grouped by part | final-day review |
>
> Within each part, sections run **basic → senior**: the plain Q&A first, then the follow-up that actually separates candidates.

---

# Part 1 — Type System & Language Core

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

## class vs struct vs record

**Q: How do you choose between class, struct, and record?**

| | `class` | `struct` | `record` (class) | `record struct` |
|---|---|---|---|---|
| Allocation | heap | inline (stack / inside owner) | heap | inline |
| Semantics | reference | **copied on every assignment/pass** | reference | copied |
| Equality | reference | member-wise (slow, reflection-based unless overridden) | **value-based, generated** | value-based, generated |
| Mutability | your choice | your choice (prefer `readonly struct`) | `init` by default | mutable unless `readonly record struct` |
| `with` expression | no | no | **yes** | yes |
| Can be `null` | yes | no (unless `T?`) | yes | no |

**The decision rule to state:**
- **`class`** — default for anything with identity or behaviour: entities, services, aggregates.
- **`record`** — data with **no identity**: DTOs, MediatR commands/queries, events, value objects. You get equality, `ToString()`, deconstruction, and immutability for free.
- **`struct`** — only when *all* hold: small (≈≤16 bytes), immutable, short-lived, allocated in huge numbers. Otherwise the copying costs more than the allocation you saved.

```csharp
public readonly record struct Money(decimal Amount, string Currency);  // ideal value object
public record CreateOrderCommand(Guid CustomerId, List<Guid> ItemIds) : IRequest<Guid>;

// Struct copy trap
public struct Counter { public int Value; public void Inc() => Value++; }
var list = new List<Counter> { new() };
list[0].Inc();          // does nothing useful — list[0] returns a COPY
                        // (with a plain array it would work: arr[0].Inc())

// Defensive copies: a non-readonly struct in a readonly field is copied on EVERY member call
private readonly Counter _c;   // _c.Inc() silently mutates a temporary
// -> mark structs `readonly struct` so the compiler can prove no copy is needed
```

> [!warning] Records are not automatically immutable
> `record` gives `init`-only *properties*, but a `List<T>` inside one is still mutable, and `with` performs a **shallow** copy. `record` ≠ deep immutability.

---

## ref, out and in parameters

**Q: What's the difference between `ref`, `out`, and `in`?**

A: All three pass by **reference** instead of by value. They differ in who must assign, and who may modify.

| | Must be initialised by caller | Must be assigned by method | Method may modify | Use for |
|---|---|---|---|---|
| `ref` | **yes** | no | yes | in-and-out modification |
| `out` | no | **yes, before returning** | yes | returning a second value |
| `in` | **yes** | no | **no (readonly)** | passing a **large struct** without copying |

```csharp
void Swap(ref int a, ref int b) { (a, b) = (b, a); }
int x = 1, y = 2; Swap(ref x, ref y);            // caller must initialise

bool TryParse(string s, out int value)            // the classic Try-pattern
{ value = 0; ... return true; }
if (int.TryParse(s, out var n)) { ... }           // inline declaration

void Process(in BigStruct data)                   // pass by reference, guarantee no mutation
{ /* data.Field = 1;  <- compile error */ }
```

**The senior points:**
- **Passing a reference type by value is not the same as `ref`.** Without `ref` you copy the *pointer*: mutating the object is visible to the caller, but **reassigning the parameter is not**.

```csharp
void A(List<int> list) { list.Add(1); }        // caller SEES the added item
void B(List<int> list) { list = new(); }       // caller sees NOTHING — only the local copy changed
void C(ref List<int> list) { list = new(); }   // caller's variable now points to the new list
```

- **`in` exists for performance, and it can backfire.** Passing a large `struct` by `in` avoids a copy — but if the struct is **not** `readonly`, the compiler inserts a *defensive copy* on every member access, making it slower than passing by value. `in` + `readonly struct` is the combination that actually pays.
- `ref` also exists on returns and locals (`ref return`, `ref var`) for high-performance array/span access — know it exists; you won't be asked to write it.
- **`out` in async is illegal** (`async` methods can't have `ref`/`out` parameters) — return a tuple or a small result record instead.

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

## Equality — ==, Equals and GetHashCode

**Q: What's the difference between `==` and `.Equals()`?**

A: `==` is a **static operator resolved at compile time** by the *declared* type. `.Equals()` is a **virtual method resolved at run time** by the *actual* type. That single sentence answers most follow-ups.

```csharp
object a = "hello";
object b = "hel" + GetLo();          // built at runtime, so not interned
Console.WriteLine(a == b);           // False! -> object's == is reference comparison
Console.WriteLine(a.Equals(b));      // True  -> virtual call lands on string.Equals

string s1 = "hello", s2 = "hel" + GetLo();
Console.WriteLine(s1 == s2);         // True  -> string OVERLOADS == to compare values

// Reference identity regardless of any overload:
Console.WriteLine(ReferenceEquals(a, b));   // False
```

**Defaults by type:** `class` → reference equality · `struct` → member-wise (via `ValueType.Equals`, which uses **reflection** unless you override it — slow) · `record` → value equality, generated · `string` → value equality (overloaded `==`).

**Q: If you override `Equals`, why must you override `GetHashCode`?**

A: Because hash-based collections (`Dictionary`, `HashSet`, `GroupBy`, `Distinct`) find a bucket by hash **first** and only then compare with `Equals`. Two objects that are `Equals` but hash differently land in different buckets and are never compared — so the lookup silently fails.

```csharp
public class Point
{
    public int X { get; init; }
    public int Y { get; init; }
    public override bool Equals(object? o) => o is Point p && p.X == X && p.Y == Y;
    // WITHOUT this override, the dictionary lookup below returns FALSE:
    public override int GetHashCode() => HashCode.Combine(X, Y);   // use HashCode.Combine, never hand-rolled
}

var set = new HashSet<Point> { new() { X = 1, Y = 2 } };
set.Contains(new Point { X = 1, Y = 2 });   // true only if GetHashCode is overridden too
```

**The `GetHashCode` contract — state all three:**
1. Equal objects **must** return the same hash code. (Unequal objects *may* collide — that's legal and normal.)
2. The hash must **not change while the object is in a hash-based collection**. Hashing on a mutable property, then mutating it, makes the entry **unfindable** — a genuine production bug and a great thing to mention.
3. It must not throw.

> [!warning] The trap they set for you
> "Records give me value equality, so I can use them as dictionary keys." Yes — **unless** the record holds a collection. `record Order(Guid Id, List<string> Tags)` compares `Tags` by **reference**, because the generated equality calls `EqualityComparer<List<string>>.Default`. Two records with identical tag lists are *not* equal. Use immutable/value-typed members, or override equality yourself.

**Also worth naming:** `IEquatable<T>` (a typed `Equals` that avoids boxing for structs — implement it on every struct you compare) · `IComparable<T>`/`IComparer<T>` for *ordering* (sorting), which is a different contract from equality · `StringComparison` — `string.Equals(a, b, StringComparison.OrdinalIgnoreCase)` is the correct case-insensitive comparison; `a.ToLower() == b.ToLower()` allocates twice and is culture-dependent (the "Turkish I" problem).

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

**Q: Why do generics exist at all — what did they replace?**

A: Type safety **and** performance. Before generics, `ArrayList` stored `object`, so every value type was **boxed** and every read needed a cast that could fail at run time. Generics are reified at run time in .NET (unlike Java's erasure): `List<int>` gets its own specialised JIT-compiled code with no boxing.

### Covariance and contravariance

**Q: Why can't I assign `List<string>` to `List<object>`?**

A: Because it would break type safety — you could then `Add(42)` to something that is really a list of strings. Variance is only allowed where it's provably safe, and that's what `out` and `in` on generic *interfaces* declare:

```csharp
// COVARIANCE (out) — T only ever comes OUT, so a more-derived T is safe
IEnumerable<string> strings = new List<string>();
IEnumerable<object> objects = strings;        // legal: IEnumerable<out T>
// You can only READ from it, so nothing can be smuggled in.

// CONTRAVARIANCE (in) — T only ever goes IN, so a less-derived T is safe
Action<object> printAny = o => Console.WriteLine(o);
Action<string> printText = printAny;          // legal: Action<in T>
// Anything that can handle any object can certainly handle a string.

List<string> list = new();
List<object> bad = list;                      // ILLEGAL: List<T> is invariant (T goes both ways)
```

**Remember it as:** `out` = **produces** (covariant, `IEnumerable<out T>`, `Func<out TResult>`) · `in` = **consumes** (contravariant, `Action<in T>`, `IComparer<in T>`). **Arrays are covariant and it was a mistake** — `object[] a = new string[1]; a[0] = 42;` compiles and throws `ArrayTypeMismatchException` at run time. That example is the cleanest way to show you understand *why* the rule exists.

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

## Exceptions

**Q: What's the difference between `throw;` and `throw ex;`?** *(asked constantly — get it instantly right)*

A: **`throw;` rethrows and preserves the original stack trace. `throw ex;` resets it to the current line**, destroying the evidence of where the failure actually happened.

```csharp
try { DoWork(); }
catch (Exception ex)
{
    _log.LogError(ex, "failed");
    throw;                       // ✅ preserves the original stack trace
    // throw ex;                 // ❌ stack trace now starts HERE — you lost the real location
    // throw new AppException("failed", ex);   // ✅ also fine: wraps, keeps the InnerException
}
```

**Q: What are exception filters and why are they better than catch-and-rethrow?**

```csharp
try { await _http.SendAsync(req, ct); }
catch (HttpRequestException ex) when (ex.StatusCode == HttpStatusCode.NotFound) { return null; }
catch (HttpRequestException ex) when (IsTransient(ex)) { await RetryAsync(); }
```

The `when` clause is evaluated **before the stack unwinds**. That means: the stack trace and local state are intact if no filter matches (better dumps and debugging), and you never enter a catch block only to rethrow. A filter that returns `false` leaves the exception completely untouched.

**The senior points to make:**
- **Exceptions are for exceptional cases, not control flow.** Throwing is expensive (stack capture, unwinding); a validation failure on a hot path should be a result object or the `Try*` pattern, not an exception. But **don't** contort the design to avoid them — "expensive" is microseconds, and correctness first.
- **Catch only what you can handle.** `catch (Exception) { }` — swallowing — is the worst line of code in any codebase. If you can't handle it, let it reach the global handler.
- **One global handler**, not try/catch in every method: exception-handling middleware (or `IExceptionHandler` in .NET 8+) maps exception types to status codes and a **ProblemDetails** response, and logs once with the correlation ID. See [[10-Middlewares|Middlewares]].
- **Custom exceptions carry meaning**: `DomainException`/`NotFoundException`/`ConflictException` map cleanly to 409/404/422 — one place, no `if` ladder.
- **`finally` always runs** — except on `StackOverflowException`, `Environment.FailFast`, or process kill. `using` is `try/finally`.
- **`OperationCanceledException` is not a failure** — filter it out of your error logging or you'll drown in noise. See [[#CancellationToken propagation|cancellation]].
- **Never catch `async` exceptions by accident**: an exception in `async void` cannot be caught by the caller and takes the process down.
- **`AggregateException`** comes from `Task.WhenAll`/`.Wait()`/`.Result`; `await` unwraps it to the *first* inner exception, which is why the others go unnoticed.

---

## The Result pattern

**Q: What is the Result pattern?**

A: A return type that makes **failure part of the method's signature** instead of an invisible side channel. Instead of "returns `Order`, and *maybe* throws something the caller has to guess", the method returns `Result<Order>` — success with a value, or failure with an error — and the caller cannot get to the value without dealing with the failure.

You already use a primitive version of it every day: `int.TryParse` is a Result with the ergonomics of 2003.

```csharp
public sealed record Error(string Code, string Description)
{
    public static readonly Error None = new(string.Empty, string.Empty);
}

public class Result
{
    protected Result(bool isSuccess, Error error)
    {
        if (isSuccess != (error == Error.None))          // a success with an error is a bug
            throw new InvalidOperationException("Invalid result state");
        IsSuccess = isSuccess;
        Error = error;
    }

    public bool IsSuccess { get; }
    public bool IsFailure => !IsSuccess;
    public Error Error { get; }

    public static Result Success() => new(true, Error.None);
    public static Result Failure(Error error) => new(false, error);
    public static Result<T> Success<T>(T value) => new(value, true, Error.None);
    public static Result<T> Failure<T>(Error error) => new(default, false, error);
}

public class Result<T> : Result
{
    private readonly T? _value;
    protected internal Result(T? value, bool isSuccess, Error error) : base(isSuccess, error)
        => _value = value;

    public T Value => IsSuccess ? _value!
        : throw new InvalidOperationException("Cannot read Value of a failed result");

    public static implicit operator Result<T>(T value) => Success(value);   // return the value directly
}
```

**Errors as a catalogue, not magic strings** — this is what makes it maintainable:

```csharp
public static class OrderErrors
{
    public static Error NotFound(Guid id) => new("Order.NotFound", $"Order {id} was not found");
    public static readonly Error AlreadyShipped = new("Order.AlreadyShipped", "A shipped order cannot be cancelled");
    public static readonly Error EmptyCart      = new("Order.EmptyCart", "Cannot place an order with no lines");
}
```

**In a handler, and at the boundary:**

```csharp
public async Task<Result<Guid>> Handle(CancelOrderCommand cmd, CancellationToken ct)
{
    var order = await _repo.GetAsync(cmd.OrderId, ct);
    if (order is null)                          return Result.Failure<Guid>(OrderErrors.NotFound(cmd.OrderId));
    if (order.Status == OrderStatus.Shipped)    return Result.Failure<Guid>(OrderErrors.AlreadyShipped);

    order.Cancel(cmd.Reason);
    await _uow.SaveChangesAsync(ct);
    return order.Id;                            // implicit conversion to Result<Guid>
}

// One mapping point turns errors into HTTP — no try/catch in controllers
[HttpPost("{id}/cancel")]
public async Task<IActionResult> Cancel(Guid id, CancellationToken ct)
{
    var result = await _sender.Send(new CancelOrderCommand(id), ct);

    return result.IsSuccess ? Ok(result.Value) : result.Error.Code switch
    {
        var c when c.EndsWith(".NotFound")   => NotFound(ToProblem(result.Error)),
        var c when c.EndsWith(".Conflict") ||
                   c == "Order.AlreadyShipped" => Conflict(ToProblem(result.Error)),
        _                                     => BadRequest(ToProblem(result.Error))
    };
}
```

### Result vs exceptions — the actual difference

**Q: You have exception middleware already. Why add Result?**

| | **Exception** | **Result** |
|---|---|---|
| **Control flow** | **non-local jump** — the stack unwinds until someone catches; every line between the `throw` and the `catch` is skipped, including code you forgot was there | **normal, local branching** — an `if` at the call site; execution never leaves the method unexpectedly |
| Visible in the signature | **No** — invisible control flow; the caller must read the implementation (or the docs) to know what can fail | **Yes** — the failure is in the return type |
| Who decides it's handled | whoever happens to `catch` it, possibly 4 frames away | the immediate caller, at the call site |
| Propagation | **automatic** — it unwinds through every layer for free | **manual** — every layer must check and pass it on |
| Cost when it happens | stack capture + unwinding (microseconds; irrelevant once, real in a loop of thousands) | an object, or nothing |
| Stack trace | free and detailed | **none** — you get the error you chose to record, and nothing about where |
| Can be ignored | can be swallowed by `catch { }` | can be ignored by not checking `IsSuccess` — **neither is compiler-enforced in C#** |
| Reads well for | "this should never happen" | "this happens every day and the caller must decide" |
| Testing | `Assert.Throws<T>` | assert on a returned value — simpler and faster |

> [!tip] Why the control-flow row is the one that matters
> Everything else on this list follows from it. Because an exception is a **non-local jump**, the compiler can't tell you it might happen, the caller can't be forced to handle it, and the handling ends up far from the cause. Because a `Result` is **just a value**, failure travels through the same `if`/`return` machinery as everything else — visible, local, and testable without a framework.
>
> The flip side, and you must concede it: that non-local jump is also exceptions' **best feature**. It propagates through twenty frames for free. `Result` makes you carry it by hand at every single layer, and one missing `if` swallows the failure silently.

### When to use each

**Reach for `Result` when:**
- The failure is an **expected outcome** the caller must branch on — it's part of the contract, not a malfunction.
- The caller can **do something meaningful** with it: return 404, show a message, offer another seat.
- It happens **routinely** — hundreds of times a day, and nobody should be paged for it.
- It **crosses the application boundary** (handler → API), where the error becomes an HTTP status code.
- Failures are **frequent *and* on a hot path** — bulk parsing, imports, retry loops. This is the only case where the performance argument is real.

**Throw an exception when:**
- A **precondition or invariant is broken** — the *code* is wrong, not the request.
- It's **infrastructure**: DB unreachable, network failure, missing config, deserialization blowing up.
- **No caller up the stack could sensibly handle it** — it should reach the global handler, be logged with a stack trace, and become a 500.
- You're **inside a domain object protecting itself**. An aggregate must never depend on the caller having checked a `Result` — see [[17-Architecture-Defense#DDD tactical patterns\|invariants]].
- The failure is **genuinely rare and unpredicted** — the case you didn't design for.

**Use neither when:** it's the **shape of the request** (missing field, bad email, negative quantity). That's FluentValidation at the boundary, rejected with a 400 before your handler ever runs.

**The decision rule to state in one sentence:**

> **"Is this failure part of the business contract, or is it a bug/environment failure?"** Expected outcomes the caller must handle — *not found*, *already cancelled*, *insufficient balance*, *seat taken* — are **Results**. Broken assumptions and infrastructure — *DB unreachable*, *null where it can't be null*, *config missing*, *invariant violated* — are **exceptions**.

Put concretely:

| Situation | Choice | Why |
|---|---|---|
| Order not found | `Result` | routine; the API returns 404 and life goes on |
| Cancelling a shipped order | `Result` | a valid request with a business answer of "no" — 409 |
| Insufficient balance | `Result` | the whole point of the operation is to check |
| `SaveChanges` times out | **exception** | infrastructure; nobody up the stack can "handle" it meaningfully |
| Aggregate constructed in an invalid state | **exception** | an object that must never exist — see [[17-Architecture-Defense#DDD tactical patterns\|invariants]] |
| Request body fails validation | **neither** | FluentValidation at the boundary → 400 before the handler ever runs |

> [!warning] The performance argument is the weakest one
> Candidates say "exceptions are slow". Throwing costs single-digit microseconds — invisible on a request that touches a database. It only matters when failures are **frequent and hot**: parsing a million rows, validating a bulk import, a retry loop. **Argue explicitness and control flow, not speed** — that's the argument a senior makes, and it survives the follow-up.

### What it costs (say this before they do)

- **Ceremony.** Every layer checks and re-wraps. Without helpers you get a staircase of `if (result.IsFailure) return Result.Failure<T>(result.Error);`.
- **No stack trace.** When a failure turns out to *be* a bug, you have a code string and no idea where it came from. Log context deliberately at the point of failure.
- **It doesn't compose for free.** You need `Map`/`Bind`/`Match`/`Ensure` helpers (this is where "railway-oriented programming" comes from), and combining them with `async` gets noisy fast:

```csharp
return await GetOrder(id)                        // Result<Order>
    .Ensure(o => o.CanBeCancelled, OrderErrors.AlreadyShipped)
    .Tap(o => o.Cancel(reason))
    .Bind(o => Save(o, ct))
    .Match(onSuccess: Ok, onFailure: ToProblem);
```

- **A dependency or a hand-rolled type.** Every team writes their own `Result`, or takes **ErrorOr**, **FluentResults**, **CSharpFunctionalExtensions**, or **LanguageExt** (increasingly functional in that order). C# still has no discriminated unions, so none of this is compiler-enforced — an ignored `Result` compiles silently.
- **A naming collision to expect:** ASP.NET Core has its own `IResult`/`Results`/`TypedResults`. Alias or namespace carefully.
- **The MediatR wrinkle** (a genuine senior detail): a `ValidationBehavior` that wants to *return* a failure instead of throwing must construct a `Result<T>` it only knows as `TResponse` — that needs a `where TResponse : Result` constraint plus reflection or a factory. Many teams keep throwing inside the pipeline and use Result only inside handlers. Knowing why is a good thing to mention.

**Q: If you adopt Result, do you still need the global exception handler?**
A: **Yes, and more than before.** Result handles the failures you *predicted*; the middleware exists for the ones you didn't. Removing it because "we return Results now" means the first unpredicted `NullReferenceException` returns a raw 500 with a stack trace.

**The verdict to give:** "Hybrid, and deliberately. **Result** for expected outcomes crossing the application boundary — my handlers return `Result<T>` and one mapper turns errors into status codes, so failure paths are explicit and testable without `Assert.Throws`. **Exceptions** for invariant violations inside the domain and for infrastructure, because an aggregate that can't protect itself is a bug and I want the stack trace. What I *don't* do is use exceptions for `if (notFound) throw` — that's business logic hiding in a side channel."

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

**The follow-ups:**
- **Why is `string` immutable?** Thread safety without locks, safe use as a dictionary key (a stable hash), and **interning** — the runtime keeps one copy of each *literal* in an intern pool, so identical literals share a reference. Runtime-built strings are not interned unless you call `string.Intern`.
- **When is `+` fine?** For a **fixed** number of concatenations — the compiler turns `a + b + c` into a single `string.Concat` call, which is one allocation. `StringBuilder` only wins in **loops**, where `+=` allocates every iteration. Reaching for `StringBuilder` to join three strings is cargo cult.
- **Better still, don't concatenate:** `string.Join`, `string.Create`, interpolated string handlers (C# 10+ makes `$"..."` allocation-aware in logging), and `ReadOnlySpan<char>` slicing instead of `Substring`.
- **Never build SQL by concatenation** — parameterise. See [[06-Database|Database]].

---

## Modern C# features worth naming

**Q: Which recent C# features do you actually use?** *(a "do you keep current" question — name features **with the problem each solves**, never a version list)*

```csharp
// Pattern matching + switch expressions (C# 8/9) — replaces if/else and switch ladders
var fee = shipment switch
{
    { Weight: > 100, Express: true }        => 50m,      // property pattern
    { Country: "EG" or "SA" }               => 10m,      // logical pattern
    null                                     => throw new ArgumentNullException(),
    _                                        => 20m      // required: exhaustive
};

if (result is { Status: OrderStatus.Paid, Total: > 0 } paid)  // pattern + capture
    Process(paid);

// Records + init + required (C# 9/11) — immutable data with enforced construction
public record Order { public required Guid Id { get; init; } }

// Primary constructors (C# 12) — the DI boilerplate killer
public class OrderService(IOrderRepository repo, ILogger<OrderService> log)
{
    public Task<Order?> GetAsync(Guid id, CancellationToken ct) => repo.GetAsync(id, ct);
}   // no fields, no constructor, no assignment

// Collection expressions (C# 12)
int[] a = [1, 2, 3];
List<int> b = [..a, 4, 5];              // spread

// Nullable reference types (C# 8) — see the next section
// File-scoped namespaces, global usings, top-level statements — less ceremony per file
// Raw string literals (C# 11) — JSON/SQL in tests without escaping
var json = """{ "id": 1, "name": "test" }""";
```

**The honest framing:** "Primary constructors and file-scoped namespaces removed real boilerplate for us. Pattern matching made state-transition code readable. I don't adopt a feature because it's new — `required` earned its place because it moved a runtime null check to compile time."

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

**The follow-up: "isn't reflection slow?"**

A: Yes — member *lookup* is the expensive part, and `Invoke` costs orders of magnitude more than a direct call. Three answers, escalating:
1. **Cache the `MemberInfo`/`PropertyInfo`** — resolve once into a static dictionary, not per call. This alone removes most of the cost.
2. **Compile it** — turn the reflection into a delegate (`Expression.Lambda<Func<T, object>>(...).Compile()` or `CreateDelegate`); after the one-time compile it's near-native speed. This is what mature ORMs and mappers do.
3. **Source generators (the modern answer)** — do the work at *compile* time and emit real code: `System.Text.Json` source generation, regex generators, logging generators. Zero runtime reflection, and it's what makes **AOT/trimming** viable, since a trimmer can't see reflection-only types and will strip them.

Mentioning source generators and trimming/AOT is the current-decade answer; "reflection is slow so avoid it" is the 2010 one.

---

---

# Part 2 — Memory & Garbage Collection

## Boxing

**Q: What is boxing and why do you care?**

A: Wrapping a value type in a heap object so it can be treated as `object` or a non-generic interface. Every box is an **allocation plus a copy**, and unboxing is a type check plus a copy. It's invisible in the source — that's what makes it dangerous.

```csharp
int x = 42;
object o = x;          // BOX: allocates, copies
int y = (int)o;        // UNBOX: checks type, copies back

// Where it hides:
ArrayList list = new(); list.Add(42);              // non-generic collection -> box per item
IComparable c = 42;                                // value type -> interface = box
string s = string.Format("{0}", 42);               // params object[] -> box
Console.WriteLine("id: " + id);                    // struct in concat -> box (interpolation in modern C# often avoids it)
if (myEnum.Equals(other))                          // Enum.Equals(object) -> two boxes
Dictionary<MyStruct, int> d;                       // no IEquatable<T> -> boxes on every lookup

// How to avoid:
List<int> generic = new();                         // generics were invented for this
public readonly struct Point : IEquatable<Point>   // implement IEquatable<T> on structs
{ public bool Equals(Point other) => ...; public override int GetHashCode() => ...; }
if (myEnum == other)                               // == on enums does not box
```

**Say this:** "Boxing matters at *rate*, not in isolation. One box is nothing; a box per row in a 100k-row loop is a gen-0 storm. I'd confirm it with a profiler or BenchmarkDotNet's `[MemoryDiagnoser]` before changing code."

---

## GC generations

**Q: Explain the .NET garbage collector's generations.**

A: A generational, mark-and-compact collector built on the observation that **most objects die young**.

| Heap | What lives there | Collection cost |
|---|---|---|
| **Gen 0** | brand-new objects | very cheap — survivors are copied out, the rest is free |
| **Gen 1** | gen-0 survivors; a buffer between short- and long-lived | cheap |
| **Gen 2** | long-lived: caches, statics, singletons, gen-1 survivors | **expensive** — walks the whole heap |
| **LOH** | objects ≥ **85,000 bytes** (big arrays, buffers) | collected *with gen 2*, **not compacted** by default → fragmentation |
| **POH** | pinned objects (.NET 5+) | keeps pinning out of the normal heaps |

**The points that show seniority:**
- **Allocation is nearly free** (bump a pointer). The cost is *collection*, and specifically **gen-2 / LOH** collections. So the metric that matters is **allocation rate**, not allocation count.
- **Mid-life crisis**: objects that live "medium-long" (a cache with a 2-minute TTL) get promoted to gen 2 and then die there — the worst case. Either keep them truly short-lived or truly long-lived.
- **Server GC vs Workstation GC**: server GC gives one heap + one dedicated GC thread per core — the default for ASP.NET Core, and much higher throughput. In a **container with a low CPU limit** it can be the wrong choice (many heaps, more memory); that's a real tuning conversation.
- `GC.Collect()` in application code is a **red flag** — you're guessing better than a tuned collector.
- **Finalizers make things worse**: a finalizable object survives its first collection (it goes on the finalizer queue) and gets promoted. That's why the dispose pattern calls `GC.SuppressFinalize(this)`.
- Big buffers → `ArrayPool<T>.Shared.Rent/Return` instead of allocating on the LOH.

```bash
dotnet-counters monitor -p <pid> System.Runtime
#   gen-0/1/2-gc-count, gc-heap-size, alloc-rate, time-in-gc  (>10% time-in-gc = investigate)
```

---

## IDisposable and IAsyncDisposable

**Q: What problem does `IDisposable` solve, given there's a GC?**

A: The GC manages **memory**; it does not manage **file handles, sockets, DB connections, locks, or unmanaged buffers**, and it runs at an unpredictable time. `IDisposable` is *deterministic* release of those resources.

```csharp
// using statement / declaration -> try/finally { Dispose(); }
using var conn = new SqlConnection(cs);
await using var stream = File.OpenRead(path);   // IAsyncDisposable: flush/close without blocking

// Full pattern (only when you own unmanaged resources or expect inheritance)
public class Resource : IDisposable
{
    private bool _disposed;
    public void Dispose() { Dispose(true); GC.SuppressFinalize(this); }  // skip the finalizer queue

    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return;
        if (disposing) { _managed?.Dispose(); }   // only safe when called from Dispose()
        ReleaseUnmanagedHandle();                 // always
        _disposed = true;
    }
    ~Resource() => Dispose(false);   // safety net only — a finalizer costs a GC promotion
}
```

**Q: `IAsyncDisposable` — why does it exist?**
A: Because `Dispose()` sometimes needs to do I/O (flush a buffer, send a `QUIT`, commit a transaction). Doing that synchronously is sync-over-async. `await using` calls `DisposeAsync()`. If a type implements both, `await using` prefers the async one. In libraries: `await _inner.DisposeAsync().ConfigureAwait(false);`.

**Q: Who disposes what in ASP.NET Core?**
A: The DI container disposes anything it created that implements `IDisposable`/`IAsyncDisposable`:
- **Scoped** → at the end of the request (this is how `DbContext` is cleaned up — never `using` an injected context).
- **Transient registered in a scope** → also tracked and disposed with the scope. *A transient `IDisposable` resolved from the root container is a memory leak* — it lives until the app shuts down.
- **Singleton** → at shutdown.
- Instances **you** `new` up are yours to dispose.

> [!warning] The classic: `HttpClient`
> `using var client = new HttpClient()` per request → **socket exhaustion**, because disposed sockets sit in `TIME_WAIT` for ~4 minutes. But a single static `HttpClient` never picks up DNS changes. The correct answer is **`IHttpClientFactory`** (`AddHttpClient`), which pools and rotates handlers — and gives you a natural place to hang Polly resilience policies. See [[18-Distributed-Systems-Reliability#Retries done properly|Retries done properly]].

---

## DI lifetimes and captive dependencies

**Q: Explain the three service lifetimes.**

| Lifetime | One instance per | Use for | Disposed |
|---|---|---|---|
| **Transient** | every injection | cheap, stateless helpers | with the scope that created it |
| **Scoped** | HTTP request (or explicit scope) | `DbContext`, unit of work, per-request context | end of request |
| **Singleton** | application | caches, config, `IHttpClientFactory`, background state | app shutdown |

**Q: What is a captive dependency?** *(the question that separates people who have debugged DI from people who have read about it)*

A: A **longer-lived service capturing a shorter-lived one**. Inject a `Scoped` `DbContext` into a `Singleton` and the singleton holds that *one* context forever — so it outlives its request, is shared across threads (and `DbContext` is **not thread-safe**), never releases its change tracker, and leaks memory. The container detects this at startup **only if scope validation is on** (it is by default in Development, and off in Production — a genuinely nasty asymmetry to mention).

```csharp
// ❌ captive dependency
public class CacheWarmer(AppDbContext db) { }        // registered as Singleton
services.AddSingleton<CacheWarmer>();

// ✅ resolve a fresh scope per unit of work
public class CacheWarmer(IServiceScopeFactory scopeFactory)
{
    public async Task RunAsync(CancellationToken ct)
    {
        await using var scope = scopeFactory.CreateAsyncScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        ...
    }   // scope disposal disposes the DbContext
}
```

**The rules to state:** a service may depend on its **own or a longer** lifetime, never a shorter one · **`BackgroundService`/`IHostedService` are singletons** — this is where the bug almost always is · a **transient `IDisposable` resolved from the root provider is a leak** (tracked until shutdown) · `AddSingleton<T>(instance)` means *you* own disposal, the container won't.

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

**Q: When would you actually use it?** (don't pretend you use it daily — this is the honest answer)

A: Parsing and slicing on a hot path, where the alternative is `Substring`/`Split` allocating a string per piece: log/CSV parsing, protocol framing, `Utf8Formatter`/`Utf8Parser`, `string.Create`. `Span<T>` is a `ref struct` — it lives on the stack only, so it **cannot be a field, cannot be captured by a lambda, and cannot cross an `await`**. That last restriction is exactly why `Memory<T>` exists: same idea, heap-storable, async-safe.

```csharp
// Allocation-free parse of "key=value"
ReadOnlySpan<char> line = input.AsSpan();
int eq = line.IndexOf('=');
ReadOnlySpan<char> key = line[..eq];
ReadOnlySpan<char> val = line[(eq + 1)..];
int number = int.Parse(val);              // Parse has span overloads — no Substring allocated
```

---

---

# Part 3 — Async & Concurrency

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

### The async/await state machine (what the compiler really generates)

**Q: What does the compiler do to an `async` method?**

A: It rewrites the method into a **state machine type** implementing `IAsyncStateMachine`. Every local variable becomes a field, every `await` becomes a numbered state, and the method body becomes a `switch` inside `MoveNext()`. A *builder* (`AsyncTaskMethodBuilder`, `AsyncValueTaskMethodBuilder`, or `AsyncVoidMethodBuilder`) owns the `Task` that callers see.

```csharp
// You write:
public async Task<int> GetAsync()
{
    var a = await _http.GetIntAsync();
    return a + 1;
}

// Compiler generates (simplified):
private struct GetAsyncStateMachine : IAsyncStateMachine
{
    public int _state;                       // -1 = running, 0 = at first await
    public AsyncTaskMethodBuilder<int> _builder;
    public HttpService _this;
    private int _a;                          // local hoisted to a field
    private TaskAwaiter<int> _awaiter;       // the awaiter we parked on

    public void MoveNext()
    {
        try
        {
            if (_state != 0)
            {
                _awaiter = _this._http.GetIntAsync().GetAwaiter();
                if (!_awaiter.IsCompleted)               // fast path check
                {
                    _state = 0;
                    _builder.AwaitUnsafeOnCompleted(ref _awaiter, ref this); // boxes + returns
                    return;                              // <-- control returns to CALLER here
                }
            }
            _a = _awaiter.GetResult();                   // resumes here, rethrows exceptions
            _builder.SetResult(_a + 1);
        }
        catch (Exception ex) { _builder.SetException(ex); }  // exception -> faulted Task
    }
}
```

**The five things to say out loud:**

1. **`await` is not a thread switch.** It's `IsCompleted` → if false, register a continuation and *return to the caller*. No thread is blocked waiting for I/O; the OS signals completion via an IO completion port and a thread pool thread runs the continuation.
2. **The method returns at the first *incomplete* await**, not at the `async` keyword. Code before the first await runs **synchronously on the calling thread**.
3. **If everything completes synchronously, there is no suspension, no continuation, and no thread hop.** The state machine stays a struct on the stack. This is exactly the case `ValueTask` optimizes.
4. **First suspension is where the cost is:** the struct gets boxed to the heap, plus a `Task` and a delegate. That's ~3 allocations per suspended call — irrelevant per-request, expensive in a hot loop.
5. **Locals become fields.** Anything held across an `await` stays alive for the whole operation — a 2 MB byte array in scope across a 30-second HTTP call is 2 MB of gen-2 pressure.

**Q: Does `await` create a thread?**
A: No. `Task.Run` creates work *for* a pool thread. `await` on real I/O uses zero threads while pending.

> [!tip] Follow-up probe you should expect
> *"Where does the code after `await` run?"* → On whatever the awaiter's continuation was scheduled to: the captured `SynchronizationContext`/`TaskScheduler` if there is one, otherwise a thread pool thread. **ASP.NET Core has no `SynchronizationContext`** — so it's always a pool thread, and you may resume on a different thread than you started on. Never assume thread affinity; never use `[ThreadStatic]` across an await.

---

### Task vs ValueTask

**Q: When would you return `ValueTask<T>` instead of `Task<T>`?**

A: When the method **usually completes synchronously** and sits on a **hot path**. `Task<T>` is a class — every non-cached completion allocates. `ValueTask<T>` is a struct that wraps *either* a result, *or* a `Task<T>`, *or* an `IValueTaskSource<T>` — so a synchronous completion allocates nothing.

| | `Task<T>` | `ValueTask<T>` |
|---|---|---|
| Type | class (heap) | readonly struct |
| Sync completion | allocates (some values cached) | **zero allocation** |
| Await more than once | safe | **undefined behavior** |
| `Task.WhenAll` / `WhenAny` | yes | must call `.AsTask()` first |
| Store in a field / cache | safe | unsafe (unless `.AsTask()`) |
| Default choice | **yes** | only after measuring |

```csharp
// Good ValueTask case: cache hit is the common path
public ValueTask<User> GetUserAsync(Guid id)
{
    if (_cache.TryGetValue(id, out var user))
        return new ValueTask<User>(user);      // no allocation at all
    return new ValueTask<User>(LoadFromDbAsync(id));  // rare path wraps a Task
}

// The rules you must not break
var vt = GetUserAsync(id);
var a = await vt;
var b = await vt;   // BUG: awaiting twice is undefined behaviour
var t = vt.AsTask(); // do this if you need to await twice, store, or WhenAll
```

**Say this:** "Framework hot paths use it — `Channel<T>.ReadAsync`, `Stream.ReadAsync`, `IAsyncEnumerator.MoveNextAsync`. In my own application code I default to `Task` because `ValueTask` buys nothing when the method really does I/O, and it adds a foot-gun."

---

### ConfigureAwait(false)

**Q: What does `ConfigureAwait(false)` do, and do you still need it in ASP.NET Core?**

A: `await task` captures the current `SynchronizationContext` (or `TaskScheduler.Current`) and posts the continuation back to it. `ConfigureAwait(false)` says **"don't marshal me back — resume anywhere."**

- **UI apps (WPF/WinForms) and legacy ASP.NET (Framework):** there *is* a context. Not using it in library code is how sync-over-async deadlocks happen.
- **ASP.NET Core:** there is **no `SynchronizationContext`**, so `ConfigureAwait(false)` changes nothing functionally in app code — that's why you rarely see it in controllers.
- **Library code: still use it.** Your library doesn't know who consumes it; a WPF app calling `.Result` on your method will deadlock without it.

```csharp
// Library code — always
var data = await _http.GetStringAsync(url).ConfigureAwait(false);

// .NET 8+ options flavour
await task.ConfigureAwait(ConfigureAwaitOptions.None);            // == false
await task.ConfigureAwait(ConfigureAwaitOptions.SuppressThrowing); // await completion, ignore fault
```

> [!warning] The honest answer
> "`ConfigureAwait(false)` is a *library* concern, not a performance trick. It does not fix thread pool starvation and it does not make blocking safe."

---

### Sync-over-async and deadlocks

**Q: Why does `.Result` / `.Wait()` deadlock?**

A: Classic single-threaded-context deadlock:

```csharp
// UI thread or legacy ASP.NET request thread
public ActionResult Get()
{
    var data = GetDataAsync().Result;   // (1) blocks THIS thread
    return View(data);
}

private async Task<string> GetDataAsync()
{
    await _http.GetStringAsync(url);    // (2) captures the context
    return "done";                      // (3) continuation must run ON the blocked thread
}
```

1. The caller blocks the one thread that owns the context.
2. The continuation is posted **to that same context**.
3. The context never becomes free → both wait forever. **Deadlock.**

**Q: ASP.NET Core has no context — so blocking is fine now?**
A: **No.** The failure mode just changes from *deadlock* to **thread pool starvation**: each blocked request consumes a pool thread doing nothing. The pool injects new threads only ~1–2 per second (hill climbing), so under a burst you get a latency cliff, queued work, and rising `ThreadPool.ThreadCount` while CPU sits near idle.

```csharp
// Symptoms to name in the interview:
// - p99 latency explodes, CPU is low
// - dotnet-counters: threadpool-queue-length climbing, threadpool-thread-count climbing slowly
// - "it works in dev, dies at 200 rps"

// Fixes, in order:
// 1. async all the way up (real fix)
// 2. never .Result/.Wait()/.GetAwaiter().GetResult() on a request path
// 3. ThreadPool.SetMinThreads() = a tourniquet, not a cure
```

**Where sync-over-async is acceptable:** `Main()` before the async entry point, a console tool, or a constructor/`IDisposable` you cannot make async — and you say that out loud as a known cost.

---

### CancellationToken propagation

**Q: How do you handle cancellation properly?**

A: One token flows from the entry point to every async call, unchanged. Cancellation is **cooperative** — nothing is cancelled unless someone checks.

```csharp
[HttpGet]
public async Task<IActionResult> Search(string q, CancellationToken ct)  // bound to HttpContext.RequestAborted
{
    var result = await _mediator.Send(new SearchQuery(q), ct);
    return Ok(result);
}

public async Task<List<Item>> Handle(SearchQuery q, CancellationToken ct)
{
    // pass it down EVERY layer — EF Core, HttpClient, Redis, Channels all accept one
    var items = await _db.Items.Where(i => i.Name.Contains(q.Text))
                               .ToListAsync(ct);

    foreach (var item in items)
    {
        ct.ThrowIfCancellationRequested();     // check inside long CPU loops
        Enrich(item);
    }
    return items;
}
```

**Combining and timing out:**

```csharp
// Caller's cancellation + your own timeout
using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
timeout.CancelAfter(TimeSpan.FromSeconds(5));
await _http.GetAsync(url, timeout.Token);

// .NET 8+: CancellationTokenSource.CancelAsync() for async-safe cancellation
```

**The senior points:**
- `OperationCanceledException` is **expected control flow, not an error** — don't log it as an exception, don't return 500. A cancelled HTTP request gets no response anyway (client is gone).
- **Do not pass a request token into fire-and-forget or post-commit work.** If the client disconnects mid-request, you don't want your outbox publish cancelled halfway.
- **Be careful cancelling around commits:** cancelling `SaveChangesAsync` after the command reached the server leaves you *unsure* whether it committed. For money-moving operations, either use `CancellationToken.None` on the commit or make the operation idempotent — see [[18-Distributed-Systems-Reliability|Idempotency]].
- Background services get a token from `ExecuteAsync(CancellationToken stoppingToken)` — honour it or your pod fails graceful shutdown and gets SIGKILLed.

---

### async void, exceptions, and parallel awaits

**Q: When is `async void` acceptable?**
A: Event handlers only. Everywhere else it's a bug: the caller can't await it, and an unhandled exception is thrown on the pool thread and **crashes the process** instead of faulting a task.

```csharp
public async void Button_Click(object s, EventArgs e) { ... }   // only legal use
public async void ProcessOrder() { ... }                        // BUG: use async Task
```

**Q: How are exceptions handled in async code?**
A: They're captured into the returned `Task` and rethrown at the `await` — so an unobserved task swallows them silently.

```csharp
// Sequential: 3 x 200ms = 600ms
var a = await GetAAsync(); var b = await GetBAsync(); var c = await GetCAsync();

// Concurrent: ~200ms — use when calls are independent
var ta = GetAAsync(); var tb = GetBAsync(); var tc = GetCAsync();
await Task.WhenAll(ta, tb, tc);
var (x, y, z) = (ta.Result, tb.Result, tc.Result);  // safe: already completed

// GOTCHA: WhenAll rethrows only the FIRST exception at the await.
try { await Task.WhenAll(tasks); }
catch (Exception)
{
    // to see them all:
    var all = tasks.Where(t => t.IsFaulted).Select(t => t.Exception!).ToList();
}
```

> [!warning] `Task.WhenAll` on a `DbContext`
> `DbContext` is **not thread-safe**. Firing three EF queries concurrently on one context throws *"A second operation was started on this context"*. Parallelise with separate contexts from `IDbContextFactory`, or don't parallelise.

---

## Concurrency and Thread Safety

**Q: `Thread` vs `Task` vs the thread pool — how do they relate?**

A: A **`Thread`** is an OS resource: ~1 MB of committed stack, kernel scheduling, and expensive to create. The **thread pool** is a reusable set of them so you don't pay that cost per work item. A **`Task`** is not a thread at all — it's a *promise of a future result*; it may run on a pool thread, or on no thread whatsoever (I/O), or inline on the current one.

| | `new Thread(...)` | `Task.Run(...)` | `await` on I/O |
|---|---|---|---|
| Costs a thread | yes, a dedicated one | yes, a pooled one | **no** |
| Right for | a long-running, dedicated loop; foreground/background control; setting apartment state | **CPU-bound** work you want off the current thread | **I/O-bound** work — the default |
| Wrong for | short work (creation dominates) | wrapping blocking I/O to "make it async" — this **steals** a pool thread and causes starvation | CPU-bound work (it never yields) |

**The line that matters:** *"`Task.Run` doesn't make code asynchronous — it moves blocking code to a different thread. Real async I/O uses no thread at all while it waits."* On a server, wrapping sync I/O in `Task.Run` is strictly worse than calling it directly: same blocking, plus a context switch, plus one fewer pool thread for real requests. It's only genuinely useful in **UI apps** (get work off the UI thread) or for real **CPU-bound** work.

**Q: `lock` vs `SemaphoreSlim` — when do you use which?**

A: `lock` (Monitor) is synchronous and **cannot be held across an `await`** — the compiler won't even let you `await` inside a `lock` block, because Monitor is thread-affine and the continuation may resume on another thread. For async mutual exclusion, use `SemaphoreSlim(1, 1)`.

```csharp
// Sync critical section
private readonly object _gate = new();
lock (_gate) { _counter++; }

// Async critical section (a mutex with count 1)
private readonly SemaphoreSlim _mutex = new(1, 1);

await _mutex.WaitAsync(ct);
try { await DoExclusiveWorkAsync(ct); }
finally { _mutex.Release(); }        // ALWAYS in finally, or you leak a permit forever
```

**Q: How do you throttle concurrency (e.g. max 10 outbound calls at once)?**

```csharp
var throttle = new SemaphoreSlim(10);
var tasks = urls.Select(async url =>
{
    await throttle.WaitAsync(ct);
    try { return await _http.GetStringAsync(url, ct); }
    finally { throttle.Release(); }
});
var results = await Task.WhenAll(tasks);

// .NET 6+ cleaner equivalent:
await Parallel.ForEachAsync(urls,
    new ParallelOptions { MaxDegreeOfParallelism = 10, CancellationToken = ct },
    async (url, token) => await ProcessAsync(url, token));
```

**Q: What is `Interlocked` for?**

A: Lock-free atomic operations on a single 32/64-bit value — far cheaper than a lock for counters and flags.

```csharp
Interlocked.Increment(ref _requestCount);
Interlocked.Add(ref _bytes, len);
Interlocked.Exchange(ref _current, newValue);

// Compare-And-Swap: the building block of lock-free algorithms
var original = Interlocked.CompareExchange(ref _state, newState, expectedState);
if (original == expectedState) { /* we won the race */ }

// Run-once initialization without a lock
if (Interlocked.CompareExchange(ref _initialized, 1, 0) == 0) { Initialize(); }
```

`volatile` only guarantees *visibility/ordering*, never atomicity — `volatile int x; x++` is still a race. `Interlocked` is the correct tool.

**Q: What is `Channel<T>` and when do you reach for it?**

A: An in-process, async, thread-safe producer/consumer queue — the modern replacement for `BlockingCollection<T>` because it never blocks a thread. Use it for in-memory pipelines: request → background writer, batching, fan-out to workers.

```csharp
// Bounded channel = backpressure. Unbounded = an OOM waiting to happen.
var channel = Channel.CreateBounded<Order>(new BoundedChannelOptions(1_000)
{
    FullMode = BoundedChannelFullMode.Wait,   // producer awaits instead of dropping
    SingleReader = false,
    SingleWriter = false
});

// Producer (e.g. an API endpoint)
await channel.Writer.WriteAsync(order, ct);   // suspends (no thread blocked) when full

// Consumer (a BackgroundService)
await foreach (var order in channel.Reader.ReadAllAsync(stoppingToken))
    await _processor.HandleAsync(order, stoppingToken);

channel.Writer.Complete();  // signals ReadAllAsync to finish
```

> [!warning] The trade-off you must name
> A `Channel<T>` lives **in one process's memory**. If the pod dies, the queued work is gone, and it doesn't spread across instances. It is a buffer, **not a message broker** — the moment you need durability, retries, or cross-service delivery, that's RabbitMQ. See [[18-Distributed-Systems-Reliability#Hangfire vs a real broker|Hangfire vs a real broker]].

**Q: What is thread pool starvation? How do you diagnose it?**

A: All pool threads are blocked (not busy), so queued work items — including async continuations — can't run. The pool grows by only ~1–2 threads/second, so recovery is glacial.

| | Symptom | Cause |
|---|---|---|
| **Starvation** | high latency, **low CPU**, rising thread count | blocking calls (`.Result`, `Thread.Sleep`, sync I/O, `lock` contention) on pool threads |
| **CPU saturation** | high latency, **high CPU** | genuinely too much work → scale out |

```bash
# Diagnose (say these tool names, it lands well)
dotnet-counters monitor --process-id <pid> System.Runtime
#   threadpool-queue-length  -> climbing = starvation
#   threadpool-thread-count  -> creeping up ~1/sec = injection, confirms it
dotnet-dump analyze <dump>   # then: clrthreads / parallelstacks -> everyone in WaitOne
```

**Causes, in the order they actually happen:** sync-over-async on a request path · a `lock` held during I/O · `Task.Run` wrapping sync-blocking code to "make it async" · exhausted connection pool making every request wait · `SemaphoreSlim.Wait()` instead of `WaitAsync()`.

**Q: Are the concurrent collections a silver bullet?**

```csharp
var dict = new ConcurrentDictionary<string, Lazy<User>>();

// GOTCHA: GetOrAdd's factory can run MULTIPLE times under contention
// (only one result is stored, but the factory is not exclusive)
var user = dict.GetOrAdd(key, k => new Lazy<User>(() => LoadExpensive(k))).Value;
// Lazy<T> makes the expensive work run exactly once.
```

`ConcurrentDictionary` makes *individual operations* atomic — it does not make your *sequence* of operations atomic. `if (!dict.ContainsKey(k)) dict.TryAdd(k, v);` is still a race; use `GetOrAdd`/`AddOrUpdate`.

---

---

# Part 4 — Collections, Iterators & LINQ

> [!info] Collection *choice* lives next door
> `List` vs `Dictionary` vs `HashSet` vs `Queue`, their Big-O, and when each is the right structure are in [[05-Data-Structures-Algorithms|Data Structures & Algorithms]]. This part is about how you **traverse and query** them — the part that shows up in .NET code review.

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

**The senior addendum:** `IQueryable` **inherits** `IEnumerable`, so a single stray `.AsEnumerable()`, `.ToList()`, or an untranslatable call silently moves the rest of the pipeline into memory — the whole table comes back and gets filtered client-side. Know exactly where in your chain the transition happens, and put it there **deliberately**.

---

## Iterators — yield return

**Q: What does `yield return` do?**

A: It tells the compiler to build a **state machine** implementing `IEnumerable<T>`/`IEnumerator<T>` — the same idea as `async`. The method body doesn't run when you call it; it runs **one `MoveNext()` at a time**, pausing at each `yield return` and resuming there on the next iteration.

```csharp
public IEnumerable<int> GetNumbers()
{
    Console.WriteLine("start");     // does NOT print when you call GetNumbers()
    for (int i = 0; i < 3; i++)
    {
        Console.WriteLine($"yielding {i}");
        yield return i;             // pauses here, hands the value to the caller
    }
    Console.WriteLine("done");
}

var seq = GetNumbers();             // prints nothing — nothing has run yet
foreach (var n in seq.Take(2)) { }  // start / yielding 0 / yielding 1  — and never "done"
```

**Why it matters (the reasons to give):**
- **Lazy + streaming** — you process one item at a time instead of materialising a list. Reading a 5 GB file line by line uses constant memory; `File.ReadAllLines` does not.
- **Infinite sequences become possible** — `while (true) yield return Next();` composes safely with `Take(10)`.
- **Early exit does no wasted work** — `First()` over an iterator stops the producer immediately.
- It's how **`Where`/`Select` are implemented**; understanding `yield` is understanding deferred execution.

```csharp
// Constant memory over an arbitrarily large file
public IEnumerable<Order> ReadOrders(string path)
{
    using var reader = new StreamReader(path);        // disposed when enumeration ends OR breaks
    while (reader.ReadLine() is { } line)
        yield return Parse(line);
}
```

**The three traps:**
1. **Argument validation doesn't run until enumeration.** `if (path is null) throw` inside an iterator throws at the first `foreach`, not at the call — far from the bug. Fix: a normal wrapper method that validates, then returns a private iterator method.
2. **Re-enumeration re-executes everything.** The sequence is a recipe, not a result — `foreach` twice = the file is read twice. Same bug family as [[#Deferred execution|multiple enumeration]].
3. **`using`/`try-finally` inside an iterator only runs if the enumerator is disposed** — `foreach` does that for you, but a manual `MoveNext()` loop must dispose or the file handle leaks. Also: **`yield return` is not allowed inside a `try` with a `catch`**.

---

## IAsyncEnumerable and await foreach

**Q: What problem does `IAsyncEnumerable<T>` solve?**

A: Streaming **asynchronous** data. Before C# 8 you had to choose between `Task<List<T>>` (async, but buffers everything in memory before returning anything) and `IEnumerable<T>` (streams, but each step blocks a thread). `IAsyncEnumerable<T>` gives you both: yield items as they arrive, without blocking.

```csharp
public async IAsyncEnumerable<Order> StreamOrdersAsync(
    [EnumeratorCancellation] CancellationToken ct = default)   // <- required attribute
{
    await foreach (var order in _db.Orders.AsAsyncEnumerable().WithCancellation(ct))
    {
        yield return order;          // one row at a time, constant memory
    }
}

await foreach (var order in StreamOrdersAsync(ct))
    await ProcessAsync(order, ct);
```

**Where it earns its place:** paging through a large result set without loading it all · consuming `Channel<T>.Reader.ReadAllAsync()` · gRPC/SignalR server streaming · exporting a huge report row by row · any producer/consumer pipeline. In ASP.NET Core, returning `IAsyncEnumerable<T>` from an action **streams the JSON response** instead of buffering it.

**The details that get noticed:**
- `[EnumeratorCancellation]` is what makes `WithCancellation(ct)` actually reach your method — without it the token is silently ignored.
- Use `.ConfigureAwait(false)` via `await foreach (... .ConfigureAwait(false))` in library code.
- **It's sequential by design.** Ten items each taking 100 ms take a second; if the work is independent, that's a job for `Task.WhenAll` or `Parallel.ForEachAsync`, not a stream.
- LINQ operators don't apply directly — you need the **`System.Linq.Async`** package, or just write the loop.

---

## LINQ Deep Dive

**Q: What is LINQ, actually?**

A: Language Integrated Query — a set of standard operators plus compiler support (query syntax, lambdas, expression trees) that gives one query language over any data source. It has **two completely different execution engines**, and confusing them is the #1 LINQ bug:

| | LINQ to Objects | LINQ to Entities |
|---|---|---|
| Interface | `IEnumerable<T>` | `IQueryable<T>` |
| Lambda compiles to | `Func<T, bool>` — **compiled code** | `Expression<Func<T, bool>>` — **a data tree** |
| Runs where | in your process, in memory | translated to SQL, runs on the DB |
| `Where` after `ToList()` | filters in memory | — |

```csharp
// Query syntax is sugar; both compile to the same thing
var a = from u in users where u.Age > 18 orderby u.Name select u.Name;
var b = users.Where(u => u.Age > 18).OrderBy(u => u.Name).Select(u => u.Name);
```

### Deferred execution

**Q: When does a LINQ query actually run?**

A: Not when you build it — when you **enumerate** it. `Where`, `Select`, `OrderBy`, `Take` are all lazy; they return a query object. Execution is forced by `foreach`, `ToList()`, `ToArray()`, `ToDictionary()`, `Count()`, `Sum()`, `First()`, `Any()`, `Single()`.

```csharp
var query = numbers.Where(n => { Console.WriteLine($"testing {n}"); return n > 2; });
Console.WriteLine("query built");   // nothing printed from the lambda yet
var list = query.ToList();          // NOW the lambda runs
```

**The three bugs deferred execution causes:**

```csharp
// 1) MULTIPLE ENUMERATION — this hits the database twice
IEnumerable<Order> orders = _db.Orders.Where(o => o.IsActive);
if (orders.Any())                       // SELECT #1
    foreach (var o in orders) { ... }   // SELECT #2, and the data may differ
// Fix: materialise once -> var orders = await _db.Orders.Where(...).ToListAsync(ct);

// 2) CAPTURED STATE CHANGES AFTER THE QUERY IS BUILT
int threshold = 5;
var q = numbers.Where(n => n > threshold);
threshold = 100;                        // the lambda reads the variable at ENUMERATION time
var result = q.ToList();                // filters by 100, not 5

// 3) DISPOSED SOURCE
IEnumerable<User> GetUsers()
{
    using var db = new AppDbContext();
    return db.Users.Where(u => u.IsActive);   // BUG: context disposed before enumeration
}   // -> ObjectDisposedException at the caller. Return ToList() or don't dispose here.
```

**Streaming vs buffering operators** — worth knowing why `OrderBy` on a huge sequence blows memory:

- **Streaming** (one item at a time): `Where`, `Select`, `Take`, `Skip`, `SelectMany`, `Zip`
- **Buffering** (must read everything first): `OrderBy`, `GroupBy`, `Reverse`, `Join`, `Distinct`, `ToList`

### Closure capture in loops

**Q: What does this print?**

```csharp
var actions = new List<Action>();
for (int i = 0; i < 3; i++)
    actions.Add(() => Console.WriteLine(i));

foreach (var a in actions) a();   // prints 3, 3, 3  — NOT 0, 1, 2
```

A: The lambda captures the **variable**, not its value. A `for` loop has **one** `i` for all iterations — the compiler hoists it into a single closure object shared by all three lambdas. By the time they run, `i == 3`.

```csharp
// Fix: give each iteration its own variable
for (int i = 0; i < 3; i++)
{
    int copy = i;                                  // new variable per iteration
    actions.Add(() => Console.WriteLine(copy));    // 0, 1, 2
}
```

**`foreach` is different:** since **C# 5** the iteration variable is a *fresh* variable each pass, so `foreach (var x in items) tasks.Add(() => Use(x));` behaves as you'd expect. (In C# 4 and earlier it had the same bug — a good "how long have you been doing this" question.)

**Where this really bites — async in a loop:**

```csharp
for (int i = 0; i < files.Count; i++)
    tasks.Add(Task.Run(() => Process(files[i])));   // BUG: i is shared -> IndexOutOfRange or wrong file

foreach (var file in files)
    tasks.Add(Task.Run(() => Process(file)));       // correct
```

Also remember every closure that captures state **allocates** a display class — in a tight loop that's real GC pressure, and it's why `foreach` with a static lambda (`static u => u.Id`) is free while a capturing one is not.

### IQueryable pitfalls the interviewer is fishing for

```csharp
// 1) N+1: one query for orders, then one per order
var orders = await _db.Orders.ToListAsync(ct);
foreach (var o in orders) Console.WriteLine(o.Customer.Name);   // lazy load per row
// Fix: .Include(o => o.Customer) or project only what you need

// 2) Fetching whole entities when you need 2 columns
var names = await _db.Users.Select(u => new { u.Id, u.Name }).ToListAsync(ct); // projection

// 3) Read-only queries still build the change tracker
var report = await _db.Orders.AsNoTracking().ToListAsync(ct);

// 4) Untranslatable method -> EF Core 3+ THROWS instead of silently pulling the table
var bad = await _db.Users.Where(u => MyHelper.IsValid(u)).ToListAsync(ct);  // InvalidOperationException
// Fix: express it in translatable terms, or .AsEnumerable() at a deliberate point (and own the cost)

// 5) Cheaper existence + row counts
await _db.Orders.AnyAsync(o => o.UserId == id, ct);      // EXISTS  -> good
(await _db.Orders.CountAsync(...)) > 0;                  // COUNT(*) -> wasteful
await _db.Users.FirstOrDefaultAsync(...);                // TOP 1
await _db.Users.SingleOrDefaultAsync(...);               // TOP 2 — asserts uniqueness, costs more

// 6) Multiple Includes -> cartesian explosion; use AsSplitQuery()
var o = await _db.Orders.Include(x => x.Lines).Include(x => x.Payments)
                        .AsSplitQuery().ToListAsync(ct);
```

> [!tip] The senior framing
> "`IQueryable` is a **leaky, powerful abstraction**: it looks like LINQ but the provider decides what's expressible. That's precisely why leaking `IQueryable` out of the data layer is a design decision with a cost — see [[17-Architecture-Defense#Repository over EF Core|Repository over EF Core]]."

---

---

# Part 5 — Rapid-Fire Drill

Answer each in **one or two sentences**, out loud, before checking above. Grouped by part, so you can drill one part at a time.

### Drill 1 — Type system & language core

| # | Question | The one-line answer |
|---|---|---|
| 1 | `==` vs `.Equals()`? | `==` is static, bound at **compile time** by the declared type; `Equals` is virtual, resolved at **run time** by the actual type. |
| 2 | Why override `GetHashCode` with `Equals`? | Hash collections find the bucket by hash first — equal objects that hash differently are never compared, so lookups silently fail. |
| 3 | Can a `record` be a safe dictionary key? | Only if its members are value-comparable; a `List<T>` member is compared **by reference**. |
| 4 | `throw;` vs `throw ex;`? | `throw;` preserves the original stack trace; `throw ex;` resets it to that line. |
| 5 | Why an exception filter (`when`) instead of catch-and-rethrow? | The filter runs **before** the stack unwinds, so state and trace survive if it doesn't match. |
| 6 | Why can't `List<string>` be a `List<object>`? | It's invariant — `T` goes both in and out, so it'd let you `Add(42)`. `out`/`in` declare the safe cases; arrays got this wrong. |
| 7 | `ref` vs `out` vs `in`? | In-and-out · must be assigned before return · read-only (and only pays off with `readonly struct`). |
| 8 | Does passing a `List<T>` by value let me reassign it for the caller? | No — mutations are visible, reassignment isn't. That needs `ref`. |
| 9 | Exception or `Result`? | Business contract the caller must handle → `Result`. Bug or infrastructure → exception. Not a performance argument. |
| 10 | How does the **control flow** differ? | Exception = non-local jump, the stack unwinds to whoever catches. `Result` = ordinary local branching at the call site. |
| 11 | So what's the *cost* of Result's local control flow? | You propagate by hand through every layer — exceptions do it for free, and one missing `if` swallows the failure. |
| 12 | With `Result`, do you still need exception middleware? | Yes — `Result` covers the failures you predicted; the middleware covers the ones you didn't. |

### Drill 2 — Memory & GC

| # | Question | The one-line answer |
|---|---|---|
| 13 | When is a `struct` worth it? | Small, immutable, short-lived, allocated in bulk — otherwise copying costs more. |
| 14 | Where does boxing hide? | Non-generic collections, value-type→interface, `Enum.Equals`, structs without `IEquatable<T>`. |
| 15 | Which GC generation should you fear? | Gen 2 / LOH (≥85 KB) — expensive and uncompacted. Watch allocation rate and `time-in-gc`. |
| 16 | Why `GC.SuppressFinalize` in `Dispose`? | A finalizable object otherwise survives a collection and gets promoted. |
| 17 | Why not `new HttpClient()` per request? | Socket exhaustion via `TIME_WAIT`. Use `IHttpClientFactory`. |
| 18 | Who disposes an injected `DbContext`? | The DI scope, at end of request. Never wrap it in `using`. |
| 19 | What's a captive dependency? | A singleton holding a scoped service — e.g. a `DbContext` shared across requests and threads, forever. |

### Drill 3 — Async & concurrency

| # | Question | The one-line answer |
|---|---|---|
| 20 | Does `await` start a thread? | No. It registers a continuation and returns; I/O waits use no thread. |
| 21 | Where does code after `await` resume? | Captured context if one exists; in ASP.NET Core there is none, so a pool thread. |
| 22 | `Task` or `ValueTask` by default? | `Task`. `ValueTask` only for hot paths that usually complete synchronously — and never awaited twice. |
| 23 | Is `ConfigureAwait(false)` needed in ASP.NET Core? | Not functionally (no `SynchronizationContext`); still yes in libraries. |
| 24 | Why does `.Result` deadlock? | Continuation is posted to the context the caller is blocking. |
| 25 | And in ASP.NET Core, where there's no context? | No deadlock — thread pool starvation instead: high latency, low CPU. |
| 26 | Is `OperationCanceledException` an error? | No, it's expected control flow. Don't log it as a failure or return 500. |
| 27 | `lock` inside `async`? | Illegal across `await`; use `SemaphoreSlim(1,1)` and `Release()` in `finally`. |
| 28 | Does `Task.Run` make blocking I/O asynchronous? | No — it moves the blocking to a pool thread. On a server that's strictly worse. |
| 29 | `Channel<T>` vs RabbitMQ? | In-process buffer vs durable cross-service delivery. A channel dies with the pod. |
| 30 | Why is `Interlocked` better than `lock` for a counter? | Single atomic CPU instruction, no kernel transition, no contention convoy. |
| 31 | Three EF queries with `Task.WhenAll`? | Throws — `DbContext` isn't thread-safe. Use `IDbContextFactory` or go sequential. |

### Drill 4 — Collections, iterators & LINQ

| # | Question | The one-line answer |
|---|---|---|
| 32 | Why did my `for` loop lambdas all print the last value? | One shared variable captured by reference; copy it inside the loop. `foreach` is safe since C# 5. |
| 33 | Why did `Any()` then `foreach` hit the DB twice? | Deferred execution — the `IEnumerable` re-executes per enumeration. Materialise once. |
| 34 | `Count() > 0` or `Any()`? | `Any()` → `EXISTS`; `Count()` scans. |
| 35 | What does `yield return` build? | A lazy state machine — the body runs one `MoveNext()` at a time, so validation and side effects are deferred too. |
| 36 | `Task<List<T>>` vs `IAsyncEnumerable<T>`? | Buffer everything then return, vs stream items as they arrive in constant memory. |
| 37 | Where does `IQueryable` become `IEnumerable`? | At `ToList`/`AsEnumerable`/any untranslatable call — after which the rest runs in memory on the whole table. |
