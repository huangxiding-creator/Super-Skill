---
name: real-time-websockets
description: Real-time communication patterns with WebSockets, Server-Sent Events (SSE), and real-time data synchronization. Covers Socket.io, WebSocket API, and live update strategies.
tags: [websocket, real-time, sse, socket-io, live-updates]
version: 1.0.0
source: Based on Socket.io, ws, Server-Sent Events best practices
integrated-with: super-skill v3.7+
---

# Real-Time & WebSockets Skill

This skill provides comprehensive real-time communication patterns using WebSockets, Server-Sent Events (SSE), and live data synchronization strategies.

## Real-Time Options

```
┌─────────────────────────────────────────────────────────────────┐
│                  REAL-TIME COMMUNICATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WEBSOCKETS                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Full-duplex       • Low latency    • Binary support   │    │
│  │ • Socket.io         • ws             • native WebSocket │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  SERVER-SENT EVENTS (SSE)                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Server to client   • Auto-reconnect   • Simple HTTP   │    │
│  │ • EventSource API    • Text only        • HTTP/2 ready  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  POLLING (Fallback)                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Simple            • HTTP only       • Higher latency  │    │
│  │ • Long-polling      • Short-polling   • Easy debugging  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## WebSocket Implementation

### Server with Socket.io

```typescript
import { Server } from 'socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import Redis from 'ioredis';

// Initialize Socket.io server
const io = new Server(httpServer, {
  cors: {
    origin: process.env.CLIENT_URL,
    methods: ['GET', 'POST']
  },
  // Redis adapter for horizontal scaling
  adapter: createAdapter(
    new Redis(process.env.REDIS_URL),
    new Redis(process.env.REDIS_URL)
  )
});

// Middleware for authentication
io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;

  try {
    const user = await verifyToken(token);
    socket.data.user = user;
    next();
  } catch (error) {
    next(new Error('Authentication failed'));
  }
});

// Connection handling
io.on('connection', (socket) => {
  const user = socket.data.user;
  console.log(`User ${user.id} connected`);

  // Join user's personal room
  socket.join(`user:${user.id}`);

  // Handle events
  socket.on('message', (data) => {
    handleMessage(socket, data);
  });

  socket.on('typing', (data) => {
    handleTyping(socket, data);
  });

  socket.on('disconnect', (reason) => {
    console.log(`User ${user.id} disconnected: ${reason}`);
  });
});

// Event handlers
async function handleMessage(socket: Socket, data: MessageInput) {
  const message = await saveMessage({
    ...data,
    userId: socket.data.user.id
  });

  // Emit to all users in the conversation
  io.to(`conversation:${data.conversationId}`).emit('message', message);
}

function handleTyping(socket: Socket, data: TypingInput) {
  socket.to(`conversation:${data.conversationId}`).emit('typing', {
    userId: socket.data.user.id,
    isTyping: data.isTyping
  });
}
```

### Client with Socket.io

```typescript
import { io, Socket } from 'socket.io-client';

class SocketManager {
  private socket: Socket;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(private url: string) {
    this.socket = io(url, {
      auth: { token: getAuthToken() },
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    this.socket.on('connect', () => {
      console.log('Connected to server');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('Disconnected:', reason);
      if (reason === 'io server disconnect') {
        // Server disconnected, need to reconnect manually
        this.socket.connect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        this.socket.disconnect();
      }
    });

    this.socket.on('message', (message) => {
      onMessageReceived(message);
    });

    this.socket.on('typing', (data) => {
      onTypingIndicator(data);
    });
  }

  connect() {
    this.socket.connect();
  }

  disconnect() {
    this.socket.disconnect();
  }

  // Join a room
  joinConversation(conversationId: string) {
    this.socket.emit('join', { conversationId });
  }

  // Leave a room
  leaveConversation(conversationId: string) {
    this.socket.emit('leave', { conversationId });
  }

  // Send message
  sendMessage(conversationId: string, content: string) {
    this.socket.emit('message', {
      conversationId,
      content,
      timestamp: Date.now()
    });
  }

  // Typing indicator
  setTyping(conversationId: string, isTyping: boolean) {
    this.socket.emit('typing', { conversationId, isTyping });
  }

  // Subscribe to events
  on<T>(event: string, callback: (data: T) => void) {
    this.socket.on(event, callback);
    return () => this.socket.off(event, callback);
  }
}

// React hook for Socket.io
function useSocket(url: string) {
  const [socket, setSocket] = useState<SocketManager | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const manager = new SocketManager(url);

    manager.on('connect', () => setIsConnected(true));
    manager.on('disconnect', () => setIsConnected(false));

    manager.connect();
    setSocket(manager);

    return () => manager.disconnect();
  }, [url]);

