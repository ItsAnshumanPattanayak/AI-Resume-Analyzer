function SkillTags({ skills, variant = "default" }) {
  if (!skills?.length) {
    return <p className="empty-text">No skills detected.</p>;
  }

  return (
    <div className="skill-tags">
      {skills.map((skill) => (
        <span
          className={`skill-tag skill-tag-${variant}`}
          key={skill}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}

function SkillsPanel({ skillData }) {
  if (!skillData) {
    return null;
  }

  return (
    <section className="result-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Job alignment</p>
          <h2>Skill comparison</h2>
        </div>

        <strong className="section-score">
          {skillData.skill_match_percentage ?? 0}% matched
        </strong>
      </div>

      <div className="skills-grid">
        <article className="skills-column">
          <h3>Matched skills</h3>
          <SkillTags
            skills={skillData.matched_skills}
            variant="matched"
          />
        </article>

        <article className="skills-column">
          <h3>Missing skills</h3>
          <SkillTags
            skills={skillData.missing_skills}
            variant="missing"
          />
        </article>

        <article className="skills-column">
          <h3>Additional resume skills</h3>
          <SkillTags
            skills={skillData.additional_resume_skills}
          />
        </article>
      </div>
    </section>
  );
}

export default SkillsPanel;