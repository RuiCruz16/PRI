import React from 'react';

const FilterBar = ({ facets, selectedFilters, onToggle, disabled }) => {
  // We assume 'category' is the main field you want to filter by.
  // Adjust 'category' to match your actual Solr field name (e.g., 'doc_type')
  const categories = facets['category'] || [];

  if (categories.length === 0) return null;

  return (
    <div className="filter-bar">
      <span className="filter-label">Filter by:</span>
      <div className="filter-chips">
        {categories.map((item) => {
          const isSelected = selectedFilters['category']?.includes(item.val);
          return (
            <button
              key={item.val}
              type="button"
              disabled={disabled}
              className={`filter-chip ${isSelected ? 'filter-chip--active' : ''}`}
              onClick={() => onToggle('category', item.val)}
            >
              {item.val}
              {/* Optional: Show count if useful, or hide for cleaner UI */}
              {/* <span className="chip-count">{item.count}</span> */}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default FilterBar;