---
name: data-patterns
description: Database design patterns, data modeling, and query optimization for SQL and NoSQL databases. Covers normalization, indexing strategies, migrations, and ORMs.
tags: [database, data-modeling, sql, nosql, orm, migrations]
version: 1.0.0
source: Based on PostgreSQL, MongoDB, Prisma best practices
integrated-with: super-skill v3.7+
---

# Data Patterns Skill

This skill provides comprehensive database design patterns, data modeling strategies, and query optimization techniques for both SQL and NoSQL databases.

## Database Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RELATIONAL (SQL)                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • PostgreSQL    • MySQL    • SQLite    • SQL Server     │    │
│  │ • ACID transactions   • Complex queries   • Joins       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  DOCUMENT (NoSQL)                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • MongoDB    • CouchDB    • DynamoDB                    │    │
│  │ • Flexible schema   • Horizontal scaling   • JSON       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  KEY-VALUE / CACHE                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Redis    • Memcached    • DynamoDB                    │    │
│  │ • Fast lookups   • Session storage   • Caching          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  GRAPH                                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Neo4j    • Amazon Neptune    • ArangoDB               │    │
│  │ • Relationships   • Social networks   • Recommendations │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Relational Database Patterns

### Schema Design

```sql
-- Normalized schema (3NF)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  status VARCHAR(50) DEFAULT 'pending',
  total DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id),
  quantity INT NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  UNIQUE(order_id, product_id)
);

-- Indexes for performance
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Partial index
CREATE INDEX idx_orders_pending ON orders(created_at)
WHERE status = 'pending';

-- Full-text search
CREATE INDEX idx_users_search ON users
USING GIN(to_tsvector('english', name || ' ' || email));
```

### Query Optimization

```sql
-- Analyze query plan
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2025-01-01'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5;

-- Optimized with CTE
WITH active_users AS (
  SELECT id, name
  FROM users
  WHERE created_at > '2025-01-01'
),
user_orders AS (
  SELECT user_id, COUNT(*) as order_count
  FROM orders
  GROUP BY user_id
  HAVING COUNT(*) > 5
)
SELECT au.name, uo.order_count
FROM active_users au
JOIN user_orders uo ON au.id = uo.user_id;

-- Window functions for analytics
SELECT
  user_id,
  order_date,
  total,
  SUM(total) OVER (PARTITION BY user_id ORDER BY order_date) as running_total,
  RANK() OVER (PARTITION BY user_id ORDER BY total DESC) as order_rank
FROM orders;
```

### Prisma Schema

```prisma
// schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id        String   @id @default(uuid())
  email     String   @unique
  name      String?
  avatar    String?
  role      Role     @default(USER)
  orders    Order[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([email])
  @@map("users")
}

model Order {
  id        String      @id @default(uuid())
  userId    String
  user      User        @relation(fields: [userId], references: [id])
  items     OrderItem[]
  status    OrderStatus @default(PENDING)
  total     Decimal     @db.Decimal(10, 2)
  createdAt DateTime    @default(now())

  @@index([userId])
  @@index([status])
  @@map("orders")
}

model OrderItem {
  id        String  @id @default(uuid())
  orderId   String
  order     Order   @relation(fields: [orderId], references: [id], onDelete: Cascade)
  productId String
  product   Product @relation(fields: [productId], references: [id])
  quantity  Int
  price     Decimal @db.Decimal(10, 2)

  @@unique([orderId, productId])
  @@map("order_items")
}

enum Role {
  USER
  ADMIN
}

enum OrderStatus {
  PENDING
  PROCESSING
  SHIPPED
  DELIVERED
  CANCELLED
}
```

## Document Database Patterns

### MongoDB Schema

