import ImprovementPanel from "../components/ImprovementPanel";
import RoleRecommendations from "../components/RoleRecommendations";
import ScoreCard from "../components/ScoreCard";
import SkillsPanel from "../components/SkillsPanel";

function CandidateDetails({ candidate }) {
  if (!candidate) {
    return null;
  }

  const allSkills = candidate.skills?.all || [];

  return (
    <section className="candidate-card">
      <div>
        <p className="eyebrow">Candidate</p>
        <h2>{candidate.name || "Name not detected"}</h2>
      </div>

      <div className="candidate-details">
        <span>{candidate.email || "Email not detected"}</span>
        <span>{candidate.phone || "Phone not detected"}</span>
        <span>{allSkills.length} skills detected</span>
      </div>
    </section>
  );
}

function Dashboard({ result }) {
  if (!result) {
    return null;
  }

  const ats = result.ats || {};
  const similarity = result.job_match?.similarity || {};
  const skills = result.job_match?.skills;
  const roles = result.job_role_recommendations;
  const improvement = result.resume_improvement;

  return (
    <div className="dashboard">
      <CandidateDetails candidate={result.candidate} />

      <section className="score-grid">
        <ScoreCard
          title="ATS compatibility"
          value={ats.overall_score}
          description={ats.rating}
        />

        <ScoreCard
          title="Combined similarity"
          value={similarity.combined_percentage}
          description="TF-IDF and semantic similarity"
        />

        <ScoreCard
          title="Semantic similarity"
          value={similarity.semantic_percentage}
          description="Meaning-based transformer comparison"
        />

        <ScoreCard
          title="Skill match"
          value={skills?.skill_match_percentage}
          description="Detected job skills in your resume"
        />
      </section>

      <SkillsPanel skillData={skills} />

      <RoleRecommendations recommendations={roles} />

      <ImprovementPanel improvement={improvement} />

      {ats.recommendations?.length > 0 && (
        <section className="result-section">
          <div className="section-heading">
            <div>
              <p className="eyebrow">ATS advice</p>
              <h2>Compatibility recommendations</h2>
            </div>
          </div>

          <ul className="ats-recommendations">
            {ats.recommendations.map((recommendation) => (
              <li key={recommendation}>
                {recommendation}
              </li>
            ))}
          </ul>

          <p className="disclaimer">{ats.disclaimer}</p>
        </section>
      )}
    </div>
  );
}

export default Dashboard;