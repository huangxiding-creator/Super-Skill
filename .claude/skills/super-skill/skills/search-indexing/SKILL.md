---
name: search-indexing
description: Search and indexing patterns including full-text search, vector embeddings, semantic search, and search engine integration (Elasticsearch, Meilisearch, Typesense).
tags: [search, indexing, elasticsearch, vector, semantic, full-text]
version: 1.0.0
source: Based on Elasticsearch, Meilisearch, Typesense, pgvector best practices
integrated-with: super-skill v3.7+
---

# Search & Indexing Skill

This skill provides comprehensive search and indexing patterns for implementing full-text search, semantic search, and search engine integrations.

## Search Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEARCH ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FULL-TEXT SEARCH                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Tokenization       • Stemming         • Relevance     │    │
│  │ • Elasticsearch      • Meilisearch      • Typesense     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  SEMANTIC SEARCH                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Vector embeddings  • Similarity        • Contextual   │    │
│  │ • pgvector           • Pinecone          • Weaviate     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  HYBRID SEARCH                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • BM25 + Vectors    • Reranking          • Best of both │    │
│  │ • Score fusion      • Multi-stage        • Context-aware│    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  AUTOCOMPLETE                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Prefix matching    • Fuzzy search      • Typo tolerance│   │
│  │ • Trie structures    • N-grams           • Suggestions  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Elasticsearch Integration

### Index Mapping

```json
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": { "type": "keyword" },
          "completion": { "type": "completion" }
        }
      },
      "content": {
        "type": "text",
        "analyzer": "standard"
      },
      "tags": {
        "type": "keyword"
      },
      "author": {
        "properties": {
          "id": { "type": "keyword" },
          "name": {
            "type": "text",
            "fields": {
              "keyword": { "type": "keyword" }
            }
          }
        }
      },
      "publishedAt": {
        "type": "date"
      },
      "embeddings": {
        "type": "dense_vector",
        "dims": 1536,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}
```

### Query Patterns

```typescript
import { Client } from '@elastic/elasticsearch';

const client = new Client({ node: process.env.ELASTICSEARCH_URL });

// Full-text search with highlighting
async function searchArticles(query: string, options: SearchOptions = {}) {
  const { page = 1, limit = 10, filters = {} } = options;

  const response = await client.search({
    index: 'articles',
    body: {
      query: {
        bool: {
          must: [
            {
              multi_match: {
                query,
                fields: ['title^2', 'content', 'tags'],
                type: 'best_fields',
                fuzziness: 'AUTO'
              }
            }
          ],
          filter: buildFilters(filters)
        }
      },
      highlight: {
        fields: {
          title: {},
          content: {
            fragment_size: 150,
            number_of_fragments: 3
          }
        }
      },
      from: (page - 1) * limit,
      size: limit,
      sort: [
        { _score: 'desc' },
        { publishedAt: 'desc' }
      ]
    }
  });

  return {
    results: response.hits.hits.map(formatHit),
    total: response.hits.total,
    page,
    limit
  };
}

// Autocomplete
async function autocomplete(prefix: string) {
  const response = await client.search({
    index: 'articles',
    body: {
      query: {
        bool: {
          should: [
            {
              match_phrase_prefix: {
                title: {
                  query: prefix,
                  max_expansions: 10
                }
              }
            },
            {
              completion: {
                field: 'title.completion',
                prefix,
                skip_duplicates: true,
                size: 5
              }
            }
          ]
        }
      },
      _source: ['title']
    }
  });

  return response.hits.hits.map(hit => hit._source.title);
}

// Build filter clauses
function buildFilters(filters: Record<string, any>): any[] {
  const clauses = [];

  if (filters.tags) {
    clauses.push({ terms: { tags: filters.tags } });
  }

  if (filters.dateRange) {
    clauses.push({
      range: {
        publishedAt: {
          gte: filters.dateRange.start,
          lte: filters.dateRange.end
        }
      }
    });
  }

  if (filters.authorId) {
    clauses.push({ term: { 'author.id': filters.authorId } });
  }

  return clauses;
}
```

## Vector Search (pgvector)

### Setup

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create vector index for fast similarity search
CREATE INDEX ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create full-text search index
CREATE INDEX ON documents
USING GIN(to_tsvector('english', title || ' ' || content));
```

### Vector Search Implementation

```typescript
import { Pool } from 'pg';
import OpenAI from 'openai';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const openai = new OpenAI();

// Generate embeddings
async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text
  });
  return response.data[0].embedding;
}

// Insert document with embedding
async function indexDocument(title: string, content: string, metadata: any = {}) {
  const embedding = await generateEmbedding(`${title}\n${content}`);

  const result = await pool.query(
    `INSERT INTO documents (title, content, embedding, metadata)
     VALUES ($1, $2, $3, $4)
     RETURNING id`,
    [title, content, `[${embedding.join(',')}]`, metadata]
  );

  return result.rows[0].id;
}

