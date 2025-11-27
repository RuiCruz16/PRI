import { useState } from 'react';
import { useSolrSearch } from '../hooks/useSolrSearch';
import SearchBar from '../components/SearchBar';
import ResultsList from '../components/ResultsList';
import Pagination from '../components/Pagination';
import EmptyState from '../components/EmptyState';
import LoadingState from '../components/LoadingState';

const SearchPage = () => {
  const [query, setQuery] = useState('');

  const {
    results,
    total,
    page,
    pageSize,
    loading,
    error,
    hasSearched,
    search,
    setPage,
  } = useSolrSearch({ pageSize: 10 });

  const handleSubmit = (value) => {
    setQuery(value);
    search(value, 1); // reset to first page
  };

  const handlePageChange = (newPage) => {
    if (!query) return;
    setPage(newPage);
    search(query, newPage);
  };

  const showResults = hasSearched && !loading && !error && results.length > 0;

  return (
    <>
      <header className="search-header">
        <div className="header-title">
          Human Disease Search
        </div>
      </header>

      <SearchBar
        value={query}
        onChange={setQuery}
        onSubmit={handleSubmit}
        loading={loading}
      />

      {loading && <LoadingState />}

      {!loading && error && (
        <div className="message-container">
          <p className="message-title" style={{ color: '#ef4444' }}>
            Search error
          </p>
          <p className="message-subtitle">
            {error || 'Could not connect to the search engine. Please try again.'}
          </p>
        </div>
      )}

      {!loading && !error && !hasSearched && (
        <div className="initial-state-container">
          <p className="initial-state-text">
            Start by typing a disease name or symptom in the search bar above.
          </p>
        </div>
      )}

      {!loading && !error && hasSearched && results.length === 0 && (
        <EmptyState query={query} />
      )}

      {showResults && (
        <>
          <div className="results-meta">
            <span className="results-meta-query">
              Results for <strong>&quot;{query}&quot;</strong>
            </span>
            <span>
              {total.toLocaleString()} documents · page {page}
            </span>
          </div>

          <ResultsList results={results} />

          <Pagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </>
  );
};

export default SearchPage;
