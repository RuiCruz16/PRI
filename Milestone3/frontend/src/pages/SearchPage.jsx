import React, { useState } from 'react';
import SearchBar from '../components/SearchBar';
import FilterBar from '../components/FilterBar';
import ResultsList from '../components/ResultsList';
import Pagination from '../components/Pagination';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';
import { useSolrSearch } from '../hooks/useSolrSearch'; // Adjust path if needed

const SearchPage = () => {
  const [query, setQuery] = useState('');
  
  const {
    results,
    selectedFilters,
    toggleFilter,
    setFilter, // Destructure setFilter
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

  // Handle Filter Bar Clicks
  const handleFilterToggle = (field, value) => {
    // Force Single Select for 'topic' field
    if (field === 'topic') {
        setFilter(field, value);
    } else {
        toggleFilter(field, value);
    }

    // Trigger immediate search
    // We manually construct the next state just for the search function call
    const nextFilters = { 
        ...selectedFilters, 
        [field]: value === null ? [] : [value] 
    };
    
    // Search if we already have a query or results
    if (hasSearched || query) {
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

      {/* 1. SEARCH BAR */}
      <SearchBar
        value={query}
        onChange={setQuery}
        onSubmit={handleSearch}
        loading={loading}
      />

      {/* 2. FILTER BAR */}
      <div style={{ marginTop: '1rem', marginBottom: '2rem' }}>
        <FilterBar 
            selectedFilters={selectedFilters} 
            onToggle={handleFilterToggle}
            disabled={loading}
        />
      </div>

      {/* 3. RESULTS AREA */}
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
      {error && <div style={{color:'red', textAlign:'center', marginTop: '2rem'}}>Error: {error}</div>}
      
      {!hasSearched && !loading && (
        <div className="initial-state-container">
            <p className="initial-state-text">Enter a disease or symptom to begin</p>
        </div>
      )}
    </div>
  );
};

export default SearchPage;