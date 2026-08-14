---
title: OOP Principles
aliases: [OOP, OOP Principles]
tags: [csharp, oop, fundamentals, interview]
order: 1
---

# OOP Principles - Interview Q&A

> [!info]+ Related Notes
> [[02-SOLID-Principles|SOLID Principles]] · [[03-Design-Patterns|Design Patterns]] · [[04-CSharp-Fundamentals|C# Fundamentals]]

## Four Pillars of OOP

**Q: Explain the four pillars of OOP?**

A: 
- **Encapsulation**: Bundling data and methods, hiding internal state
- **Abstraction**: Hiding complexity, exposing essential features
- **Inheritance**: Code reuse, IS-A relationship
- **Polymorphism**: Same interface, different implementations

---

## Encapsulation

**Q: What is encapsulation?**

A: Bundling data (fields) and methods that operate on data into single unit (class). Hiding internal state using access modifiers. Exposing only necessary interface.

```csharp
public class BankAccount
{
    // Private fields - hidden from outside
    private decimal _balance;
    private string _accountNumber;
    
    // Public properties - controlled access
    public decimal Balance 
    { 
        get => _balance; 
        private set => _balance = value; 
    }
    
    public string AccountNumber 
    { 
        get => _accountNumber; 
    }
    
    public BankAccount(string accountNumber)
    {
        _accountNumber = accountNumber;
        _balance = 0;
    }
    
    // Public methods - exposed behavior
    public void Deposit(decimal amount)
    {
        if (amount <= 0)
            throw new ArgumentException("Amount must be positive");
            
        _balance += amount;
    }
    
    public void Withdraw(decimal amount)
    {
        if (amount > _balance)
            throw new InvalidOperationException("Insufficient funds");
            
        _balance -= amount;
    }
}

// Usage - internal state is protected
var account = new BankAccount("123456");
account.Deposit(100);
account.Withdraw(50);
// account._balance = 1000000;  // Cannot access - private
```

**Benefits:**
- Data protection
- Maintainability
- Flexibility to change implementation
- Validation in one place

---

## Abstraction

**Q: What is abstraction?**

A: Hiding complex implementation details and showing only necessary features. Focus on WHAT object does, not HOW it does it. Achieved through abstract classes and interfaces.

```csharp
// Abstract class
public abstract class PaymentProcessor
{
    // Template method - defines algorithm structure
    public void ProcessPayment(decimal amount)
    {
        ValidateAmount(amount);
        AuthorizePayment(amount);
        ExecutePayment(amount);
        SendConfirmation();
    }
    
    // Concrete method
    private void ValidateAmount(decimal amount)
    {
        if (amount <= 0)
            throw new ArgumentException("Invalid amount");
    }
    
    // Abstract methods - subclasses provide implementation
    protected abstract void AuthorizePayment(decimal amount);
    protected abstract void ExecutePayment(decimal amount);
    
    // Virtual method - can be overridden
    protected virtual void SendConfirmation()
    {
        Console.WriteLine("Payment processed");
    }
}

// Concrete implementations
public class CreditCardProcessor : PaymentProcessor
{
    protected override void AuthorizePayment(decimal amount)
    {
        // Credit card authorization logic
        Console.WriteLine("Authorizing credit card");
    }
    
    protected override void ExecutePayment(decimal amount)
    {
        // Execute payment through credit card gateway
        Console.WriteLine($"Charging ${amount} to credit card");
    }
}

public class PayPalProcessor : PaymentProcessor
{
    protected override void AuthorizePayment(decimal amount)
    {
        // PayPal authorization logic
        Console.WriteLine("Authorizing PayPal");
    }
    
    protected override void ExecutePayment(decimal amount)
    {
        // Execute payment through PayPal API
        Console.WriteLine($"Charging ${amount} through PayPal");
    }
}

// Usage - Don't care about HOW payment is processed
PaymentProcessor processor = new CreditCardProcessor();
processor.ProcessPayment(100.00m);  // Just call, abstraction handles details
```

**Benefits:**
- Reduces complexity
- Increases reusability
- Easy to maintain
- Focus on high-level operations

---

## Inheritance

**Q: What is inheritance?**

A: Mechanism where new class derives from existing class. Child class inherits members from parent class. Promotes code reuse. Represents IS-A relationship.

```csharp
// Base class
public class Employee
{
    public int Id { get; set; }
    public string Name { get; set; }
    public decimal BaseSalary { get; set; }
    
    public virtual decimal CalculateSalary()
    {
        return BaseSalary;
    }
    
    public void DisplayInfo()
    {
        Console.WriteLine($"{Name} - {Id}");
    }
}

// Derived class
public class Manager : Employee
{
    public decimal Bonus { get; set; }
    
    // Override base method
    public override decimal CalculateSalary()
    {
        return BaseSalary + Bonus;
    }
    
    // Add new functionality
    public void ManageTeam()
    {
        Console.WriteLine($"{Name} is managing team");
    }
}

public class Developer : Employee
{
    public string ProgrammingLanguage { get; set; }
    
    public override decimal CalculateSalary()
    {
        // Different calculation for developers
        return BaseSalary * 1.1m;  // 10% extra
    }
    
    public void WriteCode()
    {
        Console.WriteLine($"{Name} is writing {ProgrammingLanguage} code");
    }
}

// Usage
Manager manager = new Manager 
{ 
    Name = "Alice", 
    BaseSalary = 80000, 
    Bonus = 10000 
};
Console.WriteLine(manager.CalculateSalary());  // 90000
manager.DisplayInfo();  // Inherited method
manager.ManageTeam();   // New method

Developer dev = new Developer 
{ 
    Name = "Bob", 
    BaseSalary = 70000,
    ProgrammingLanguage = "C#"
};
Console.WriteLine(dev.CalculateSalary());  // 77000
```

**Types of Inheritance in C#:**
- Single inheritance (class can inherit from one class)
- Multi-level inheritance (chain of inheritance)
- Interface inheritance (multiple interfaces allowed)

**Note:** C# doesn't support multiple class inheritance to avoid diamond problem.

---

## Polymorphism

**Q: What is polymorphism? Types?**

A: Ability to take multiple forms. Same interface, different implementations.

### Compile-time Polymorphism (Static)

**Method Overloading:**
```csharp
public class Calculator
{
    // Same method name, different parameters
    public int Add(int a, int b)
    {
        return a + b;
    }
    
    public int Add(int a, int b, int c)
    {
        return a + b + c;
    }
    
    public double Add(double a, double b)
    {
        return a + b;
    }
}

// Usage
var calc = new Calculator();
calc.Add(1, 2);           // Calls first method
calc.Add(1, 2, 3);        // Calls second method
calc.Add(1.5, 2.5);       // Calls third method
```

**Operator Overloading:**
```csharp
public class Vector
{
    public int X { get; set; }
    public int Y { get; set; }
    
    // Overload + operator
    public static Vector operator +(Vector v1, Vector v2)
    {
        return new Vector 
        { 
            X = v1.X + v2.X, 
            Y = v1.Y + v2.Y 
        };
    }
}

// Usage
var v1 = new Vector { X = 1, Y = 2 };
var v2 = new Vector { X = 3, Y = 4 };
var v3 = v1 + v2;  // Uses overloaded operator
```

### Runtime Polymorphism (Dynamic)

**Method Overriding:**
```csharp
public class Shape
{
    public virtual double CalculateArea()
    {
        return 0;
    }
    
    public virtual void Draw()
    {
        Console.WriteLine("Drawing shape");
    }
}

public class Circle : Shape
{
    public double Radius { get; set; }
    
    public override double CalculateArea()
    {
        return Math.PI * Radius * Radius;
    }
    
    public override void Draw()
    {
        Console.WriteLine("Drawing circle");
    }
}

public class Rectangle : Shape
{
    public double Width { get; set; }
    public double Height { get; set; }
    
    public override double CalculateArea()
    {
        return Width * Height;
    }
    
    public override void Draw()
    {
        Console.WriteLine("Drawing rectangle");
    }
}

// Runtime polymorphism in action
Shape[] shapes = new Shape[]
{
    new Circle { Radius = 5 },
    new Rectangle { Width = 4, Height = 6 }
};

foreach (Shape shape in shapes)
{
    shape.Draw();  // Calls appropriate Draw method at runtime
    Console.WriteLine($"Area: {shape.CalculateArea()}");
}
```

**Interface Polymorphism:**
```csharp
public interface ILogger
{
    void Log(string message);
}

public class FileLogger : ILogger
{
    public void Log(string message)
    {
        File.AppendAllText("log.txt", message);
    }
}

public class ConsoleLogger : ILogger
{
    public void Log(string message)
    {
        Console.WriteLine(message);
    }
}

public class DatabaseLogger : ILogger
{
    public void Log(string message)
    {
        // Save to database
    }
}

// Polymorphic usage
public class Application
{
    private readonly ILogger _logger;
    
    public Application(ILogger logger)
    {
        _logger = logger;  // Any ILogger implementation
    }
    
    public void Run()
    {
        _logger.Log("Application started");  // Polymorphic call
    }
}
```

---

## Composition Over Inheritance

**Q: Explain composition over inheritance?**

A: Favor HAS-A relationships over IS-A relationships. More flexible, avoids tight coupling. Combine simple objects to create complex behavior.

```csharp
// BAD: Deep inheritance hierarchy
public class Animal { }
public class Mammal : Animal { }
public class Dog : Mammal 
{ 
    public void Bark() { }
}
public class Cat : Mammal 
{ 
    public void Meow() { }
}

// GOOD: Composition approach
public interface ISound
{
    void MakeSound();
}

public class BarkSound : ISound
{
    public void MakeSound() => Console.WriteLine("Woof!");
}

public class MeowSound : ISound
{
    public void MakeSound() => Console.WriteLine("Meow!");
}

public class Animal
{
    private readonly ISound _sound;
    
    public Animal(ISound sound)
    {
        _sound = sound;
    }
    
    public void Speak()
    {
        _sound.MakeSound();
    }
}

// Usage - More flexible
var dog = new Animal(new BarkSound());
var cat = new Animal(new MeowSound());

dog.Speak();  // Woof!
cat.Speak();  // Meow!
```

**Complex Example:**
```csharp
// Components
public interface IMovement
{
    void Move();
}

public interface IAttack
{
    void Attack();
}

public class WalkMovement : IMovement
{
    public void Move() => Console.WriteLine("Walking");
}

public class FlyMovement : IMovement
{
    public void Move() => Console.WriteLine("Flying");
}

public class MeleeAttack : IAttack
{
    public void Attack() => Console.WriteLine("Melee attack");
}

public class RangedAttack : IAttack
{
    public void Attack() => Console.WriteLine("Ranged attack");
}

// Composed class
public class GameCharacter
{
    private readonly IMovement _movement;
    private readonly IAttack _attack;
    
    public string Name { get; set; }
    
    public GameCharacter(string name, IMovement movement, IAttack attack)
    {
        Name = name;
        _movement = movement;
        _attack = attack;
    }
    
    public void Move() => _movement.Move();
    public void Attack() => _attack.Attack();
}

// Create different character types easily
var warrior = new GameCharacter("Warrior", new WalkMovement(), new MeleeAttack());
var archer = new GameCharacter("Archer", new WalkMovement(), new RangedAttack());
var dragon = new GameCharacter("Dragon", new FlyMovement(), new RangedAttack());

warrior.Move();   // Walking
warrior.Attack(); // Melee attack

dragon.Move();    // Flying
dragon.Attack();  // Ranged attack
```

**Benefits:**
- More flexible
- Easy to test (inject dependencies)
- Avoid fragile base class problem
- Can change behavior at runtime

---

## SOLID Principles Preview

The SOLID principles extend OOP concepts:

1. **Single Responsibility** - Class should have one reason to change
2. **Open/Closed** - Open for extension, closed for modification
3. **Liskov Substitution** - Derived classes must be substitutable
4. **Interface Segregation** - Many specific interfaces better than one general
5. **Dependency Inversion** - Depend on abstractions, not concretions

*(See SOLID-Principles.md for detailed examples)*
