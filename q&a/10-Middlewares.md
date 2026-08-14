---
title: ASP.NET Core Middlewares
aliases: [Middlewares, ASP.NET Middleware]
tags: [aspnet, middleware, interview]
order: 10
---

# ASP.NET Core Middlewares Interview Questions & Answers

> [!info]+ Related Notes
> [[09-Onion-Architecture|Onion Architecture]] · [[11-Module-Communication|Module Communication]]

## What is Middleware in ASP.NET Core?
**Answer:** Middleware is software assembled into the application pipeline to handle requests and responses. Each component can process the request, pass it to the next component, or short-circuit the pipeline.

## What is the Request Pipeline?
**Answer:** The request pipeline is a sequence of middleware components that process HTTP requests in order. Each middleware can perform operations before and after the next middleware in the pipeline.

## How do you register middleware?
**Answer:** Use the `Use`, `Run`, or `Map` methods in the `Configure` method of `Startup.cs` or `Program.cs`:
```csharp
app.UseMiddleware<CustomMiddleware>();
app.Use(async (context, next) => {
    // Before
    await next.Invoke();
    // After
});
```

## What is the difference between Use, Run, and Map?
**Answer:**
- **Use:** Adds middleware to the pipeline and can call next middleware
- **Run:** Terminal middleware that doesn't call next (ends pipeline)
- **Map:** Branches the pipeline based on request path

## What is the order of built-in middleware?
**Answer:**
1. ExceptionHandler
2. HSTS
3. HttpsRedirection
4. StaticFiles
5. Routing
6. CORS
7. Authentication
8. Authorization
9. Custom middleware
10. Endpoints

## How do you create custom middleware?
**Answer:**
```csharp
public class CustomMiddleware
{
    private readonly RequestDelegate _next;

    public CustomMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // Before logic
        await _next(context);
        // After logic
    }
}

// Extension method
public static class CustomMiddlewareExtensions
{
    public static IApplicationBuilder UseCustomMiddleware(
        this IApplicationBuilder builder)
    {
        return builder.UseMiddleware<CustomMiddleware>();
    }
}
```

## What is the purpose of UseExceptionHandler middleware?
**Answer:** UseExceptionHandler catches exceptions from subsequent middleware and executes an error-handling path, preventing unhandled exceptions from reaching the client.

## What is UseStaticFiles middleware?
**Answer:** UseStaticFiles enables serving static files (HTML, CSS, JS, images) from wwwroot. It short-circuits the pipeline if a matching file is found.

## What is UseRouting and UseEndpoints?
**Answer:** UseRouting adds route matching to the pipeline, and UseEndpoints executes the matched endpoint (controller action, Razor Page, etc.).

## What is the difference between Authentication and Authorization middleware?
**Answer:**
- **UseAuthentication:** Identifies who the user is (validates credentials, tokens)
- **UseAuthorization:** Determines what the user can access (checks permissions)

## What is CORS middleware?
**Answer:** CORS (Cross-Origin Resource Sharing) middleware enables cross-origin requests from browsers by adding appropriate headers, configured with policies for allowed origins, methods, and headers.

## How do you implement request logging middleware?
**Answer:**
```csharp
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, 
        ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        _logger.LogInformation($"Request: {context.Request.Method} {context.Request.Path}");
        await _next(context);
        _logger.LogInformation($"Response: {context.Response.StatusCode}");
    }
}
```

## What is middleware short-circuiting?
**Answer:** Short-circuiting occurs when middleware doesn't call `next()`, terminating the pipeline early. Examples include UseStaticFiles (when file found) or authorization failures.

## Can middleware be conditional?
**Answer:** Yes, use `UseWhen` to branch middleware conditionally:
```csharp
app.UseWhen(context => context.Request.Path.StartsWithSegments("/api"), 
    appBuilder => {
        appBuilder.UseMiddleware<ApiMiddleware>();
    });
```

## What is the difference between middleware and filters?
**Answer:**
- **Middleware:** Works at the application level, processes all requests
- **Filters:** Work at the MVC level, tied to controller actions with more specific scopes (action, controller, global)

## How do you handle dependency injection in middleware?
**Answer:** Constructor injection for singleton services, method injection for scoped services:
```csharp
public async Task InvokeAsync(HttpContext context, 
    IMyService myService) // Scoped service
{
    // Use myService
    await _next(context);
}
```

## What is response compression middleware?
**Answer:** UseResponseCompression middleware compresses HTTP responses (Gzip, Brotli) to reduce bandwidth and improve performance, configured with MIME types and compression levels.

## What is UseHsts middleware?
**Answer:** UseHsts adds the Strict-Transport-Security header, forcing browsers to use HTTPS for future requests, enhancing security.

## What is session middleware?
**Answer:** UseSession enables session state, storing user data across requests using cookies and server-side storage (in-memory, distributed cache, SQL Server).

## How do you implement rate limiting middleware?
**Answer:**
```csharp
public class RateLimitingMiddleware
{
    private readonly RequestDelegate _next;
    private static readonly Dictionary<string, Queue<DateTime>> _requests = new();

    public async Task InvokeAsync(HttpContext context)
    {
        var ip = context.Connection.RemoteIpAddress?.ToString();
        if (IsRateLimited(ip))
        {
            context.Response.StatusCode = 429;
            await context.Response.WriteAsync("Too many requests");
            return;
        }
        await _next(context);
    }
}
```

## What is middleware branching with MapWhen?
**Answer:** MapWhen branches the pipeline based on a predicate without rejoining the main pipeline:
```csharp
app.MapWhen(context => context.Request.Query.ContainsKey("debug"),
    appBuilder => {
        appBuilder.UseMiddleware<DebugMiddleware>();
    });
```

## Can you remove or replace middleware?
**Answer:** No, once added to the pipeline, middleware cannot be removed. Order matters—configure middleware carefully during application startup.

## What is the purpose of UseDeveloperExceptionPage?
**Answer:** UseDeveloperExceptionPage displays detailed exception information (stack traces, headers) during development, helping diagnose issues. Never use in production.

## How do you test custom middleware?
**Answer:** Create a mock HttpContext and RequestDelegate:
```csharp
[Test]
public async Task Middleware_ShouldLogRequest()
{
    var context = new DefaultHttpContext();
    var next = Substitute.For<RequestDelegate>();
    var middleware = new LoggingMiddleware(next);
    
    await middleware.InvokeAsync(context);
    
    await next.Received(1).Invoke(context);
}
```

## What is response caching middleware?
**Answer:** UseResponseCaching caches HTTP responses based on cache headers, reducing server load for frequently requested resources.
