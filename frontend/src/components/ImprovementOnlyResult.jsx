import ImprovementPanel from "./ImprovementPanel";
import ScoreCard from "./ScoreCard";

function ImprovementOnlyResult({ result }) {
  const improvement =
    result?.resume_improvement;

  if (!improvement) {
    return null;
  }

  return (
    <div className="dashboard">
      <section className="candidate-card">
        <div>
          <p className="eyebrow">Candidate</p>
          <h2>
            {result.candidate?.name ||
              "Name not detected"}
          </h2>
        </div>

        <div className="candidate-details">
          <span>
            {result.resume_statistics?.word_count || 0}{" "}
            words
          </span>
          <span>
            {result.candidate?.skills
              ?.total_detected || 0}{" "}
            skills
          </span>
        </div>
      </section>

      <section className="score-grid single-score-grid">
        <ScoreCard
          title="Resume quality"
          value={improvement.quality_score}
          description={improvement.quality_rating}
        />

        <ScoreCard
          title="Section completion"
          value={
            improvement.section_analysis
              ?.section_completion_percentage
          }
          description="Expected sections detected"
        />

        <ScoreCard
          title="Action verb usage"
          value={
            improvement.action_verb_analysis
              ?.action_verb_percentage
          }
          description="Strong openings in content lines"
        />

        <ScoreCard
          title="Summary quality"
          value={
            improvement.summary_analysis?.score
          }
          description={
            improvement.summary_analysis?.present
              ? "Professional summary detected"
              : "Summary not detected"
          }
        />
      </section>

      <ImprovementPanel
        improvement={improvement}
      />
    </div>
  );
}

export default ImprovementOnlyResult;