// Semantic search
async function semanticSearch(query: string, limit: number = 10) {
  const embedding = await generateEmbedding(query);

  const result = await pool.query(
    `SELECT
      id, title, content, metadata,
      1 - (embedding <=> $1::vector) as similarity
    FROM documents
    ORDER BY embedding <=> $1::vector
    LIMIT $2`,
    [`[${embedding.join(',')}]`, limit]
  );

  return result.rows;
}

// Hybrid search (BM25 + vector)
async function hybridSearch(query: string, limit: number = 10) {
  const embedding = await generateEmbedding(query);

  const result = await pool.query(
    `WITH fulltext AS (
      SELECT id, ts_rank(to_tsvector('english', title || ' ' || content), plainto_tsquery($1)) as score
      FROM documents
      WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery($1)
      ORDER BY score DESC
      LIMIT $2 * 2
    ),
    semantic AS (
      SELECT id, 1 - (embedding <=> $3::vector) as score
      FROM documents
      ORDER BY embedding <=> $3::vector
      LIMIT $2 * 2
    )
    SELECT DISTINCT ON (d.id)
      d.id, d.title, d.content, d.metadata,
      COALESCE(f.score, 0) * 0.5 + COALESCE(s.score, 0) * 0.5 as combined_score
    FROM documents d
    LEFT JOIN fulltext f ON d.id = f.id
    LEFT JOIN semantic s ON d.id = s.id
    WHERE f.id IS NOT NULL OR s.id IS NOT NULL
    ORDER BY d.id, combined_score DESC
    LIMIT $2`,
    [query, limit, `[${embedding.join(',')}]`]
  );

  return result.rows;
}
```

## Meilisearch Integration

### Configuration

```typescript
import { MeiliSearch } from 'meilisearch';

const client = new MeiliSearch({
  host: process.env.MEILISEARCH_URL,
  apiKey: process.env.MEILISEARCH_KEY
});

// Create index with settings
async function setupIndex() {
  const index = client.index('products');

  await index.updateSettings({
    searchableAttributes: ['name', 'description', 'brand', 'category'],
    filterableAttributes: ['brand', 'category', 'price', 'inStock'],
    sortableAttributes: ['price', 'rating', 'createdAt'],
    rankingRules: [
      'words',
      'typo',
      'proximity',
      'attribute',
      'sort',
      'exactness',
      'rating:desc'
    ],
    typoTolerance: {
      enabled: true,
      minWordSizeForTypos: {
        oneTypo: 4,
        twoTypos: 8
      }
    }
  });

  return index;
}

// Index documents
async function indexProducts(products: Product[]) {
  const index = client.index('products');

  const documents = products.map(p => ({
    id: p.id,
    name: p.name,
    description: p.description,
    brand: p.brand,
    category: p.category,
    price: p.price,
    inStock: p.stock > 0,
    rating: p.rating,
    createdAt: p.createdAt.getTime()
  }));

  await index.addDocuments(documents);
}

// Search with filters
async function searchProducts(query: string, options: ProductSearchOptions = {}) {
  const index = client.index('products');

  const {
    page = 1,
    limit = 20,
    filters = {},
    sort = ['rating:desc']
  } = options;

  const filterExpressions: string[] = [];

  if (filters.brands?.length) {
    filterExpressions.push(`brand IN [${filters.brands.join(', ')}]`);
  }

  if (filters.categories?.length) {
    filterExpressions.push(`category IN [${filters.categories.join(', ')}]`);
  }

  if (filters.priceRange) {
    filterExpressions.push(`price >= ${filters.priceRange.min}`);
    filterExpressions.push(`price <= ${filters.priceRange.max}`);
  }

  if (filters.inStock) {
    filterExpressions.push('inStock = true');
  }

  const response = await index.search(query, {
    page,
    hitsPerPage: limit,
    filter: filterExpressions.length > 0 ? filterExpressions : undefined,
    sort,
    facets: ['brand', 'category']
  });

  return {
    results: response.hits,
    total: response.totalHits,
    page: response.page,
    limit: response.hitsPerPage,
    facets: response.facetDistribution
  };
}
```

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

## Integration with Super-Skill

### Phase Integration

```yaml
search_phase_mapping:
  phase_5_design:
    outputs:
      - search_architecture
      - index_mapping
      - search_requirements

  phase_8_development:
    actions:
      - setup_search_engine
      - create_index_mappings
      - implement_search_api
      - add_autocomplete

  phase_9_qa:
    actions:
      - test_relevance
      - verify_filters
      - test_performance
```

## Best Practices Checklist

### Indexing
- [ ] Proper mappings defined
- [ ] Analyzers configured
- [ ] Vectors indexed
- [ ] Incremental updates

### Search
- [ ] Relevance tuning
- [ ] Filters working
- [ ] Facets correct
- [ ] Pagination implemented

### Performance
- [ ] Indexes optimized
- [ ] Caching enabled
- [ ] Queries efficient
- [ ] Monitoring active

## Deliverables

- Search engine setup
- Index configurations
- Search API implementation
- Autocomplete feature

---

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
