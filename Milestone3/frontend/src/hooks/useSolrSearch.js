import { useState, useCallback } from 'react';

// Point to the Python Backend
const BACKEND_URL = 'http://localhost:8000/semantic_search';

export const useSolrSearch = ({ pageSize = 10 } = {}) => {
  const [results, setResults] = useState([]);
  const [selectedFilters, setSelectedFilters] = useState({});
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 1. Toggle Filter (Multi-select logic - kept for future use)
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

  // 2. Set Filter (Single-select logic - USED FOR TABS)
  const setFilter = (field, value) => {
    setSelectedFilters(prev => ({
      ...prev,
      [field]: value === null ? [] : [value] // Replace array with just this one value
    }));
  };

  // 3. Search Function
  const search = useCallback(
    async (query, requestedPage = 1, currentFilters = selectedFilters) => {
      // Allow searching with empty query if filters are present, or vice versa
      if (!query && Object.keys(currentFilters).length === 0) return;

      setLoading(true);
      setError('');
      setHasSearched(true);

      try {
        const params = new URLSearchParams({
          q: query?.trim() || '*:*',
          page: String(requestedPage),
          rows: String(pageSize),
        });

        // Check specifically for 'topic' filter
        if (currentFilters['topic'] && currentFilters['topic'].length > 0) {
            params.append('topic', currentFilters['topic'][0]);
        }

        const response = await fetch(`${BACKEND_URL}?${params.toString()}`);
        
        if (!response.ok) {
          throw new Error(`Backend error: ${response.status}`);
        }

        const data = await response.json();

        setResults(data.results || []);
        setTotal(data.total || 0);
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
    selectedFilters,
    toggleFilter,
    setFilter, // Exporting the new function
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