import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import RoleRecommendations from "./RoleRecommendations";


const explainableRecommendations = {
  recommended_roles: [
    {
      role: "Backend Developer",
      overall_match_percentage: 70.67,
      recommendation_level: "Good fit",
      skill_match_percentage: 66.67,
      semantic_match_percentage: 80,
      role_description: "Build backend services.",
      reason: "Legacy reason.",
      explanation:
        "Your resume matches 2 of 3 skills associated with this role.",
      matched_skills: ["Python", "FastAPI"],
      missing_skills: ["Docker"],
      strengths: ["Relevant skills include Python and FastAPI."],
      improvement_areas: ["Consider strengthening Docker."],
      score_components: {
        exact_skill_coverage: {
          score: 66.67,
          weight: 0.7,
          weighted_score: 46.67,
        },
        semantic_similarity: {
          score: 80,
          weight: 0.3,
          weighted_score: 24,
        },
        final_score: { score: 70.67 },
      },
    },
  ],
};


describe("RoleRecommendations", () => {
  it("renders explainable role fields and an accessible breakdown", async () => {
    const user = userEvent.setup();
    render(
      <RoleRecommendations
        recommendations={explainableRecommendations}
      />,
    );

    expect(screen.getAllByText("70.67%")).toHaveLength(2);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Docker")).toBeInTheDocument();
    expect(
      screen.getByText(/matches 2 of 3 skills/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Strengths")).toBeInTheDocument();
    expect(screen.getByText("Improvement areas")).toBeInTheDocument();

    await user.click(
      screen.getByText(/view score breakdown for backend developer/i),
    );

    expect(screen.getByText("Exact skill coverage")).toBeInTheDocument();
    expect(screen.getByText("66.67% × 0.7 = 46.67")).toBeInTheDocument();
    expect(screen.getByText("Final score")).toBeInTheDocument();
  });

  it("uses legacy fields when optional explanation fields are absent", () => {
    render(
      <RoleRecommendations
        recommendations={{
          recommended_roles: [
            {
              role: "Data Analyst",
              overall_match_percentage: 50,
              recommendation_level: "Potential fit",
              skill_match_percentage: 50,
              semantic_match_percentage: 50,
              role_description: "Analyze data.",
              reason: "Legacy response remains visible.",
            },
          ],
        }}
      />,
    );

    expect(
      screen.getByText("Legacy response remains visible."),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/view score breakdown/i),
    ).not.toBeInTheDocument();
  });
});
