# data-patterns — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

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
