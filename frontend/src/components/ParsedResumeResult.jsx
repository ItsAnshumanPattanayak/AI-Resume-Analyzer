function InformationItem({
  label,
  value,
}) {
  return (
    <div className="information-item">
      <span>{label}</span>
      <strong>{value || "Not detected"}</strong>
    </div>
  );
}

function ParsedResumeResult({ result }) {
  const data = result?.parsed_data;

  if (!data) {
    return null;
  }

  const skills = data.skills?.all || [];
  const sections = Object.keys(data.sections || {});
  const education = data.education || [];

  return (
    <div className="dashboard">
      <section className="result-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">
              Parsed information
            </p>
            <h2>Candidate details</h2>
          </div>

          <strong className="section-score">
            {result.word_count || 0} words
          </strong>
        </div>

        <div className="information-grid">
          <InformationItem
            label="Name"
            value={data.name}
          />

          <InformationItem
            label="Email"
            value={data.email}
          />

          <InformationItem
            label="Phone"
            value={data.phone}
          />

          <InformationItem
            label="LinkedIn"
            value={data.links?.linkedin}
          />

          <InformationItem
            label="GitHub"
            value={data.links?.github}
          />

          <InformationItem
            label="Portfolio"
            value={data.links?.portfolio}
          />
        </div>
      </section>

      <section className="result-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Detected skills</p>
            <h2>{skills.length} skills found</h2>
          </div>
        </div>

        <div className="skill-tags">
          {skills.length ? (
            skills.map((skill) => (
              <span
                className="skill-tag skill-tag-matched"
                key={skill}
              >
                {skill}
              </span>
            ))
          ) : (
            <p className="empty-text">
              No known skills were detected.
            </p>
          )}
        </div>
      </section>

      <section className="result-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Resume structure</p>
            <h2>Detected sections</h2>
          </div>
        </div>

        <div className="skill-tags">
          {sections.length ? (
            sections.map((section) => (
              <span
                className="skill-tag"
                key={section}
              >
                {section}
              </span>
            ))
          ) : (
            <p className="empty-text">
              No standard sections were detected.
            </p>
          )}
        </div>

        {education.length > 0 && (
          <div className="subsection">
            <h3>Education information</h3>

            <ul className="template-list">
              {education.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}

export default ParsedResumeResult;