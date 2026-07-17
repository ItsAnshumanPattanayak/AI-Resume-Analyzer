function RoleRecommendations({ recommendations }) {
  const roles = recommendations?.recommended_roles || [];

  const renderSkills = (skills, className) => {
    if (!skills?.length) {
      return <span className="skill-empty">None detected</span>;
    }

    return (
      <div className="skill-tags">
        {skills.slice(0, 8).map((skill) => (
          <span className={`skill-tag ${className}`} key={skill}>
            {skill}
          </span>
        ))}
      </div>
    );
  };

  if (!roles.length) {
    return null;
  }

  return (
    <section className="result-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Career direction</p>
          <h2>Recommended job roles</h2>
        </div>
      </div>

      <div className="roles-list">
        {roles.map((role, index) => (
          <article className="role-card" key={role.role}>
            <div className="role-rank">{index + 1}</div>

            <div className="role-content">
              <div className="role-heading">
                <div>
                  <h3>{role.role}</h3>
                  <span>{role.recommendation_level}</span>
                </div>

                <strong>
                  {role.overall_match_percentage}%
                </strong>
              </div>

              <p>{role.role_description}</p>

              <div className="role-scores">
                <span>
                  Skill match: {role.skill_match_percentage}%
                </span>

                <span>
                  Semantic match:{" "}
                  {role.semantic_match_percentage}%
                </span>
              </div>

              <p className="role-reason">
                {role.explanation || role.reason}
              </p>

              {(role.matched_skills || role.missing_skills) && (
                <div className="role-skill-summary">
                  <div>
                    <h4>Matched skills</h4>
                    {renderSkills(
                      role.matched_skills,
                      "skill-tag-matched",
                    )}
                  </div>

                  <div>
                    <h4>Skills to strengthen</h4>
                    {renderSkills(
                      role.missing_skills,
                      "skill-tag-missing",
                    )}
                  </div>
                </div>
              )}

              {role.score_components && (
                <details className="role-breakdown">
                  <summary>
                    View score breakdown for {role.role}
                  </summary>

                  <dl>
                    <div>
                      <dt>Exact skill coverage</dt>
                      <dd>
                        {role.score_components.exact_skill_coverage.score}%
                        {" × "}
                        {role.score_components.exact_skill_coverage.weight}
                        {" = "}
                        {role.score_components.exact_skill_coverage.weighted_score}
                      </dd>
                    </div>
                    <div>
                      <dt>Semantic similarity</dt>
                      <dd>
                        {role.score_components.semantic_similarity.score}%
                        {" × "}
                        {role.score_components.semantic_similarity.weight}
                        {" = "}
                        {role.score_components.semantic_similarity.weighted_score}
                      </dd>
                    </div>
                    <div>
                      <dt>Final score</dt>
                      <dd>
                        {role.score_components.final_score.score}%
                      </dd>
                    </div>
                  </dl>
                </details>
              )}

              {(role.strengths?.length > 0 ||
                role.improvement_areas?.length > 0) && (
                <div className="role-feedback">
                  {role.strengths?.length > 0 && (
                    <div>
                      <h4>Strengths</h4>
                      <ul>
                        {role.strengths.map((strength) => (
                          <li key={strength}>{strength}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {role.improvement_areas?.length > 0 && (
                    <div>
                      <h4>Improvement areas</h4>
                      <ul>
                        {role.improvement_areas.map((area) => (
                          <li key={area}>{area}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default RoleRecommendations;
