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

## GraphQL Patterns

### Schema Design

```graphql
type User {
  id: ID!
  email: String!
  name: String!
  avatar: String
  createdAt: DateTime!
  updatedAt: DateTime!

  # Relationships
  posts(first: Int, after: String): PostConnection!
  comments(first: Int, after: String): CommentConnection!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  tags: [Tag!]!
  publishedAt: DateTime

  # Computed fields
  commentCount: Int!
  isPublished: Boolean!
}

# Relay-style connections
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Inputs
input CreateUserInput {
  email: String!
  name: String!
  password: String!
}

input UpdateUserInput {
  email: String
  name: String
}

# Mutations with payloads
type CreateUserPayload {
  user: User
  errors: [ValidationError!]
}

type ValidationError {
  field: String!
  message: String!
}
```

### Query Patterns

```graphql
# Query with fragments
query GetUserWithPosts($userId: ID!, $first: Int!) {
  user(id: $userId) {
    ...UserFields
    posts(first: $first) {
      ...PostConnectionFields
    }
  }
}

fragment UserFields on User {
  id
  email
  name
  avatar
}

fragment PostConnectionFields on PostConnection {
  edges {
    node {
      id
      title
      publishedAt
    }
    cursor
  }
  pageInfo {
    hasNextPage
    endCursor
  }
  totalCount
}

# Mutation pattern
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    post {
      id
      title
      content
    }
    errors {
      field
      message
    }
  }
}
```

### Resolver Patterns

```typescript
// DataLoader for N+1 prevention
import DataLoader from 'dataloader';

const userLoader = new DataLoader(async (ids: string[]) => {
  const users = await db.user.findMany({ where: { id: { in: ids } } });
  const userMap = new Map(users.map(u => [u.id, u]));
  return ids.map(id => userMap.get(id) || null);
});

const resolvers = {
  Query: {
    user: async (_, { id }, { loaders }) => {
      return loaders.user.load(id);
    },
    users: async (_, { first, after }, { db }) => {
      const users = await db.user.findMany({
        take: first + 1,
        cursor: after ? { id: after } : undefined,
        orderBy: { createdAt: 'desc' }
      });

      return {
        edges: users.slice(0, first).map(user => ({
          node: user,
          cursor: user.id
        })),
        pageInfo: {
          hasNextPage: users.length > first,
          endCursor: users[users.length - 1]?.id
        }
      };
    }
  },

  User: {
    // Batch load posts
    posts: async (user, { first }, { loaders }) => {
      return loaders.userPosts.load(user.id);
    }
  },

  Mutation: {
    createPost: async (_, { input }, { db, user }) => {
      // Validate
      const errors = validateCreatePost(input);
      if (errors.length > 0) {
        return { errors, post: null };
      }

      // Create
      const post = await db.post.create({
        data: {
          ...input,
          authorId: user.id
        }
      });

      return { post, errors: [] };
    }
  }
};
```

## Authentication & Authorization

### Authentication Patterns

```typescript
// JWT Authentication
interface JWTPayload {
  sub: string;      // User ID
  iat: number;      // Issued at
  exp: number;      // Expiration
  role: string;     // User role
  permissions: string[];
}

// Middleware
async function authenticate(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const token = extractToken(req);

  if (!token) {
    throw new UnauthorizedError('No token provided');
  }

  try {
    const payload = await verifyToken(token);
    req.user = payload;
    next();
  } catch (error) {
    throw new UnauthorizedError('Invalid token');
  }
}

// API Key Authentication
async function authenticateApiKey(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const apiKey = req.headers['x-api-key'];

  if (!apiKey) {
    throw new UnauthorizedError('API key required');
  }

  const key = await validateApiKey(apiKey as string);
  if (!key || key.expiresAt < new Date()) {
    throw new UnauthorizedError('Invalid or expired API key');
  }

  req.apiKey = key;
  next();
}
```

### Authorization Patterns

```typescript
// Role-Based Access Control (RBAC)
const ROLES = {
  ADMIN: ['read', 'write', 'delete', 'manage_users'],
  EDITOR: ['read', 'write'],
  VIEWER: ['read']
};

function hasPermission(user: User, permission: string): boolean {
  const rolePermissions = ROLES[user.role] || [];
  return rolePermissions.includes(permission);
}

// Resource-Based Access Control (ReBAC)
async function canAccessResource(
  user: User,
  resource: Resource,
  action: string
): Promise<boolean> {
  // Owner can do anything
  if (resource.ownerId === user.id) {
    return true;
  }

  // Check explicit permissions
  const permission = await db.permission.findFirst({
    where: {
      userId: user.id,
      resourceId: resource.id,
      actions: { has: action }
    }
  });

  return !!permission;
}

// Middleware
function authorize(permission: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!hasPermission(req.user, permission)) {
      throw new ForbiddenError('Insufficient permissions');
    }
    next();
  };
}

// Usage
app.delete('/users/:id',
  authenticate,
  authorize('delete_user'),
  deleteUser
);
```

## API Versioning

```typescript
// URL Versioning
app.use('/v1', v1Routes);
app.use('/v2', v2Routes);

// Header Versioning
app.use((req, res, next) => {
  const version = req.headers['accept-version'] || '1';
  req.apiVersion = version;
  next();
});

// Content Negotiation
app.use((req, res, next) => {
  const accept = req.headers.accept;
  if (accept?.includes('application/vnd.api+json;version=2')) {
    req.apiVersion = '2';
  } else {
    req.apiVersion = '1';
  }
  next();
});

// Deprecation headers
app.get('/v1/legacy', (req, res) => {
  res.setHeader('Deprecation', 'true');
  res.setHeader('Sunset', 'Sat, 01 Jan 2027 00:00:00 GMT');
  res.setHeader('Link', '</v2/endpoint>; rel="successor-version"');
  // ... handler
});
```

## Rate Limiting

```typescript
import rateLimit from 'express-rate-limit';

// Basic rate limiter
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per window
  message: {
    success: false,
    error: {
      code: 'RATE_LIMIT_EXCEEDED',
      message: 'Too many requests, please try again later'
    }
  },
  headers: true // Send rate limit info in headers
});

// Tiered rate limiting
const tieredLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: (req) => {
    switch (req.user?.tier) {
      case 'enterprise': return 1000;
      case 'pro': return 500;
      case 'free': return 100;
      default: return 50;
    }
  }
});

app.use('/api', limiter);
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

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [OpenAPI Specification](https://swagger.io/specification/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [REST API Tutorial](https://restfulapi.net/)
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)
