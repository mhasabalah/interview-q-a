---
title: Real-Time Communication
aliases: [Real-Time Communication, SignalR]
tags: [signalr, realtime, interview]
order: 13
---

# Real-Time Communication Interview Questions & Answers

> [!info]+ Related Notes
> [[11-Module-Communication|Module Communication]] · [[16-System-Design|System Design]]

## What is Real-Time Communication?
**Answer:** Real-time communication enables instant bidirectional data exchange between clients and servers with minimal latency, used for chat, notifications, live updates, and collaborative applications.

## What is SignalR?
**Answer:** SignalR is an ASP.NET Core library for adding real-time web functionality. It automatically manages connections and chooses the best transport method (WebSockets, Server-Sent Events, Long Polling).

## What are the main components of SignalR?
**Answer:**
- **Hub:** Server-side class handling client connections and messages
- **HubConnection:** Client-side connection to the hub
- **Transport:** Communication protocol (WebSockets, SSE, Long Polling)

## How do you create a SignalR Hub?
**Answer:**
```csharp
public class ChatHub : Hub
{
    public async Task SendMessage(string user, string message)
    {
        await Clients.All.SendAsync("ReceiveMessage", user, message);
    }

    public override async Task OnConnectedAsync()
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, "ChatRoom");
        await base.OnConnectedAsync();
    }
}
```

## How do you configure SignalR in ASP.NET Core?
**Answer:**
```csharp
// Program.cs
builder.Services.AddSignalR();

app.MapHub<ChatHub>("/chatHub");
```

## What are the different transport methods in SignalR?
**Answer:**
- **WebSockets:** Full-duplex, lowest latency (preferred)
- **Server-Sent Events (SSE):** Server-to-client streaming
- **Long Polling:** Fallback for older browsers

## How do you connect to SignalR from a client?
**Answer:**
```javascript
const connection = new signalR.HubConnectionBuilder()
    .withUrl("/chatHub")
    .build();

connection.on("ReceiveMessage", (user, message) => {
    console.log(`${user}: ${message}`);
});

await connection.start();
await connection.invoke("SendMessage", "John", "Hello!");
```

## What is the difference between Clients.All, Clients.Caller, and Clients.Others?
**Answer:**
- **Clients.All:** Sends to all connected clients
- **Clients.Caller:** Sends only to the calling client
- **Clients.Others:** Sends to all except the caller

## How do you implement groups in SignalR?
**Answer:**
```csharp
public class ChatHub : Hub
{
    public async Task JoinRoom(string roomName)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, roomName);
        await Clients.Group(roomName).SendAsync("UserJoined", Context.ConnectionId);
    }

    public async Task SendToRoom(string roomName, string message)
    {
        await Clients.Group(roomName).SendAsync("ReceiveMessage", message);
    }

    public async Task LeaveRoom(string roomName)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, roomName);
    }
}
```

## What is strongly-typed SignalR Hub?
**Answer:**
```csharp
public interface IChatClient
{
    Task ReceiveMessage(string user, string message);
}

public class ChatHub : Hub<IChatClient>
{
    public async Task SendMessage(string user, string message)
    {
        await Clients.All.ReceiveMessage(user, message);
    }
}
```

## How do you handle authentication in SignalR?
**Answer:**
```csharp
[Authorize]
public class ChatHub : Hub
{
    public async Task SendMessage(string message)
    {
        var username = Context.User.Identity.Name;
        await Clients.All.SendAsync("ReceiveMessage", username, message);
    }
}

// Client
const connection = new signalR.HubConnectionBuilder()
    .withUrl("/chatHub", { accessTokenFactory: () => getAccessToken() })
    .build();
```

## What is connection lifetime management?
**Answer:** SignalR automatically manages connections with reconnection logic. Handle `OnConnectedAsync` and `OnDisconnectedAsync` for connection tracking:
```csharp
public override async Task OnDisconnectedAsync(Exception exception)
{
    await Clients.Others.SendAsync("UserDisconnected", Context.ConnectionId);
    await base.OnDisconnectedAsync(exception);
}
```

## How do you scale SignalR?
**Answer:** Use a backplane (Redis, Azure SignalR Service, SQL Server) to synchronize messages across multiple servers:
```csharp
services.AddSignalR().AddStackExchangeRedis("localhost:6379");
```

## What is Azure SignalR Service?
**Answer:** Azure SignalR Service is a fully managed service for hosting SignalR applications with automatic scaling, persistent connections, and global distribution.

## How do you implement automatic reconnection?
**Answer:**
```javascript
const connection = new signalR.HubConnectionBuilder()
    .withUrl("/chatHub")
    .withAutomaticReconnect([0, 2000, 10000, 30000])
    .build();

connection.onreconnecting(error => {
    console.log("Reconnecting...");
});

connection.onreconnected(connectionId => {
    console.log("Reconnected!");
});
```

