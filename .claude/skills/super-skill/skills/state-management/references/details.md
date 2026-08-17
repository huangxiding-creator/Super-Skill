# state-management — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## URL State Management

```typescript
import { useSearchParams, useNavigate } from 'react-router-dom';

// Reading and writing URL params
function useFilterState() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = {
    status: searchParams.get('status') || 'all',
    search: searchParams.get('search') || '',
    sortBy: searchParams.get('sortBy') || 'createdAt',
    sortOrder: searchParams.get('sortOrder') || 'desc',
    page: parseInt(searchParams.get('page') || '1'),
    limit: parseInt(searchParams.get('limit') || '20')
  };

  const setFilter = (key: string, value: string | number) => {
    setSearchParams((prev) => {
      if (value === '' || value === null) {
        prev.delete(key);
      } else {
        prev.set(key, String(value));
      }
      return prev;
    });
  };

  const resetFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  return { filters, setFilter, resetFilters };
}

// Usage
function OrderList() {
  const { filters, setFilter } = useFilterState();
  const { data, isLoading } = useOrdersQuery(filters);

  return (
    <div>
      <input
        value={filters.search}
        onChange={(e) => setFilter('search', e.target.value)}
        placeholder="Search orders..."
      />

      <select
        value={filters.status}
        onChange={(e) => setFilter('status', e.target.value)}
      >
        <option value="all">All</option>
        <option value="pending">Pending</option>
        <option value="shipped">Shipped</option>
      </select>

      {/* Order list */}
    </div>
  );
}
```

## Form State with React Hook Form

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Schema validation
const userSchema = z.object({
  email: z.string().email('Invalid email'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  age: z.number().min(18, 'Must be 18 or older').optional(),
  preferences: z.object({
    newsletter: z.boolean().default(false),
    notifications: z.boolean().default(true)
  })
});

type UserFormData = z.infer<typeof userSchema>;

function UserForm({ defaultValues, onSubmit }: UserFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
    reset
  } = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues
  });

  const handleFormSubmit = async (data: UserFormData) => {
    await onSubmit(data);
    reset();
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)}>
      <div>
        <label>Email</label>
        <input {...register('email')} type="email" />
        {errors.email && <span>{errors.email.message}</span>}
      </div>

      <div>
        <label>Name</label>
        <input {...register('name')} />
        {errors.name && <span>{errors.name.message}</span>}
      </div>

      <div>
        <label>
          <input type="checkbox" {...register('preferences.newsletter')} />
          Subscribe to newsletter
        </label>
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  );
}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [React Query Documentation](https://tanstack.com/query/latest)
- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod Documentation](https://zod.dev/)