```javascript
// User document with embedded orders (denormalized for read performance)
{
  _id: ObjectId("..."),
  email: "user@example.com",
  name: "John Doe",
  profile: {
    avatar: "https://...",
    bio: "..."
  },
  preferences: {
    theme: "dark",
    notifications: true
  },
  orderSummary: {
    totalOrders: 15,
    totalSpent: 1250.00,
    lastOrderDate: ISODate("2025-02-15")
  },
  createdAt: ISODate("2024-01-01"),
  updatedAt: ISODate("2026-03-02")
}

// Separate orders collection with references
{
  _id: ObjectId("..."),
  userId: ObjectId("..."),  // Reference to user
  items: [
    {
      productId: ObjectId("..."),
      name: "Product Name",  // Denormalized for display
      quantity: 2,
      price: 49.99
    }
  ],
  status: "shipped",
  shipping: {
    address: { ... },
    method: "express"
  },
  createdAt: ISODate("2025-02-15")
}

// Indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ "preferences.theme": 1 });
db.orders.createIndex({ userId: 1, createdAt: -1 });
db.orders.createIndex({ status: 1 });
```

### Aggregation Patterns

```javascript
// User order statistics
db.orders.aggregate([
  { $match: { status: "delivered" } },
  { $group: {
    _id: "$userId",
    totalOrders: { $sum: 1 },
    totalSpent: { $sum: "$total" },
    avgOrderValue: { $avg: "$total" }
  }},
  { $lookup: {
    from: "users",
    localField: "_id",
    foreignField: "_id",
    as: "user"
  }},
  { $unwind: "$user" },
  { $project: {
    userId: "$_id",
    userName: "$user.name",
    totalOrders: 1,
    totalSpent: 1,
    avgOrderValue: 1
  }}
]);

// Time-series analysis
db.orders.aggregate([
  { $match: {
    createdAt: { $gte: new Date("2025-01-01") }
  }},
  { $group: {
    _id: {
      year: { $year: "$createdAt" },
      month: { $month: "$createdAt" },
      day: { $dayOfMonth: "$createdAt" }
    },
    dailyRevenue: { $sum: "$total" },
    orderCount: { $sum: 1 }
  }},
  { $sort: { "_id.year": 1, "_id.month": 1, "_id.day": 1 } }
]);
```

## Migration Patterns

### Prisma Migrations

```bash
# Create migration
npx prisma migrate dev --name add_user_preferences

# Deploy migrations
npx prisma migrate deploy

# Reset database
npx prisma migrate reset
```

### Custom Migration

```sql
-- migrations/001_add_soft_delete.sql
BEGIN;

ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE orders ADD COLUMN deleted_at TIMESTAMP;

CREATE INDEX idx_users_not_deleted ON users(id) WHERE deleted_at IS NULL;
CREATE INDEX idx_orders_not_deleted ON orders(id) WHERE deleted_at IS NULL;

COMMIT;

-- migrations/002_add_audit_log.sql
BEGIN;

CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name VARCHAR(100) NOT NULL,
  record_id UUID NOT NULL,
  action VARCHAR(20) NOT NULL,
  old_data JSONB,
  new_data JSONB,
  user_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);

COMMIT;
```

## Data Access Patterns

### Repository Pattern

```typescript
interface Repository<T, CreateInput, UpdateInput> {
  findById(id: string): Promise<T | null>;
  findMany(filters?: FilterInput): Promise<T[]>;
  create(data: CreateInput): Promise<T>;
  update(id: string, data: UpdateInput): Promise<T>;
  delete(id: string): Promise<void>;
}

class UserRepository implements Repository<User, CreateUserInput, UpdateUserInput> {
  constructor(private db: PrismaClient) {}

  async findById(id: string): Promise<User | null> {
    return this.db.user.findUnique({ where: { id } });
  }

  async findMany(filters?: UserFilters): Promise<User[]> {
    return this.db.user.findMany({
      where: {
        ...(filters?.role && { role: filters.role }),
        ...(filters?.search && {
          OR: [
            { name: { contains: filters.search, mode: 'insensitive' } },
            { email: { contains: filters.search, mode: 'insensitive' } }
          ]
        })
      },
      orderBy: { createdAt: 'desc' }
    });
  }

  async create(data: CreateUserInput): Promise<User> {
    return this.db.user.create({ data });
  }

  async update(id: string, data: UpdateUserInput): Promise<User> {
    return this.db.user.update({ where: { id }, data });
  }

  async delete(id: string): Promise<void> {
    // Soft delete
    await this.db.user.update({
      where: { id },
      data: { deletedAt: new Date() }
    });
  }
}
```

