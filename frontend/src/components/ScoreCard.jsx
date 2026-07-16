function ScoreCard({
  title,
  value,
  suffix = "%",
  description,
}) {
  const safeValue = Number.isFinite(Number(value))
    ? Number(value)
    : 0;

  return (
    <article className="score-card">
      <span className="score-title">{title}</span>

      <strong className="score-value">
        {safeValue.toFixed(1)}
        {suffix}
      </strong>

      {description && (
        <p className="score-description">{description}</p>
      )}

      <div
        className="score-progress"
        role="progressbar"
        aria-label={title}
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={safeValue}
      >
        <span
          style={{
            width: `${Math.min(Math.max(safeValue, 0), 100)}%`,
          }}
        />
      </div>
    </article>
  );
}

export default ScoreCard;