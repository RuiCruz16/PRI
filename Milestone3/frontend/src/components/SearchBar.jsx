import React, { useState, useEffect, useRef } from 'react';
import { Search } from 'lucide-react';

const SearchBar = ({ value, onChange, onSubmit, loading }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const wrapperRef = useRef(null);

  // Close dropdown if clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fetch suggestions when value changes (Debounced)
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!value || value.length < 2) {
        setSuggestions([]);
        return;
      }

      try {
        const res = await fetch(`http://localhost:8000/autocomplete?q=${encodeURIComponent(value)}`);
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data);
          setShowSuggestions(true);
        }
      } catch (err) {
        console.error("Failed to fetch suggestions", err);
      }
    };

    const timeoutId = setTimeout(fetchSuggestions, 300); // 300ms debounce
    return () => clearTimeout(timeoutId);
  }, [value]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value.trim()) return;
    setShowSuggestions(false);
    onSubmit(value.trim());
  };

  const handleSuggestionClick = (suggestion) => {
    onChange(suggestion); // Update input value
    setShowSuggestions(false); // Hide dropdown
    onSubmit(suggestion); // Trigger search immediately
  };

  return (
    <div ref={wrapperRef} className="search-bar-container" style={{ position: 'relative', width: '100%' }}>
      <form onSubmit={handleSubmit} className="search-bar">
        <div className="search-input-wrapper">
          <Search
            className="search-icon"
            style={{
              position: 'absolute',
              left: '0.95rem',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '1.1rem',
              height: '1.1rem',
              color: '#9ca3af',
            }}
          />
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => value.length >= 2 && setShowSuggestions(true)}
            placeholder="Search diseases, symptoms, or document text…"
            className="query-input"
            disabled={loading}
            autoComplete="off" // Disable browser default autocomplete
          />
        </div>
        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="submit-btn"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {/* Autocomplete Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <ul className="suggestions-dropdown">
          {suggestions.map((item, index) => (
            <li 
              key={index} 
              className="suggestion-item"
              onClick={() => handleSuggestionClick(item)}
            >
              <Search size={14} style={{ marginRight: '10px', color: '#9ca3af' }} />
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SearchBar;