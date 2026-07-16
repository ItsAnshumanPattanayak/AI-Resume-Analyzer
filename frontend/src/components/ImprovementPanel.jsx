function ImprovementPanel({ improvement }) {
  if (!improvement) {
    return null;
  }

  const recommendations =
    improvement.priority_recommendations || [];

  const weakPhrases = improvement.weak_phrases || [];
  const templates = improvement.bullet_point_templates || [];

  return (
    <section className="result-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Resume writing</p>
          <h2>Improvement suggestions</h2>
        </div>

        <strong className="section-score">
          {improvement.quality_score}% —{" "}
          {improvement.quality_rating}
        </strong>
      </div>

      <div className="recommendation-list">
        {recommendations.length ? (
          recommendations.map((item, index) => (
            <article
              className={`recommendation recommendation-${item.priority}`}
              key={`${item.category}-${index}`}
            >
              <div>
                <span className="recommendation-priority">
                  {item.priority}
                </span>

                <span className="recommendation-category">
                  {item.category}
                </span>
              </div>

              <p>{item.recommendation}</p>
            </article>
          ))
        ) : (
          <p className="empty-text">
            No major resume-quality issues were detected.
          </p>
        )}
      </div>

      {weakPhrases.length > 0 && (
        <div className="subsection">
          <h3>Weak phrases to replace</h3>

          <div className="phrase-list">
            {weakPhrases.map((item) => (
              <div
                className="phrase-item"
                key={item.weak_phrase}
              >
                <span>{item.weak_phrase}</span>
                <strong>→</strong>
                <span>{item.suggested_replacement}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {templates.length > 0 && (
        <div className="subsection">
          <h3>Bullet-point templates</h3>

          <ul className="template-list">
            {templates.map((template) => (
              <li key={template}>{template}</li>
            ))}
          </ul>

          <p className="template-warning">
            Replace placeholders only with truthful experience and
            measurable results.
          </p>
        </div>
      )}
    </section>
  );
}

export default ImprovementPanel;