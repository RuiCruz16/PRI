import { useState } from 'react';
import SearchBar from '../components/SearchBar';
import FilterBar from '../components/FilterBar';
import ResultsList from '../components/ResultsList';
import Pagination from '../components/Pagination';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';
import { useSolrSearch } from '../hooks/useSolrSearch';

const SearchPage = () => {
  const [query, setQuery] = useState('');

  const {
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
  } = useSolrSearch({ pageSize: 10 });

  const handleSearch = (newQuery) => {
    search(newQuery, 1, selectedFilters); 
  };

  const handleFilterToggle = (field, value) => {
    toggleFilter(field, value);
    if (hasSearched || query) {
        const currentList = selectedFilters[field] || [];
        const isSelected = currentList.includes(value);
        const newList = isSelected 
            ? currentList.filter(i => i !== value) 
            : [...currentList, value];
        const nextFilters = { ...selectedFilters, [field]: newList };
        search(query, 1, nextFilters);
    }
  };

  const handlePageChange = (newPage) => {
    search(query, newPage, selectedFilters);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };


  return (
    <div>
      <div className="search-header">
        <h1 className="header-title">
          ClinicalSearch <span className="header-title-badge">Pro</span>
        </h1>
        <p className="header-subtitle">
          Advanced indexing for medical documentation
        </p>
      </div>

      <SearchBar
        value={query}
        onChange={setQuery}
        onSubmit={handleSearch}
        loading={loading}
      />

      <div style={{ marginTop: '1rem', marginBottom: '2rem' }}>
        <FilterBar 
            facets={facets} 
            selectedFilters={selectedFilters} 
            onToggle={handleFilterToggle}
            disabled={loading}
        />
      </div>

      {hasSearched && !loading && !error && (
        <>
          <div className="results-meta">
            <span className="results-meta-query">
              Results for "{query}"
            </span>
            <span>{total.toLocaleString()} found</span>
          </div>

          {results.length > 0 ? (
            <>
              <ResultsList results={results} />
              <Pagination
                page={page}
                pageSize={pageSize}
                total={total}
                onPageChange={handlePageChange}
              />
            </>
          ) : (
            <EmptyState query={query} />
          )}
        </>
      )}

      {loading && <LoadingState />}
      {error && <div style={{color:'red', textAlign:'center'}}>{error}</div>}
    </div>
  );
};

export default SearchPage;
