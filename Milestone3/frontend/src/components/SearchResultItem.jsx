
import { Link as LinkIcon } from 'lucide-react';

const SearchResultItem = ({ result }) => (
  <article className="result-card">
    {result.url && result.url !== '#' && (
      <a
        href={result.url}
        target="_blank"
        rel="noopener noreferrer"
        className="result-url"
      >
        <LinkIcon style={{ width: 14, height: 14, marginRight: 6 }} />
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {result.url}
        </span>
      </a>
    )}

    <a
      href={result.url || '#'}
      target={result.url && result.url !== '#' ? '_blank' : undefined}
      rel={result.url && result.url !== '#' ? 'noopener noreferrer' : undefined}
      className="result-title"
    >
      {result.title || 'Untitled document'}
    </a>

    {result.snippet && (
      <p className="result-snippet">
        {result.snippet}
      </p>
    )}

    {result.meta && (
      <p className="result-snippet" style={{ marginTop: '0.3rem', fontSize: '0.8rem', color: '#9ca3af' }}>
        {result.meta}
      </p>
    )}
  </article>
);

export default SearchResultItem;
