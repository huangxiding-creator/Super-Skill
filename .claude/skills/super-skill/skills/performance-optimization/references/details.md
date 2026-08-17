# performance-optimization — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## Database Optimization

### Indexing Strategy

```sql
-- Primary key index (automatic)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Unique index for email lookups
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Composite index for common queries
CREATE INDEX idx_users_name_created ON users(name, created_at DESC);

-- Partial index for active users
CREATE INDEX idx_users_active ON users(email) WHERE active = true;

-- Full-text search index
CREATE INDEX idx_users_search ON users USING GIN(
  to_tsvector('english', name || ' ' || email)
);

-- Covering index (include columns for index-only scans)
CREATE INDEX idx_users_covering ON users(email) INCLUDE (name, created_at);
```

### Query Optimization

```sql
-- EXPLAIN ANALYZE for query analysis
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2025-01-01'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5
ORDER BY order_count DESC;

-- Optimized query with proper indexing
-- 1. Use INNER JOIN if NULLs not needed
-- 2. Filter early
-- 3. Use covering indexes
SELECT u.name, o.count
FROM users u
INNER JOIN LATERAL (
  SELECT COUNT(*) as count
  FROM orders o
  WHERE o.user_id = u.id
) o ON o.count > 5
WHERE u.created_at > '2025-01-01'
ORDER BY o.count DESC;
```

### N+1 Query Prevention

```typescript
// BAD: N+1 queries
async function getUsersWithOrders(userIds: string[]) {
  const users = await db.user.findMany({
    where: { id: { in: userIds } }
  });

  for (const user of users) {
    user.orders = await db.order.findMany({
      where: { userId: user.id }
    });
  }

  return users;
}

// GOOD: Batch loading with DataLoader
import DataLoader from 'dataloader';

const orderLoader = new DataLoader(async (userIds: string[]) => {
  const orders = await db.order.findMany({
    where: { userId: { in: userIds } }
  });

  // Group by userId
  const orderMap = new Map<string, Order[]>();
  for (const order of orders) {
    const userOrders = orderMap.get(order.userId) || [];
    userOrders.push(order);
    orderMap.set(order.userId, userOrders);
  }

  return userIds.map(id => orderMap.get(id) || []);
});

// GOOD: Prisma include
async function getUsersWithOrdersOptimized(userIds: string[]) {
  return db.user.findMany({
    where: { id: { in: userIds } },
    include: { orders: true }
  });
}
```

## Performance Profiling

### Frontend Profiling

```typescript
import { Profiler, ProfilerOnRenderCallback } from 'react';

const onRenderCallback: ProfilerOnRenderCallback = (
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime
) => {
  console.log({
    component: id,
    phase,
    actualDuration: `${actualDuration.toFixed(2)}ms`,
    baseDuration: `${baseDuration.toFixed(2)}ms`,
  });

  // Send to analytics
  if (actualDuration > 100) {
    trackSlowRender(id, actualDuration);
  }
};

function ProfiledApp() {
  return (
    <Profiler id="App" onRender={onRenderCallback}>
      <App />
    </Profiler>
  );
}
```

### Backend Profiling

```typescript
import { performance, PerformanceObserver } from 'perf_hooks';

// Performance markers
performance.mark('api-start');

// ... API logic

performance.mark('api-end');
performance.measure('api-duration', 'api-start', 'api-end');

// Observer for logging
const obs = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  entries.forEach((entry) => {
    console.log({
      name: entry.name,
      duration: `${entry.duration.toFixed(2)}ms`,
    });
  });
});
obs.observe({ entryTypes: ['measure'] });
```

## Performance Budget

```javascript
// performance-budget.js
const budget = {
  // Bundle sizes (KB)
  javascript: 300,
  css: 100,
  images: 500,
  fonts: 100,

  // Web Vitals
  lcp: 2500, // Largest Contentful Paint (ms)
  fid: 100,  // First Input Delay (ms)
  cls: 0.1,  // Cumulative Layout Shift

  // Resource counts
  maxRequests: 50,
  maxScripts: 10,
};

module.exports = budget;
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Vercel React Best Practices](https://github.com/vercel/next.js/blob/canary/packages/next-codemod/transforms/__testfixtures__/next-image-to-next-image)
- [web.dev Performance](https://web.dev/performance/)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [React Performance](https://react.dev/learn/render-and-commit)
