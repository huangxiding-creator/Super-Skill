# api-patterns — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

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