## What is the difference between SignalR and WebSockets?
**Answer:**
- **WebSockets:** Low-level protocol requiring manual connection management
- **SignalR:** High-level abstraction with automatic transport selection, reconnection, and fallback

## How do you send messages to specific users?
**Answer:**
```csharp
public async Task SendPrivateMessage(string userId, string message)
{
    await Clients.User(userId).SendAsync("ReceivePrivateMessage", message);
}

// Configure User ID provider
services.AddSingleton<IUserIdProvider, EmailBasedUserIdProvider>();

public class EmailBasedUserIdProvider : IUserIdProvider
{
    public string GetUserId(HubConnectionContext connection)
    {
        return connection.User?.FindFirst(ClaimTypes.Email)?.Value;
    }
}
```

## What is streaming in SignalR?
**Answer:** SignalR supports server-to-client and client-to-server streaming:
```csharp
public async IAsyncEnumerable<int> StreamCounter(int count)
{
    for (int i = 0; i < count; i++)
    {
        await Task.Delay(1000);
        yield return i;
    }
}

// Client
connection.stream("StreamCounter", 10)
    .subscribe({
        next: (item) => console.log(item),
        complete: () => console.log("Complete")
    });
```

## How do you handle errors in SignalR?
**Answer:**
```csharp
public class ChatHub : Hub
{
    public async Task SendMessage(string message)
    {
        try
        {
            await Clients.All.SendAsync("ReceiveMessage", message);
        }
        catch (Exception ex)
        {
            await Clients.Caller.SendAsync("Error", ex.Message);
        }
    }
}

// Client
connection.on("Error", (error) => {
    console.error(error);
});
```

## What is message packing in SignalR?
**Answer:** SignalR supports JSON (default) and MessagePack protocols. MessagePack is binary, faster, and smaller:
```csharp
services.AddSignalR().AddMessagePackProtocol();

// Client
const connection = new signalR.HubConnectionBuilder()
    .withUrl("/chatHub")
    .withHubProtocol(new signalR.protocols.msgpack.MessagePackHubProtocol())
    .build();
```

## How do you implement presence tracking?
**Answer:**
```csharp
public class PresenceTracker
{
    private static readonly Dictionary<string, List<string>> OnlineUsers = new();

    public Task UserConnected(string username, string connectionId)
    {
        lock (OnlineUsers)
        {
            if (!OnlineUsers.ContainsKey(username))
                OnlineUsers[username] = new List<string>();
            
            OnlineUsers[username].Add(connectionId);
        }
        return Task.CompletedTask;
    }

    public Task UserDisconnected(string username, string connectionId)
    {
        lock (OnlineUsers)
        {
            if (OnlineUsers.ContainsKey(username))
            {
                OnlineUsers[username].Remove(connectionId);
                if (OnlineUsers[username].Count == 0)
                    OnlineUsers.Remove(username);
            }
        }
        return Task.CompletedTask;
    }
}
```

## What are the limitations of SignalR?
**Answer:**
- Connection limits on single server (use Azure SignalR Service or backplane)
- Stateful connections require sticky sessions without backplane
- WebSocket support required for best performance
- Higher resource usage than traditional HTTP

## How do you test SignalR Hubs?
**Answer:**
```csharp
[Test]
public async Task SendMessage_ShouldBroadcastToAll()
{
    var mockClients = Substitute.For<IHubCallerClients<IChatClient>>();
    var mockAll = Substitute.For<IChatClient>();
    mockClients.All.Returns(mockAll);

    var hub = new ChatHub { Clients = mockClients };

    await hub.SendMessage("Hello");

    await mockAll.Received(1).ReceiveMessage("Hello");
}
```

## What is the HubContext?
**Answer:** HubContext sends messages to clients from outside a Hub (controllers, background services):
```csharp
public class NotificationService
{
    private readonly IHubContext<NotificationHub> _hubContext;

    public NotificationService(IHubContext<NotificationHub> hubContext)
    {
        _hubContext = hubContext;
    }

    public async Task SendNotification(string userId, string message)
    {
        await _hubContext.Clients.User(userId)
            .SendAsync("ReceiveNotification", message);
    }
}
```

## How do you implement connection throttling?
**Answer:**
```csharp
services.AddSignalR(options =>
{
    options.EnableDetailedErrors = true;
    options.ClientTimeoutInterval = TimeSpan.FromSeconds(60);
    options.KeepAliveInterval = TimeSpan.FromSeconds(30);
    options.MaximumReceiveMessageSize = 32 * 1024; // 32 KB
});
```
