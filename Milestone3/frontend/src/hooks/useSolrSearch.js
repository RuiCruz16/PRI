import { useState, useCallback, useEffect } from 'react';

const BACKEND_URL = 'http://localhost:8000/search';

export const useSolrSearch = ({ pageSize = 10 } = {}) => {
  const [results, setResults] = useState([]);
  const [facets, setFacets] = useState({});
  const [selectedFilters, setSelectedFilters] = useState({});
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 1. Toggle Filter Logic
  const toggleFilter = (field, value) => {
    setSelectedFilters(prev => {
      const current = prev[field] || [];
      const isSelected = current.includes(value);
      const updated = isSelected
        ? current.filter(item => item !== value)
        : [...current, value];
      return { ...prev, [field]: updated };
    });
  };

  // 2. Fetch Initial Facets (Load categories on mount)
  useEffect(() => {
    const fetchFacets = async () => {
      try {
        // We make a dummy call just to get facets
        const res = await fetch(`${BACKEND_URL}?q=*:*&rows=0`);
        const data = await res.json();
        setFacets(data.facets || {});
      } catch (e) {
        console.error("Failed to load facets", e);
      }
    };
    fetchFacets();
  }, []);

  // 3. Search Function
  const search = useCallback(
    async (query, requestedPage = 1, currentFilters = selectedFilters) => {
      if (!query && !currentFilters) return;

      setLoading(true);
      setError('');
      setHasSearched(true);

      try {
        // Construct URL Params for FastAPI
        const params = new URLSearchParams({
          q: query.trim() || '*:*',
          page: String(requestedPage),
          rows: String(pageSize),
        });

        Object.entries(currentFilters).forEach(([field, values]) => {
          values.forEach(val => {
            params.append(field, val);
          });
        });

        const response = await fetch(`${BACKEND_URL}?${params.toString()}`);
        
        if (!response.ok) {
          throw new Error(`Backend error: ${response.status}`);
        }

        const data = await response.json();

        // The Backend now returns clean data, so we just map it simply
        const mapped = (data.results || []).map(doc => ({
            id: doc.id,
            title: Array.isArray(doc.title) ? doc.title[0] : (doc.title || 'Untitled'),
            snippet: doc.snippet || doc.abstract || '',
            url: doc.url || '#',
            meta: doc.icd_code ? `ICD: ${doc.icd_code}` : null
        }));

        setResults(mapped);
        setTotal(data.total);
        if (data.facets) setFacets(data.facets);
        setPage(requestedPage);

      } catch (err) {
        console.error(err);
        setError('Failed to fetch results.');
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [pageSize, selectedFilters]
  );

  return {
    results,
    facets,
    selectedFilters,
    toggleFilter,
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