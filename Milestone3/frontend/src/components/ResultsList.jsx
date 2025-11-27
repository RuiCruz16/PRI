
import SearchResultItem from './SearchResultItem';

const ResultsList = ({ results }) => {
  return (
    <section className="results-list" aria-label="Search results">
      {results.map((r) => (
        <SearchResultItem key={r.id ?? r.url ?? Math.random()} result={r} />
      ))}
    </section>
  );
};

export default ResultsList;
