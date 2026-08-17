---
name: state-management
description: State management patterns for frontend applications including Redux, Zustand, React Context, and server state management with React Query/SWR.
tags: [state, redux, zustand, react-query, swr, context]
version: 1.0.0
source: Based on Redux, Zustand, React Query, SWR best practices
integrated-with: super-skill v3.7+
---
# State Management Skill

This skill provides comprehensive state management patterns for frontend applications, covering client state (Redux, Zustand, Context) and server state (React Query, SWR).

## State Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    STATE MANAGEMENT TYPES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SERVER STATE (Async)                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • API data        • Cache management   • Revalidation   │    │
│  │ • React Query     • SWR               • RTK Query       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  CLIENT STATE (Sync)                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • UI state        • Form state          • Session       │    │
│  │ • Redux           • Zustand             • Context       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  URL STATE                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Route params    • Query strings       • Navigation    │    │
│  │ • React Router    • Next.js router      • History API   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  FORM STATE                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Input values    • Validation          • Submission    │    │
│  │ • React Hook Form • Formik              • Zod           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Server State with React Query

### Setup

```typescript
// QueryClient setup
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 minutes
      gcTime: 10 * 60 * 1000,    // 10 minutes (formerly cacheTime)
      retry: 2,
      refetchOnWindowFocus: false
    }
  }
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <ReactQueryDevtools />
    </QueryClientProvider>
  );
}
```

### Query Patterns

```typescript
// useQuery for data fetching
import { useQuery } from '@tanstack/react-query';

interface User {
  id: string;
  name: string;
  email: string;
}

// Basic query
function useUser(id: string) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => fetchUser(id),
    enabled: !!id  // Only run when id exists
  });
}

// Query with dependencies
function useUserOrders(userId: string, filters: OrderFilters) {
  return useQuery({
    queryKey: ['orders', userId, filters],
    queryFn: () => fetchOrders(userId, filters),
    staleTime: 30000
  });
}

// Parallel queries
function useDashboardData(userId: string) {
  const user = useQuery({ queryKey: ['user', userId], queryFn: () => fetchUser(userId) });
  const orders = useQuery({ queryKey: ['orders', userId], queryFn: () => fetchOrders(userId) });
  const notifications = useQuery({
    queryKey: ['notifications', userId],
    queryFn: () => fetchNotifications(userId)
  });

  return {
    user: user.data,
    orders: orders.data,
    notifications: notifications.data,
    isLoading: user.isLoading || orders.isLoading || notifications.isLoading
  };
}

// Dependent queries
function useUserProfile(userId: string) {
  const { data: user } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId)
  });

  const { data: preferences } = useQuery({
    queryKey: ['preferences', userId],
    queryFn: () => fetchPreferences(userId),
    enabled: !!user?.hasPreferences
  });

  return { user, preferences };
}
```

### Mutation Patterns

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

// Basic mutation
function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateUserInput) => createUser(data),
    onSuccess: (newUser) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['users'] });

      // Optimistically update cache
      queryClient.setQueryData(['user', newUser.id], newUser);
    },
    onError: (error) => {
      toast.error(`Failed to create user: ${error.message}`);
    }
  });
}

// Optimistic update
function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateUserInput) => updateUser(data.id, data),

    // Optimistic update
    onMutate: async (newData) => {
      // Cancel ongoing queries
      await queryClient.cancelQueries({ queryKey: ['user', newData.id] });

      // Snapshot previous value
      const previousUser = queryClient.getQueryData(['user', newData.id]);

      // Optimistically update
      queryClient.setQueryData(['user', newData.id], (old: User) => ({
        ...old,
        ...newData
      }));

      return { previousUser };
    },

    // Rollback on error
    onError: (error, newData, context) => {
      queryClient.setQueryData(['user', newData.id], context.previousUser);
    },

    // Always refetch after error or success
    onSettled: (data, error, variables) => {
      queryClient.invalidateQueries({ queryKey: ['user', variables.id] });
    }
  });
}