  return { socket, isConnected };
}
```

## Server-Sent Events (SSE)

### Server Implementation

```typescript
import express from 'express';

const app = express();

// SSE endpoint
app.get('/events', (req, res) => {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering

  // Send initial connection message
  res.write(`data: ${JSON.stringify({ type: 'connected' })}\n\n`);

  // Heartbeat to keep connection alive
  const heartbeat = setInterval(() => {
    res.write(':heartbeat\n\n');
  }, 15000);

  // Subscribe to events
  const unsubscribe = eventBus.subscribe((event) => {
    res.write(`event: ${event.type}\n`);
    res.write(`data: ${JSON.stringify(event.data)}\n\n`);
  });

  // Handle client disconnect
  req.on('close', () => {
    clearInterval(heartbeat);
    unsubscribe();
  });
});

// Broadcast to all connected clients
class SSEBroadcaster {
  private clients: Set<express.Response> = new Set();

  addClient(res: express.Response) {
    this.clients.add(res);
    res.on('close', () => this.clients.delete(res));
  }

  broadcast(event: string, data: any) {
    const message = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
    this.clients.forEach((client) => {
      client.write(message);
    });
  }

  broadcastToUser(userId: string, event: string, data: any) {
    // Filter clients by user ID if tracking
    const message = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
    // Implementation depends on client tracking
  }
}

const broadcaster = new SSEBroadcaster();

app.get('/events', (req, res) => {
  broadcaster.addClient(res);
  // ... rest of SSE setup
});
```

### Client Implementation

```typescript
class SSEClient {
  private eventSource: EventSource | null = null;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;

  constructor(private url: string) {}

  connect() {
    this.eventSource = new EventSource(this.url);

    this.eventSource.onopen = () => {
      console.log('SSE connected');
      this.reconnectDelay = 1000; // Reset delay
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      this.reconnect();
    };

    // Listen for specific event types
    this.eventSource.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);
      this.onMessage(data);
    });

    this.eventSource.addEventListener('notification', (event) => {
      const data = JSON.parse(event.data);
      this.onNotification(data);
    });

    this.eventSource.addEventListener('update', (event) => {
      const data = JSON.parse(event.data);
      this.onUpdate(data);
    });
  }

  private reconnect() {
    this.eventSource?.close();
    this.eventSource = null;

    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(
      this.reconnectDelay * 2,
      this.maxReconnectDelay
    );
  }

  disconnect() {
    this.eventSource?.close();
    this.eventSource = null;
  }

  private onMessage(data: any) {
    // Handle message
  }

  private onNotification(data: any) {
    // Handle notification
  }

  private onUpdate(data: any) {
    // Handle update
  }
}

// React hook for SSE
function useSSE<T>(url: string, eventType: string) {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(url);

    eventSource.onopen = () => setIsConnected(true);
    eventSource.onerror = () => setIsConnected(false);

    eventSource.addEventListener(eventType, (event) => {
      setData(JSON.parse(event.data));
    });

    return () => eventSource.close();
  }, [url, eventType]);

  return { data, isConnected };
}
```

## Real-Time Data Synchronization

### Optimistic Updates

```typescript
class RealtimeSync {
  private socket: Socket;
  private pendingUpdates: Map<string, PendingUpdate> = new Map();

