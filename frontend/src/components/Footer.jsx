const QUICK_LINKS = [
  { label: "Home", href: "#main-content" },
  { label: "Analyze Resume", href: "#analysis-workflow", mode: "analyze" },
  { label: "Role Recommendations", href: "#analysis-results", mode: "roles" },
  { label: "Resume Improvement", href: "#analysis-results", mode: "improve" },
  { label: "Analysis History", href: "#analysis-history" },
];


function Footer({ onModeChange }) {
  function handleQuickLinkClick(event, mode) {
    if (!mode) {
      return;
    }

    const targetHash = event.currentTarget.hash;

    onModeChange(mode);

    window.setTimeout(() => {
      document.querySelector(targetHash)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 0);
  }

  return (
    <footer className="project-footer">
      <div className="project-footer-grid">
        <section aria-labelledby="footer-project-heading">
          <h2 id="footer-project-heading">AI Resume Analyzer</h2>
          <p>
            An AI-powered resume analysis and career guidance platform. Analyze
            resumes, compare them with job descriptions, discover missing
            skills, receive ATS insights, and get role recommendations.
          </p>
        </section>

        <nav aria-label="Quick links">
          <h2>Quick Links</h2>
          <ul>
            {QUICK_LINKS.map((link) => (
              <li key={link.label}>
                <a
                  href={link.href}
                  onClick={(event) => handleQuickLinkClick(event, link.mode)}
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <address aria-labelledby="footer-contact-heading">
          <h2 id="footer-contact-heading">Contact Developer</h2>
          <p>Anshuman Pattanayak</p>
          <p>AI &amp; ML Expert</p>
          <p>Centurion University BBSR</p>
          <p>B.Tech 4th Year</p>
          <a href="mailto:anshumanpattanayak931@gmail.com">
            anshumanpattanayak931@gmail.com
          </a>
          <a
            href="https://github.com/ItsAnshumanPattanayak"
            target="_blank"
            rel="noopener noreferrer"
          >
            ItsAnshumanPattanayak
          </a>
        </address>
      </div>

      <div className="project-footer-bottom">
        <p>Created by Anshuman Pattanayak</p>
        <p>© 2026 AI Resume Analyzer. All rights reserved.</p>
        <p>
          Have questions, suggestions, or want to collaborate? Feel free to
          reach out!
        </p>
      </div>
    </footer>
  );
}


export default Footer;
