---
name: api-patterns
description: REST and GraphQL API design patterns, implementation best practices, and integration strategies. Covers endpoint design, authentication, pagination, error handling, and API versioning.
tags: [api, rest, graphql, endpoints, authentication, versioning]
version: 1.0.0
source: Based on industry best practices, OpenAPI specification, GraphQL best practices
integrated-with: super-skill v3.7+
---
# API Patterns Skill

This skill provides comprehensive API design patterns for REST and GraphQL APIs, covering endpoint design, authentication, pagination, error handling, and versioning strategies.

## API Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     API ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LAYER 1: API GATEWAY                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Rate Limiting    • Authentication    • Request Router │    │
│  │ • Load Balancing   • Caching           • Logging        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  LAYER 2: API INTERFACE                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • REST Endpoints   • GraphQL Schema   • WebSocket       │    │
│  │ • Request/Response • Serialization    • Content Negot.  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  LAYER 3: BUSINESS LOGIC                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Validation       • Authorization     • Processing     │    │
│  │ • Orchestration    • Events            • Transactions   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  LAYER 4: DATA ACCESS                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Repository       • ORM              • Query Builder   │    │
│  │ • Caching          • Connections      • Migrations      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## REST API Design

### Resource Naming

```
# Good: Nouns, plural, hierarchical
GET    /users                    # List users
GET    /users/{id}               # Get user
POST   /users                    # Create user
PUT    /users/{id}               # Replace user
PATCH  /users/{id}               # Update user
DELETE /users/{id}               # Delete user

GET    /users/{id}/orders        # User's orders
POST   /users/{id}/orders        # Create order for user
GET    /orders/{orderId}/items   # Order items

# Bad: Verbs, singular, inconsistent
GET    /getUsers
POST   /user/create
DELETE /deleteUser/{id}
GET    /user_orders
```

### Request/Response Patterns

```typescript
// Standard response wrapper
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  meta?: ResponseMeta;
}

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

interface ResponseMeta {
  timestamp: string;
  requestId: string;
  pagination?: PaginationMeta;
}

// Success response
{
  "success": true,
  "data": { "id": "123", "name": "John" },
  "meta": {
    "timestamp": "2026-03-02T12:00:00Z",
    "requestId": "req_abc123"
  }
}

// Error response
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["Invalid email format"],
      "age": ["Must be a positive number"]
    }
  },
  "meta": {
    "timestamp": "2026-03-02T12:00:00Z",
    "requestId": "req_abc123"
  }
}
```

### Pagination

```typescript
// Cursor-based pagination (recommended)
interface CursorPagination {
  cursor?: string;  // Opaque cursor
  limit: number;    // Items per page
  direction?: 'forward' | 'backward';
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    hasNext: boolean;
    hasPrevious: boolean;
    nextCursor?: string;
    previousCursor?: string;
    limit: number;
  };
}

// Implementation
async function getPaginatedUsers(
  pagination: CursorPagination
): Promise<PaginatedResponse<User>> {
  const { cursor, limit = 20, direction = 'forward' } = pagination;

  const query = db.user.findMany({
    take: limit + 1, // Get one extra to check hasNext
    orderBy: { createdAt: 'desc' },
    where: cursor ? {
      createdAt: direction === 'forward'
        ? { lt: decodeCursor(cursor) }
        : { gt: decodeCursor(cursor) }
    } : undefined
  });

  const users = await query;
  const hasNext = users.length > limit;

  return {
    data: users.slice(0, limit),
    pagination: {
      hasNext,
      hasPrevious: !!cursor,
      nextCursor: hasNext ? encodeCursor(users[limit - 1].createdAt) : undefined,
      previousCursor: cursor ? encodeCursor(users[0].createdAt) : undefined,
      limit
    }
  };
}

// Offset-based pagination (simpler, use for small datasets)
interface OffsetPagination {
  page: number;      // Current page (1-based)
  pageSize: number;  // Items per page
}

interface OffsetResponse<T> extends PaginatedResponse<T> {
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
    totalItems: number;
  };
}
```

### Filtering & Sorting

```typescript
// Query parameter conventions
interface QueryParams {
  // Filtering
  filter?: {
    field: string;
    operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'like';
    value: any;
  };

  // Sorting
  sort?: string;   // e.g., "name,-createdAt" (asc, desc)
  search?: string; // Full-text search
}

// Example URLs
// GET /users?filter[status]=active&filter[age][gte]=18
// GET /users?sort=name,-createdAt
// GET /users?search=john

// Implementation
function parseQueryParams(query: Record<string, any>): ParsedQuery {
  const filters: Filter[] = [];
  const sorts: Sort[] = [];

  // Parse filters
  for (const [key, value] of Object.entries(query)) {
    if (key.startsWith('filter[')) {
      const field = key.match(/filter\[(.+)\]/)?.[1];
      if (field) {
        filters.push({ field, operator: 'eq', value });
      }
    }
  }

  // Parse sort
  if (query.sort) {
    const sortFields = query.sort.split(',');
    for (const field of sortFields) {
      const desc = field.startsWith('-');
      sorts.push({
        field: desc ? field.slice(1) : field,
        direction: desc ? 'desc' : 'asc'
      });
    }
  }

  return { filters, sorts, search: query.search };
}
```

## Integration with Super-Skill

### Phase Integration

```yaml
api_phase_mapping:
  phase_5_design:
    outputs:
      - OpenAPI specification
      - GraphQL schema
      - API documentation

  phase_8_development:
    actions:
      - implement_endpoints
      - add_authentication
      - implement_rate_limiting
      - add_error_handling

  phase_9_qa:
    actions:
      - api_contract_testing
      - load_testing
      - security_testing
```

## Best Practices Checklist

### Design
- [ ] Resources named consistently (nouns, plural)
- [ ] HTTP methods used correctly
- [ ] Status codes used appropriately
- [ ] Versioning strategy defined

### Security
- [ ] Authentication implemented
- [ ] Authorization enforced
- [ ] Rate limiting configured
- [ ] Input validation in place

### Performance
- [ ] Pagination implemented
- [ ] Caching configured
- [ ] N+1 queries prevented
- [ ] Compression enabled

### Documentation
- [ ] OpenAPI spec up to date
- [ ] Examples provided
- [ ] Error codes documented
- [ ] Authentication documented

## Deliverables

- API design document
- OpenAPI specification
- GraphQL schema
- Authentication configuration
- Rate limiting setup

---

## Detail Reference

Loaded on demand from [references/details.md](references/details.md): `GraphQL Patterns`, `Authentication & Authorization`, `API Versioning`, `Rate Limiting`, `Version History`, `References`.