  async updateDocument(documentId: string, changes: DocumentChanges) {
    const updateId = generateId();

    // Store pending update
    this.pendingUpdates.set(updateId, {
      documentId,
      changes,
      timestamp: Date.now()
    });

    // Optimistically apply changes locally
    applyChangesLocally(documentId, changes);

    try {
      // Send to server
      this.socket.emit('document:update', {
        updateId,
        documentId,
        changes
      });

      // Wait for acknowledgment
      await this.waitForAck(updateId);

    } catch (error) {
      // Rollback on failure
      rollbackChanges(documentId, changes);
      throw error;
    } finally {
      this.pendingUpdates.delete(updateId);
    }
  }

  private waitForAck(updateId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Update timeout'));
      }, 10000);

      this.socket.once(`ack:${updateId}`, (response) => {
        clearTimeout(timeout);
        if (response.success) {
          resolve();
        } else {
          reject(new Error(response.error));
        }
      });
    });
  }
}
```

### Conflict Resolution

```typescript
interface VersionedDocument {
  id: string;
  version: number;
  content: any;
  lastModifiedBy: string;
  lastModifiedAt: number;
}

class ConflictResolver {
  // Last-write-wins strategy
  resolveLastWriteWins(local: VersionedDocument, remote: VersionedDocument): VersionedDocument {
    return remote.lastModifiedAt > local.lastModifiedAt ? remote : local;
  }

  // Operational transformation
  transformOperations(
    localOps: Operation[],
    remoteOps: Operation[],
    baseVersion: number
  ): Operation[] {
    const transformed: Operation[] = [];

    for (const localOp of localOps) {
      let transformedOp = { ...localOp };

      for (const remoteOp of remoteOps) {
        transformedOp = this.transform(transformedOp, remoteOp);
      }

      transformed.push(transformedOp);
    }

    return transformed;
  }

  private transform(op1: Operation, op2: Operation): Operation {
    // Transform op1 against op2
    if (op1.type === 'insert' && op2.type === 'insert') {
      if (op2.position <= op1.position) {
        return { ...op1, position: op1.position + op2.text.length };
      }
    }
    // ... other transformation rules
    return op1;
  }

  // CRDT-based merge
  mergeWithCRDT(local: VersionedDocument, remote: VersionedDocument): VersionedDocument {
    // Use CRDT merge strategy (e.g., LWW-Element-Set)
    return {
      ...local,
      ...remote,
      version: Math.max(local.version, remote.version) + 1
    };
  }
}
```

## Integration with Super-Skill

### Phase Integration

```yaml
realtime_phase_mapping:
  phase_5_design:
    outputs:
      - real_time_architecture
      - event_flow_diagram

  phase_8_development:
    actions:
      - implement_websocket_server
      - create_client_connection_manager
      - setup_event_handlers

  phase_9_qa:
    actions:
      - test_reconnection_logic
      - load_test_connections
      - test_conflict_resolution
```

## Best Practices Checklist

### WebSocket
- [ ] Authentication on connect
- [ ] Heartbeat/ping-pong
- [ ] Reconnection logic
- [ ] Message acknowledgment

### SSE
- [ ] Proper headers set
- [ ] Heartbeat messages
- [ ] Event type filtering
- [ ] Reconnection handling

### Data Sync
- [ ] Optimistic updates
- [ ] Conflict resolution
- [ ] Offline support
- [ ] Version tracking

## Deliverables

- WebSocket server setup
- Client connection manager
- Event handlers
- Sync strategies

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Socket.io Documentation](https://socket.io/docs/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Operational Transformation](https://en.wikipedia.org/wiki/Operational_transformation)
