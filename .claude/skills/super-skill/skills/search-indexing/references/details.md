# search-indexing — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## Search Patterns

### Faceted Search

```typescript
interface FacetConfig {
  name: string;
  type: 'terms' | 'range' | 'histogram';
  field: string;
  size?: number;
}

async function facetedSearch(
  query: string,
  facets: FacetConfig[],
  filters: Record<string, any> = {}
) {
  const response = await client.search({
    index: 'products',
    body: {
      query: {
        multi_match: {
          query,
          fields: ['name^2', 'description']
        }
      },
      aggs: buildFacetAggregations(facets),
      post_filter: buildPostFilter(filters)
    }
  });

  return {
    results: response.hits.hits,
    facets: parseFacetResults(response.aggregations)
  };
}

function buildFacetAggregations(facets: FacetConfig[]): any {
  const aggs: any = {};

  for (const facet of facets) {
    if (facet.type === 'terms') {
      aggs[facet.name] = {
        terms: {
          field: facet.field,
          size: facet.size || 10
        }
      };
    } else if (facet.type === 'range') {
      aggs[facet.name] = {
        range: {
          field: facet.field,
          ranges: [
            { to: 50 },
            { from: 50, to: 100 },
            { from: 100, to: 500 },
            { from: 500 }
          ]
        }
      };
    }
  }

  return aggs;
}
```

### Search-as-you-type

```typescript
import { debounce } from 'lodash';

function useSearchAsYouType(delay: number = 300) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const debouncedSearch = useMemo(
    () =>
      debounce(async (searchQuery: string) => {
        if (searchQuery.length < 2) {
          setResults([]);
          setIsLoading(false);
          return;
        }

        try {
          const searchResults = await autocomplete(searchQuery);
          setResults(searchResults);
        } catch (error) {
          console.error('Search error:', error);
        } finally {
          setIsLoading(false);
        }
      }, delay),
    []
  );

  const handleQueryChange = (newQuery: string) => {
    setQuery(newQuery);
    setIsLoading(true);
    debouncedSearch(newQuery);
  };

  return { query, results, isLoading, handleQueryChange };
}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Elasticsearch Documentation](https://www.elastic.co/guide/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Meilisearch](https://www.meilisearch.com/docs)
- [Typesense](https://typesense.org/docs/)
