import { useState } from "react";

import AnalysisModeTabs from "./components/AnalysisModeTabs";
import ImprovementOnlyResult from "./components/ImprovementOnlyResult";
import ParsedResumeResult from "./components/ParsedResumeResult";
import ResumeForm from "./components/ResumeForm";
import RoleOnlyResult from "./components/RoleOnlyResult";
import Dashboard from "./pages/Dashboard";
import {
  analyzeResume,
  improveResume,
  parseResume,
  recommendRoles,
} from "./services/api";

const MODE_LOADING_MESSAGES = {
  analyze:
    "Extracting details, generating embeddings and calculating compatibility scores.",
  parse:
    "Extracting candidate information, skills and resume sections.",
  roles:
    "Comparing your resume with predefined technical career profiles.",
  improve:
    "Reviewing resume structure, language, action verbs and achievements.",
};

function App() {
  const [activeMode, setActiveMode] =
    useState("analyze");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] =
    useState("");

  function handleModeChange(nextMode) {
    setActiveMode(nextMode);
    setResult(null);
    setRequestError("");
  }

  async function handleSubmit({
    resumeFile,
    jobDescription,
    topN,
  }) {
    setLoading(true);
    setRequestError("");
    setResult(null);

    try {
      let response;

      switch (activeMode) {
        case "parse":
          response = await parseResume(resumeFile);
          break;

        case "roles":
          response = await recommendRoles(
            resumeFile,
            topN,
          );
          break;

        case "improve":
          response = await improveResume(
            resumeFile,
          );
          break;

        case "analyze":
        default:
          response = await analyzeResume(
            resumeFile,
            jobDescription,
          );
          break;
      }

      setResult(response);

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
        error.message ||
          "The requested analysis failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  function renderResult() {
    switch (activeMode) {
      case "parse":
        return (
          <ParsedResumeResult result={result} />
        );

      case "roles":
        return (
          <RoleOnlyResult result={result} />
        );

      case "improve":
        return (
          <ImprovementOnlyResult
            result={result}
          />
        );

      case "analyze":
      default:
        return <Dashboard result={result} />;
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/">
          <span className="brand-mark">RA</span>

          <div>
            <strong>Resume Analyzer</strong>
            <small>
              AI-powered career analysis
            </small>
          </div>
        </a>

        <span className="status-badge">
          Backend connected
        </span>
      </header>

      <main>
        <section className="hero hero-compact">
          <div className="hero-copy">
            <p className="eyebrow">
              AI + NLP + Machine Learning
            </p>

            <h1>
              Improve your resume with explainable
              AI analysis.
            </h1>

            <p>
              Parse candidate information, compare a
              resume with a job, identify suitable roles
              and receive writing recommendations.
            </p>

            <div className="feature-pills">
              <span>ATS compatibility</span>
              <span>Semantic matching</span>
              <span>Skill-gap detection</span>
              <span>Career recommendations</span>
            </div>
          </div>

          <ResumeForm
            mode={activeMode}
            onSubmit={handleSubmit}
            loading={loading}
          />
        </section>

        <AnalysisModeTabs
          activeMode={activeMode}
          onModeChange={handleModeChange}
          disabled={loading}
        />

        {loading && (
          <section
            className="loading-card"
            aria-live="polite"
          >
            <div className="spinner" />

            <div>
              <h2>Processing your resume</h2>

              <p>
                {MODE_LOADING_MESSAGES[activeMode]}
              </p>
            </div>
          </section>
        )}

        {requestError && (
          <section
            className="request-error"
            role="alert"
          >
            <strong>Request failed</strong>
            <p>{requestError}</p>
          </section>
        )}

        <div id="analysis-results">
          {renderResult()}
        </div>
      </main>

      <footer>
        <p>
          Scores are custom guidance metrics and do not
          represent a specific employer’s ATS.
        </p>
      </footer>
    </div>
  );
}

export default App;