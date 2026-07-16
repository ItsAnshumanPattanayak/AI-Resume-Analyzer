import { useState } from "react";

import ResumeForm from "./components/ResumeForm";
import Dashboard from "./pages/Dashboard";
import { analyzeResume } from "./services/api";

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState("");

  async function handleAnalyze(resumeFile, jobDescription) {
    setLoading(true);
    setRequestError("");
    setAnalysisResult(null);

    try {
      const result = await analyzeResume(
        resumeFile,
        jobDescription,
      );

      setAnalysisResult(result);

      window.setTimeout(() => {
        document
          .getElementById("analysis-results")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);
    } catch (error) {
      setRequestError(
        error.message || "Resume analysis failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/">
          <span className="brand-mark">RA</span>

          <div>
            <strong>Resume Analyzer</strong>
            <small>AI-powered career analysis</small>
          </div>
        </a>

        <span className="status-badge">
          Phase 8 frontend
        </span>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">AI + NLP + Machine Learning</p>

            <h1>
              Understand how well your resume matches the job.
            </h1>

            <p>
              Analyze ATS compatibility, missing skills, semantic
              alignment, suitable job roles and resume-writing
              quality in one report.
            </p>

            <div className="feature-pills">
              <span>PDF and DOCX parsing</span>
              <span>Transformer matching</span>
              <span>Skill-gap detection</span>
              <span>Role recommendations</span>
            </div>
          </div>

          <ResumeForm
            onAnalyze={handleAnalyze}
            loading={loading}
          />
        </section>

        {loading && (
          <section className="loading-card" aria-live="polite">
            <div className="spinner" />
            <div>
              <h2>Analyzing your resume</h2>
              <p>
                Extracting details, generating embeddings and
                calculating compatibility scores.
              </p>
            </div>
          </section>
        )}

        {requestError && (
          <section className="request-error" role="alert">
            <strong>Analysis failed</strong>
            <p>{requestError}</p>
          </section>
        )}

        <div id="analysis-results">
          <Dashboard result={analysisResult} />
        </div>
      </main>

      <footer>
        <p>
          AI Resume Analyzer — custom scores are intended for
          guidance and do not represent a specific employer’s ATS.
        </p>
      </footer>
    </div>
  );
}

export default App;