// Usage in component
function UserEditForm({ userId }: { userId: string }) {
  const { data: user } = useUser(userId);
  const updateMutation = useUpdateUser();

  const handleSubmit = (formData: UpdateUserInput) => {
    updateMutation.mutate({ id: userId, ...formData });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button
        type="submit"
        disabled={updateMutation.isPending}
      >
        {updateMutation.isPending ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
}
```

## Zustand for Client State

### Basic Store

```typescript
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface UserState {
  user: User | null;
  isAuthenticated: boolean;

  // Actions
  setUser: (user: User | null) => void;
  logout: () => void;
}

const useUserStore = create<UserState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isAuthenticated: false,

        setUser: (user) =>
          set({ user, isAuthenticated: !!user }, false, 'setUser'),

        logout: () =>
          set({ user: null, isAuthenticated: false }, false, 'logout')
      }),
      { name: 'user-storage' }
    )
  )
);

// Usage
function Header() {
  const user = useUserStore((state) => state.user);
  const logout = useUserStore((state) => state.logout);

  return (
    <header>
      {user && (
        <>
          <span>{user.name}</span>
          <button onClick={logout}>Logout</button>
        </>
      )}
    </header>
  );
}
```

### Slices Pattern

```typescript
// Slice: Cart
interface CartSlice {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (productId: string) => void;
  clearCart: () => void;
  getTotal: () => number;
}

const createCartSlice: StateCreator<CartSlice> = (set, get) => ({
  items: [],

  addItem: (item) =>
    set((state) => {
      const existing = state.items.find((i) => i.productId === item.productId);
      if (existing) {
        return {
          items: state.items.map((i) =>
            i.productId === item.productId
              ? { ...i, quantity: i.quantity + item.quantity }
              : i
          )
        };
      }
      return { items: [...state.items, item] };
    }),

  removeItem: (productId) =>
    set((state) => ({
      items: state.items.filter((i) => i.productId !== productId)
    })),

  clearCart: () => set({ items: [] }),

  getTotal: () => {
    return get().items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }
});

// Slice: Theme
interface ThemeSlice {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

const createThemeSlice: StateCreator<ThemeSlice> = (set) => ({
  theme: 'light',
  toggleTheme: () =>
    set((state) => ({
      theme: state.theme === 'light' ? 'dark' : 'light'
    }))
});

// Combined store
const useStore = create<CartSlice & ThemeSlice>()((...a) => ({
  ...createCartSlice(...a),
  ...createThemeSlice(...a)
}));
```

## React Context for Simple State

```typescript
import { createContext, useContext, useReducer, ReactNode } from 'react';

// Types
interface AppState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
}

type AppAction =
  | { type: 'SET_THEME'; payload: 'light' | 'dark' }
  | { type: 'TOGGLE_SIDEBAR' };

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_THEME':
      return { ...state, theme: action.payload };
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarOpen: !state.sidebarOpen };
    default:
      return state;
  }
}

// Context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

// Provider
function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, {
    theme: 'light',
    sidebarOpen: false
  });

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook
function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}

// Usage
function ThemeToggle() {
  const { state, dispatch } = useApp();

  return (
    <button
      onClick={() =>
        dispatch({ type: 'SET_THEME', payload: state.theme === 'light' ? 'dark' : 'light' })
      }
    >
      Toggle {state.theme}
    </button>
  );
}
```

## Integration with Super-Skill

### Phase Integration

```yaml
state_phase_mapping:
  phase_5_design:
    outputs:
      - state_architecture_diagram
      - data_flow_diagram
      - api_cache_strategy

  phase_8_development:
    actions:
      - setup_react_query
      - implement_stores
      - add_url_state_sync
      - create_form_handlers
```

## Best Practices Checklist

### Server State
- [ ] Stale time configured
- [ ] Cache invalidation strategy
- [ ] Optimistic updates for mutations
- [ ] Error handling

### Client State
- [ ] Minimal global state
- [ ] Proper selectors
- [ ] DevTools enabled
- [ ] Persistence configured

### URL State
- [ ] Shareable URLs
- [ ] Browser history support
- [ ] Default values handled
- [ ] Reset functionality

## Deliverables

- React Query configuration
- Zustand stores
- Context providers
- Form schemas

---

## Detail Reference

Loaded on demand from [references/details.md](references/details.md): `URL State Management`, `Form State with React Hook Form`, `Version History`, `References`.
