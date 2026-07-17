import {
  useCallback,
  useEffect,
  useState,
} from "react";

import AnalysisHistory from "./components/AnalysisHistory";
import AnalysisModeTabs from "./components/AnalysisModeTabs";
import AuthForm from "./components/AuthForm";
import DeveloperSection from "./components/DeveloperSection";
import Footer from "./components/Footer";
import ImprovementOnlyResult from "./components/ImprovementOnlyResult";
import ParsedResumeResult from "./components/ParsedResumeResult";
import ResumeForm from "./components/ResumeForm";
import RoleOnlyResult from "./components/RoleOnlyResult";
import UserHeader from "./components/UserHeader";
import { useAuth } from "./context/useAuth";
import Dashboard from "./pages/Dashboard";
import {
  analyzeResume,
  deleteAnalysisHistory,
  getAnalysisHistory,
  getAnalysisHistoryDetail,
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


const VALID_ANALYSIS_MODES = new Set([
  "analyze",
  "parse",
  "roles",
  "improve",
]);


function App() {
  const {
    isAuthenticated,
    authLoading,
    logout,
  } = useAuth();

  const [activeMode, setActiveMode] =
    useState("analyze");

  const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [requestError, setRequestError] =
    useState("");

  const [historyRecords, setHistoryRecords] =
    useState([]);

  const [historyLoading, setHistoryLoading] =
    useState(false);

  const [historyError, setHistoryError] =
    useState("");


  const handleUnauthorized =
    useCallback((error) => {
      const message =
        error?.message || "";

      const unauthorized =
        message.includes(
          "Authentication is required",
        ) ||
        message.includes(
          "Invalid or expired access token",
        ) ||
        message.includes(
          "does not exist or is inactive",
        );

      if (unauthorized) {
        logout();
      }

      return unauthorized;
    }, [logout]);


  const loadHistory =
    useCallback(async () => {
      if (!isAuthenticated) {
        setHistoryRecords([]);
        return;
      }

      setHistoryLoading(true);
      setHistoryError("");

      try {
        const records =
          await getAnalysisHistory(
            20,
            0,
          );

        setHistoryRecords(records);
      } catch (error) {
        if (!handleUnauthorized(error)) {
          setHistoryError(
            error.message ||
              "Could not load analysis history.",
          );
        }
      } finally {
        setHistoryLoading(false);
      }
    }, [
      isAuthenticated,
      handleUnauthorized,
    ]);


  useEffect(() => {
    if (!isAuthenticated) {
      return undefined;
    }

    const timeoutId =
      window.setTimeout(() => {
        void loadHistory();
      }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [
    isAuthenticated,
    loadHistory,
  ]);


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
          response = await parseResume(
            resumeFile,
          );
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

      await loadHistory();

      window.setTimeout(() => {
        document
          .getElementById(
            "analysis-results",
          )
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);
    } catch (error) {
      if (!handleUnauthorized(error)) {
        setRequestError(
          error.message ||
            "The requested analysis failed.",
        );
      }
    } finally {
      setLoading(false);
    }
  }


  async function handleOpenHistory(
    recordId,
  ) {
    setRequestError("");

    try {
      const record =
        await getAnalysisHistoryDetail(
          recordId,
        );

      const savedMode =
        VALID_ANALYSIS_MODES.has(
          record.analysis_type,
        )
          ? record.analysis_type
          : "analyze";

      setActiveMode(savedMode);
      setResult(record.result_data);

      window.setTimeout(() => {
        document
          .getElementById(
            "analysis-results",
          )
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);
    } catch (error) {
      if (!handleUnauthorized(error)) {
        setRequestError(
          error.message ||
            "Could not open the saved report.",
        );
      }
    }
  }


  async function handleDeleteHistory(
    recordId,
  ) {
    const confirmed =
      window.confirm(
        "Delete this saved analysis report?",
      );

    if (!confirmed) {
      return;
    }

    setHistoryError("");

    try {
      await deleteAnalysisHistory(
        recordId,
      );

      setHistoryRecords(
        (currentRecords) =>
          currentRecords.filter(
            (record) =>
              record.id !== recordId,
          ),
      );
    } catch (error) {
      if (!handleUnauthorized(error)) {
        setHistoryError(
          error.message ||
            "Could not delete the saved report.",
        );
      }
    }
  }


  function renderResult() {
    switch (activeMode) {
      case "parse":
        return (
          <ParsedResumeResult
            result={result}
          />
        );

      case "roles":
        return (
          <RoleOnlyResult
            result={result}
          />
        );

      case "improve":
        return (
          <ImprovementOnlyResult
            result={result}
          />
        );

      case "analyze":
      default:
        return (
          <Dashboard result={result} />
        );
    }
  }


  if (authLoading) {
    return (
      <div className="auth-loading-page">
        <div className="spinner" />

        <p>
          Restoring your session...
        </p>
      </div>
    );
  }


  if (!isAuthenticated) {
    return <AuthForm />;
  }


  return (
    <div className="app-shell">
      <UserHeader />

      <main id="main-content">
        <section className="hero hero-compact">
          <div className="hero-copy">
            <p className="eyebrow">
              AI + NLP + Machine Learning
            </p>

            <h1>
              Improve your resume with
              explainable AI analysis.
            </h1>

            <p>
              Parse candidate information,
              compare a resume with a job,
              identify suitable roles and
              receive writing recommendations.
            </p>

            <div className="feature-pills">
              <span>
                ATS compatibility
              </span>

              <span>
                Semantic matching
              </span>

              <span>
                Skill-gap detection
              </span>

              <span>
                Private history
              </span>
            </div>
          </div>

          <ResumeForm
            mode={activeMode}
            onSubmit={handleSubmit}
            loading={loading}
          />
        </section>

        <div id="analysis-workflow">
          <AnalysisModeTabs
            activeMode={activeMode}
            onModeChange={
              handleModeChange
            }
            disabled={loading}
          />
        </div>

        {loading && (
          <section
            className="loading-card"
            aria-live="polite"
          >
            <div className="spinner" />

            <div>
              <h2>
                Processing your resume
              </h2>

              <p>
                {
                  MODE_LOADING_MESSAGES[
                    activeMode
                  ]
                }
              </p>
            </div>
          </section>
        )}

        {requestError && (
          <section
            className="request-error"
            role="alert"
          >
            <strong>
              Request failed
            </strong>

            <p>{requestError}</p>
          </section>
        )}

        <div id="analysis-results">
          {renderResult()}
        </div>

        <div id="analysis-history">
          <AnalysisHistory
            records={historyRecords}
            loading={historyLoading}
            error={historyError}
            onOpen={handleOpenHistory}
            onDelete={
              handleDeleteHistory
            }
            onRefresh={loadHistory}
          />
        </div>

        <DeveloperSection />
      </main>

      <Footer onModeChange={handleModeChange} />
    </div>
  );
}


export default App;
