
import { Search } from 'lucide-react';

const SearchBar = ({ value, onChange, onSubmit, loading }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  };

  return (
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
          placeholder="Search diseases, symptoms, or document text…"
          className="query-input"
          disabled={loading}
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
  );
};

export default SearchBar;
