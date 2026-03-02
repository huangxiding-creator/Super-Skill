---
name: performance-optimization
description: Performance optimization patterns for frontend, backend, database, and infrastructure. Includes profiling, caching strategies, bundle optimization, and database query optimization.
tags: [performance, optimization, caching, profiling, bundle, database]
version: 1.0.0
source: Based on Vercel React best practices, web.dev performance patterns
integrated-with: super-skill v3.7+
---

# Performance Optimization Skill

This skill provides comprehensive performance optimization patterns for frontend, backend, database, and infrastructure layers, enabling high-performance application development.

## Performance Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                 PERFORMANCE OPTIMIZATION STACK                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FRONTEND                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Bundle Size     • Code Splitting   • Lazy Loading     │    │
│  │ • React.memo      • Virtualization    • Image Opt       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  BACKEND                                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Connection Pool • Async Operations  • Rate Limiting   │    │
│  │ • Caching         • Load Balancing    • Compression     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  DATABASE                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Indexing        • Query Optimization • Connection Mgmt │    │
│  │ • Replication     • Partitioning       • Caching        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  INFRASTRUCTURE                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • CDN            • Edge Computing    • Containerization │    │
│  │ • Auto-scaling   • Health Checks     • Monitoring       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Frontend Optimization

### Bundle Size Optimization

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable bundle analyzer
  experimental: {
    bundlePagesExternals: true,
  },

  // Webpack optimizations
  webpack: (config, { isServer }) => {
    // Tree shaking
    config.optimization.usedExports = true;
    config.optimization.sideEffects = true;

    // Code splitting
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    };

    return config;
  },

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  },
};

module.exports = nextConfig;
```

### React Performance Patterns

```typescript
import { memo, useMemo, useCallback, useState } from 'react';

// Memo for preventing unnecessary re-renders
interface UserCardProps {
  user: User;
  onSelect: (id: string) => void;
}

export const UserCard = memo<UserCardProps>(({ user, onSelect }) => {
  return (
    <div onClick={() => onSelect(user.id)}>
      {user.name}
    </div>
  );
});

// useMemo for expensive calculations
function DataTable({ data, filter }: DataTableProps) {
  const filteredData = useMemo(() => {
    return data.filter(item => item.name.includes(filter));
  }, [data, filter]);

  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => a.name.localeCompare(b.name));
  }, [filteredData]);

  return <Table data={sortedData} />;
}

// useCallback for stable references
function UserList({ users }: UserListProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleSelect = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  return (
    <div>
      {users.map(user => (
        <UserCard
          key={user.id}
          user={user}
          onSelect={handleSelect}
        />
      ))}
    </div>
  );
}
```

### Virtualization for Large Lists

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualizedList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50, // Estimated row height
    overscan: 5, // Extra items to render
  });

  return (
    <div ref={parentRef} style={{ height: '500px', overflow: 'auto' }}>
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map(virtualRow => (
          <div
            key={virtualRow.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            {items[virtualRow.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Image Optimization

```typescript
import Image from 'next/image';

// Optimized image component
function OptimizedImage({ src, alt, width, height }: ImageProps) {
  return (
    <Image
      src={src}
      alt={alt}
      width={width}
      height={height}
      loading="lazy"
      placeholder="blur"
      blurDataURL={generateBlurDataURL(width, height)}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    />
  );
}

// Responsive images with srcset
function ResponsiveImage({ src, alt }: { src: string; alt: string }) {
  return (
    <picture>
      <source
        type="image/avif"
        srcSet={`${src}?format=avif&w=640 640w,
                 ${src}?format=avif&w=1280 1280w`}
      />
      <source
        type="image/webp"
        srcSet={`${src}?format=webp&w=640 640w,
                 ${src}?format=webp&w=1280 1280w`}
      />
      <img
        src={src}
        alt={alt}
        loading="lazy"
        decoding="async"
      />
    </picture>
  );
}
```

## Backend Optimization

### Caching Strategies

```typescript
// Redis caching layer
import { Redis } from 'ioredis';

