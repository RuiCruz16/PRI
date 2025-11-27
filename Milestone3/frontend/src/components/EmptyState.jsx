
const EmptyState = ({ query }) => (
  <div className="message-container">
    <p className="message-title" style={{ color: '#ef4444' }}>
      No documents found
    </p>
    <p className="message-subtitle">
      Your search for <strong>&quot;{query}&quot;</strong> did not match any indexed documents.
      Try alternative disease names, synonyms, or broader clinical terms.
    </p>
  </div>
);

export default EmptyState;
