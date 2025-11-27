
const Pagination = ({ page, pageSize, total, onPageChange }) => {
  if (total === 0) return null;

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const clampedPage = Math.min(Math.max(page, 1), totalPages);

  const startIndex = (clampedPage - 1) * pageSize + 1;
  const endIndex = Math.min(startIndex + pageSize - 1, total);

  const canPrev = clampedPage > 1;
  const canNext = clampedPage < totalPages;

  const pagesToShow = [];
  const maxButtons = 5;
  let start = Math.max(1, clampedPage - 2);
  let end = Math.min(totalPages, start + maxButtons - 1);

  if (end - start + 1 < maxButtons) {
    start = Math.max(1, end - maxButtons + 1);
  }

  for (let p = start; p <= end; p += 1) {
    pagesToShow.push(p);
  }

  return (
    <nav className="pagination" aria-label="Pagination">
      <div className="pagination-info">
        Showing <strong>{startIndex}</strong>–<strong>{endIndex}</strong> of{' '}
        <strong>{total.toLocaleString()}</strong> documents
      </div>

      <div className="pagination-controls">
        <button
          type="button"
          className="pagination-button"
          onClick={() => onPageChange(clampedPage - 1)}
          disabled={!canPrev}
        >
          ‹
        </button>

        {start > 1 && (
          <>
            <button
              type="button"
              className="pagination-button"
              onClick={() => onPageChange(1)}
            >
              1
            </button>
            {start > 2 && <span style={{ padding: '0 4px', fontSize: '0.8rem' }}>…</span>}
          </>
        )}

        {pagesToShow.map((p) => (
          <button
            key={p}
            type="button"
            className={
              'pagination-button' + (p === clampedPage ? ' pagination-button--active' : '')
            }
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        ))}

        {end < totalPages && (
          <>
            {end < totalPages - 1 && (
              <span style={{ padding: '0 4px', fontSize: '0.8rem' }}>…</span>
            )}
            <button
              type="button"
              className="pagination-button"
              onClick={() => onPageChange(totalPages)}
            >
              {totalPages}
            </button>
          </>
        )}

        <button
          type="button"
          className="pagination-button"
          onClick={() => onPageChange(clampedPage + 1)}
          disabled={!canNext}
        >
          ›
        </button>
      </div>
    </nav>
  );
};

export default Pagination;
