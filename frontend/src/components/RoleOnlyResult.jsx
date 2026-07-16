import RoleRecommendations from "./RoleRecommendations";

function RoleOnlyResult({ result }) {
  if (!result) {
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
            {result.recommendations
              ?.total_candidate_skills || 0}{" "}
            skills detected
          </span>

          <span>
            {result.recommendations
              ?.roles_evaluated || 0}{" "}
            roles evaluated
          </span>
        </div>
      </section>

      <RoleRecommendations
        recommendations={result.recommendations}
      />
    </div>
  );
}

export default RoleOnlyResult;