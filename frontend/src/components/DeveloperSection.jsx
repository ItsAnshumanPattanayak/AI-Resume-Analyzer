const TECHNOLOGIES = [
  "React",
  "Python",
  "FastAPI",
  "PostgreSQL",
  "Sentence Transformers",
  "Machine Learning",
  "Natural Language Processing",
  "Docker",
  "REST APIs",
  "JWT Authentication",
];


function DeveloperIcon() {
  return (
    <svg
      aria-hidden="true"
      className="developer-icon"
      viewBox="0 0 48 48"
    >
      <path
        d="M24 6a12 12 0 0 0-12 12v5.5A7.5 7.5 0 0 0 8 30v2a7.5 7.5 0 0 0 7.5 7.5H19V42h10v-2.5h3.5A7.5 7.5 0 0 0 40 32v-2a7.5 7.5 0 0 0-4-6.5V18A12 12 0 0 0 24 6Z"
      />
      <path d="M18 25h.01M30 25h.01M18 32h12M24 6v-3M15 9l-2-2M33 9l2-2" />
    </svg>
  );
}


function DeveloperSection() {
  return (
    <section
      className="developer-section"
      aria-labelledby="developer-heading"
    >
      <div className="developer-card">
        <div className="developer-heading">
          <div className="developer-icon-wrap">
            <DeveloperIcon />
          </div>

          <div>
            <p className="eyebrow">Project creator</p>
            <h2 id="developer-heading">Meet the Developer</h2>
          </div>
        </div>

        <div className="developer-intro">
          <div>
            <h3>Anshuman Pattanayak</h3>
            <p className="developer-title">AI &amp; ML Expert</p>
            <p className="developer-subtitle">
              Artificial Intelligence Specialist
            </p>
          </div>

          <dl className="developer-details">
            <div>
              <dt>University</dt>
              <dd>Centurion University BBSR</dd>
            </div>
            <div>
              <dt>Education</dt>
              <dd>B.Tech 4th Year</dd>
            </div>
          </dl>
        </div>

        <p className="developer-description">
          Passionate about building AI-powered solutions that solve real-world
          problems. This project combines Natural Language Processing, Machine
          Learning, semantic analysis, and full-stack development to help job
          seekers evaluate resumes, identify skill gaps, and improve their
          career opportunities.
        </p>

        <div className="developer-technologies">
          <h3>Built with</h3>
          <ul aria-label="Project technologies" className="technology-badges">
            {TECHNOLOGIES.map((technology) => (
              <li key={technology}>{technology}</li>
            ))}
          </ul>
        </div>

        <div className="developer-actions">
          <a
            className="primary-button developer-email-link"
            href="mailto:anshumanpattanayak931@gmail.com"
          >
            Email Me
          </a>
          <a
            className="secondary-button developer-github-link"
            href="https://github.com/ItsAnshumanPattanayak"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub Profile
          </a>
        </div>
      </div>
    </section>
  );
}


export default DeveloperSection;
