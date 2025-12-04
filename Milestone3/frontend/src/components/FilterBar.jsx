// Must match Python TOPIC_MAPPING keys
const FILTERS = [
  { label: 'All', value: null },
  { label: 'Heart & Blood', value: 'Cardiovascular' },
  { label: 'Lungs & Breathing', value: 'Respiratory' },
  { label: 'Brain & Nerves', value: 'Neurological' },
  { label: 'Stomach & Digestion', value: 'Gastrointestinal' },
  { label: 'Skin', value: 'Dermatological' },
];

const FilterBar = ({ selectedFilters, onToggle, disabled }) => {
  // Get the current selected topic (safe check)
  const currentTopic = selectedFilters['topic'] && selectedFilters['topic'].length > 0 
      ? selectedFilters['topic'][0] 
      : null;

  return (
    <div className="filter-bar">
      <span className="filter-label">Filter by System:</span>
      <div className="filter-chips">
        {FILTERS.map((f) => {
          const isActive = currentTopic === f.value || (f.value === null && !currentTopic);
          return (
            <button
              key={f.label}
              type="button"
              disabled={disabled}
              className={`filter-chip ${isActive ? 'filter-chip--active' : ''}`}
              onClick={() => onToggle('topic', f.value)}
            >
              {f.label}
            </button>
          );
        })}
        </div>
    </div>
  );
};

export default FilterBar;