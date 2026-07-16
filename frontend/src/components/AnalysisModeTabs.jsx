const ANALYSIS_MODES = [
  {
    id: "analyze",
    title: "Full Analysis",
    description: "Compare your resume with a job description.",
  },
  {
    id: "parse",
    title: "Parse Resume",
    description: "Extract contact details, skills and sections.",
  },
  {
    id: "roles",
    title: "Recommend Roles",
    description: "Find suitable job roles using your resume.",
  },
  {
    id: "improve",
    title: "Improve Resume",
    description: "Check writing quality and resume structure.",
  },
];

function AnalysisModeTabs({
  activeMode,
  onModeChange,
  disabled = false,
}) {
  return (
    <section className="mode-selector">
      <div className="mode-selector-heading">
        <p className="eyebrow">Choose workflow</p>
        <h2>What would you like to analyze?</h2>
      </div>

      <div
        className="mode-tabs"
        role="tablist"
        aria-label="Resume analysis modes"
      >
        {ANALYSIS_MODES.map((mode) => {
          const isActive = activeMode === mode.id;

          return (
            <button
              key={mode.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={
                isActive
                  ? "mode-tab mode-tab-active"
                  : "mode-tab"
              }
              onClick={() => onModeChange(mode.id)}
              disabled={disabled}
            >
              <strong>{mode.title}</strong>
              <span>{mode.description}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

export default AnalysisModeTabs;