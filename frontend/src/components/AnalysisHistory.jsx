function formatDate(value) {
  if (!value) {
    return "Unknown date";
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(new Date(value));
}

function displayScore(value) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${Number(value).toFixed(1)}%`;
}

function AnalysisHistory({
  records,
  loading,
  error,
  onOpen,
  onDelete,
  onRefresh,
}) {
  return (
    <section className="result-section history-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Saved reports</p>
          <h2>Analysis history</h2>
        </div>

        <button
          className="text-button"
          type="button"
          onClick={onRefresh}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      {loading && (
        <p className="empty-text">
          Loading saved reports...
        </p>
      )}

      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}

      {!loading && !records.length && (
        <p className="empty-text">
          No reports have been saved yet.
        </p>
      )}

      <div className="history-list">
        {records.map((record) => (
          <article
            className="history-card"
            key={record.id}
          >
            <div className="history-main">
              <span className="history-type">
                {record.analysis_type}
              </span>

              <h3>
                {record.candidate_name ||
                  record.filename}
              </h3>

              <p>{record.filename}</p>

              <small>
                {formatDate(record.created_at)}
              </small>
            </div>

            <div className="history-scores">
              <span>
                ATS
                <strong>
                  {displayScore(record.ats_score)}
                </strong>
              </span>

              <span>
                Quality
                <strong>
                  {displayScore(
                    record.quality_score,
                  )}
                </strong>
              </span>

              <span>
                Best role
                <strong>
                  {record.best_role || "—"}
                </strong>
              </span>
            </div>

            <div className="history-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={() => onOpen(record.id)}
              >
                Open
              </button>

              <button
                className="danger-button"
                type="button"
                onClick={() => onDelete(record.id)}
              >
                Delete
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default AnalysisHistory;