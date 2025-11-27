
import { useState, useCallback } from 'react';

// Toggle this to true if you want to use mock data while Solr is not ready
const USE_MOCK = true;

const mockResults = [
  {
    id: 1,
    title: 'Diabetes mellitus type 2 — clinical overview',
    snippet:
      'Diabetes mellitus type 2 is a chronic metabolic disease characterized by insulin resistance and progressive β-cell dysfunction...',
    url: '#',
  },
  {
    id: 2,
    title: 'Hypertension guidelines 2023',
    snippet:
      'Updated recommendations for diagnosis and management of arterial hypertension, including target blood pressure for high-risk patients...',
    url: '#',
  },
];

const SOLR_BASE_URL = 'http://localhost:8983/solr/mycollection/select';

export const useSolrSearch = ({ pageSize = 10 } = {}) => {
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const mapSolrDocToResult = (doc) => {
    // Adjust these field names to match your schema
    const title =
      doc.title ||
      doc.disease_name ||
      doc.name ||
      'Untitled document';

    const textField =
      doc.snippet ||
      doc.abstract ||
      doc.description ||
      doc.text ||
      '';

    const url =
      doc.url ||
      doc.link ||
      '#';

    const snippet =
      Array.isArray(textField)
        ? textField[0]
        : textField;

    return {
      id: doc.id || url || title,
      title,
      snippet: snippet ? String(snippet).slice(0, 320) : '',
      url,
      meta: doc.icd_code ? `ICD code: ${doc.icd_code}` : undefined,
    };
  };

  const search = useCallback(
    async (query, requestedPage = 1) => {
      if (!query || !query.trim()) return;

      setLoading(true);
      setError('');
      setHasSearched(true);

      try {
        // MOCK mode for quick testing
        if (USE_MOCK) {
          await new Promise((r) => setTimeout(r, 500));
          setResults(mockResults);
          setTotal(mockResults.length);
          setPage(1);
          setLoading(false);
          return;
        }

        const q = query.trim();
        const start = (requestedPage - 1) * pageSize;

        const params = new URLSearchParams({
          q: q || '*:*',
          start: String(start),
          rows: String(pageSize),
          wt: 'json',
          // Optional: use edismax and tell it which fields to search
          defType: 'edismax',
          qf: 'title^3 disease_name^3 abstract^2 text',
        });

        const response = await fetch(`${SOLR_BASE_URL}?${params.toString()}`);
        if (!response.ok) {
          throw new Error(`Solr returned status ${response.status}`);
        }

        const data = await response.json();

        const docs = data?.response?.docs ?? [];
        const mapped = docs.map(mapSolrDocToResult);
        const numFound = data?.response?.numFound ?? mapped.length;

        setResults(mapped);
        setTotal(numFound);
        setPage(requestedPage);
      } catch (err) {
        console.error('Error querying Solr:', err);
        setError(
          err?.message || 'Unexpected error while querying the search index.'
        );
        setResults([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    },
    [pageSize]
  );

  return {
    results,
    total,
    page,
    pageSize,
    loading,
    error,
    hasSearched,
    search,
    setPage,
  };
};
