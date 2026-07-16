function RoleRecommendations({ recommendations }) {
  const roles = recommendations?.recommended_roles || [];

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

              <p className="role-reason">{role.reason}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default RoleRecommendations;