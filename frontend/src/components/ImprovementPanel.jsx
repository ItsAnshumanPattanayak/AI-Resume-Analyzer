function ImprovementPanel({ improvement }) {
  if (!improvement) {
    return null;
  }

  const recommendations =
    improvement.priority_recommendations || [];

  const weakPhrases = improvement.weak_phrases || [];
  const templates = improvement.bullet_point_templates || [];
  const priorityActions = improvement.priority_actions || [];
  const sectionFeedback = improvement.section_feedback || [];
  const bulletFeedback = improvement.bullet_feedback || [];

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

      {improvement.overall_feedback_summary && (
        <div className="feedback-summary">
          <h3>Feedback summary</h3>
          <p>{improvement.overall_feedback_summary}</p>
        </div>
      )}

      {priorityActions.length > 0 && (
        <div className="subsection">
          <h3>First actions to take</h3>
          <ol className="priority-actions">
            {priorityActions.map((action) => (
              <li key={action.id}>
                <strong>{action.priority} priority:</strong>{" "}
                {action.action}
              </li>
            ))}
          </ol>
        </div>
      )}

      {sectionFeedback.length > 0 && (
        <div className="subsection">
          <h3>Section feedback</h3>
          <div className="feedback-details-list">
            {sectionFeedback.map((section) => (
              <details key={section.section_name}>
                <summary>
                  {section.section_name} — {section.detected ? "detected" : "not detected"}
                </summary>
                {section.strengths?.map((strength) => (
                  <p key={strength}>{strength}</p>
                ))}
                {section.issues?.map((issue) => (
                  <p key={issue.id}>{issue.message}</p>
                ))}
                {section.suggestions?.map((suggestion) => (
                  <p key={suggestion}>{suggestion}</p>
                ))}
              </details>
            ))}
          </div>
        </div>
      )}

      {bulletFeedback.length > 0 && (
        <div className="subsection">
          <h3>Bullet feedback</h3>
          <div className="feedback-details-list">
            {bulletFeedback.map((bullet) => (
              <details key={bullet.id}>
                <summary>{bullet.section_name} bullet</summary>
                <p>{bullet.evidence}</p>
                {bullet.issues?.map((issue) => (
                  <p key={issue.id}>{issue.message}</p>
                ))}
              </details>
            ))}
          </div>
        </div>
      )}

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