### Unit of Work

```typescript
class UnitOfWork {
  private tx: PrismaClient | Prisma.TransactionClient;
  private committed = false;

  constructor(private db: PrismaClient) {}

  async begin(): Promise<void> {
    this.tx = this.db.$transaction();
  }

  get users(): UserRepository {
    return new UserRepository(this.tx);
  }

  get orders(): OrderRepository {
    return new OrderRepository(this.tx);
  }

  async commit(): Promise<void> {
    if (this.committed) {
      throw new Error('Transaction already committed');
    }
    await this.tx.$commit();
    this.committed = true;
  }

  async rollback(): Promise<void> {
    if (!this.committed) {
      await this.tx.$rollback();
    }
  }
}

// Usage
async function transferOrder(fromUserId: string, toUserId: string, orderId: string) {
  const uow = new UnitOfWork(db);
  await uow.begin();

  try {
    const order = await uow.orders.findById(orderId);
    await uow.orders.update(orderId, { userId: toUserId });
    await uow.users.update(fromUserId, { orderCount: { decrement: 1 } });
    await uow.users.update(toUserId, { orderCount: { increment: 1 } });

    await uow.commit();
  } catch (error) {
    await uow.rollback();
    throw error;
  }
}
```

## CQRS Pattern

```typescript
// Separate read and write models

// Write model (normalized)
interface UserWriteModel {
  id: string;
  email: string;
  name: string;
  role: Role;
}

// Read model (denormalized for queries)
interface UserReadModel {
  id: string;
  email: string;
  name: string;
  role: Role;
  orderCount: number;
  totalSpent: number;
  lastOrderDate: Date | null;
}

// Command handler
class UserCommandHandler {
  async create(command: CreateUserCommand): Promise<string> {
    const user = await this.db.user.create({
      data: { ...command }
    });

    // Update read model
    await this.readDb.userSummary.create({
      data: { id: user.id, email: user.email, name: user.name, orderCount: 0 }
    });

    return user.id;
  }
}

// Query handler
class UserQueryHandler {
  async getUserSummary(id: string): Promise<UserReadModel | null> {
    // Query from optimized read model
    return this.readDb.userSummary.findUnique({ where: { id } });
  }

  async searchUsers(query: string): Promise<UserReadModel[]> {
    return this.readDb.userSummary.findMany({
      where: {
        OR: [
          { name: { contains: query } },
          { email: { contains: query } }
        ]
      }
    });
  }
}
```

## Integration with Super-Skill

### Phase Integration

```yaml
data_phase_mapping:
  phase_5_design:
    outputs:
      - database_schema
      - er_diagram
      - migration_plan

  phase_7_initialization:
    actions:
      - setup_database
      - run_migrations
      - seed_data

  phase_8_development:
    actions:
      - implement_repositories
      - write_queries
      - add_indexes
```

## Best Practices Checklist

### Schema Design
- [ ] Proper normalization
- [ ] Foreign key constraints
- [ ] Appropriate indexes
- [ ] Soft delete strategy

### Query Optimization
- [ ] Query plans analyzed
- [ ] N+1 queries prevented
- [ ] Pagination implemented
- [ ] Caching configured

### Data Integrity
- [ ] Transactions used
- [ ] Constraints defined
- [ ] Validation in place
- [ ] Audit logging enabled

## Deliverables

- Database schema
- Migration scripts
- Repository implementations
- Query optimizations

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Prisma Documentation](https://www.prisma.io/docs/)
- [MongoDB Best Practices](https://www.mongodb.com/docs/manual/core/data-modeling/)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