class CacheService {
  private redis: Redis;

  constructor() {
    this.redis = new Redis(process.env.REDIS_URL);
  }

  async get<T>(key: string): Promise<T | null> {
    const cached = await this.redis.get(key);
    if (cached) {
      return JSON.parse(cached);
    }
    return null;
  }

  async set<T>(
    key: string,
    value: T,
    ttl: number = 3600
  ): Promise<void> {
    await this.redis.setex(key, ttl, JSON.stringify(value));
  }

  async getOrSet<T>(
    key: string,
    factory: () => Promise<T>,
    ttl: number = 3600
  ): Promise<T> {
    const cached = await this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    const value = await factory();
    await this.set(key, value, ttl);
    return value;
  }
}

// Usage
const cache = new CacheService();

async function getUser(id: string): Promise<User> {
  return cache.getOrSet(
    `user:${id}`,
    () => db.user.findUnique({ where: { id } }),
    300 // 5 minutes TTL
  );
}
```

### Connection Pooling

```typescript
import { Pool } from 'pg';

// PostgreSQL connection pool
const pool = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20, // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

async function query<T>(sql: string, params: any[] = []): Promise<T[]> {
  const client = await pool.connect();
  try {
    const result = await client.query(sql, params);
    return result.rows;
  } finally {
    client.release();
  }
}
```

### Async Operations

```typescript
import { setTimeout as sleep } from 'timers/promises';

// Batch processing with concurrency limit
async function processBatch<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  concurrency: number = 10
): Promise<R[]> {
  const results: R[] = [];
  const queue = [...items];

  async function worker() {
    while (queue.length > 0) {
      const item = queue.shift();
      if (item) {
        const result = await processor(item);
        results.push(result);
      }
    }
  }

  const workers = Array(Math.min(concurrency, items.length))
    .fill(null)
    .map(() => worker());

  await Promise.all(workers);
  return results;
}

// Usage
const results = await processBatch(
  users,
  async (user) => sendEmail(user.email, 'Welcome!'),
  5 // Process 5 at a time
);
```

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

## Integration with Super-Skill

### Phase Integration

```yaml
performance_phase_mapping:
  phase_5_design:
    actions:
      - define_performance_budget
      - design_caching_strategy
      - plan_database_indexes

  phase_8_development:
    actions:
      - implement_code_splitting
      - add_react_optimization
      - setup_connection_pooling

  phase_9_qa:
    actions:
      - run_lighthouse_audit
      - profile_bottlenecks
      - check_bundle_size

  phase_10_optimization:
    actions:
      - optimize_slow_queries
      - implement_caching
      - fine_tune_performance
```

## Best Practices

### Frontend
- [ ] Code splitting implemented
- [ ] Images optimized (WebP, lazy loading)
- [ ] Virtualization for long lists
- [ ] Memoization for expensive calculations
- [ ] Bundle size under budget

### Backend
- [ ] Connection pooling configured
- [ ] Caching strategy implemented
- [ ] Async operations used
- [ ] Rate limiting in place
- [ ] Response compression enabled

### Database
- [ ] Proper indexes created
- [ ] N+1 queries eliminated
- [ ] Query plans analyzed
- [ ] Connection pooling active
- [ ] Read replicas configured

## Checklist

### Before Optimization
- [ ] Performance baseline measured
- [ ] Bottlenecks identified
- [ ] Budget defined
- [ ] Profiling tools configured

### During Optimization
- [ ] Changes measured
- [ ] No regressions introduced
- [ ] Documentation updated
- [ ] Tests passing

### After Optimization
- [ ] Budget targets met
- [ ] Core Web Vitals passing
- [ ] Monitoring configured
- [ ] Performance report generated

## Deliverables

- Performance budget configuration
- Optimized code components
- Database indexes
- Caching implementation
- Performance report

---

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
