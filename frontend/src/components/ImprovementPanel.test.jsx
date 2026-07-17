import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import ImprovementPanel from "./ImprovementPanel";


const improvement = {
  quality_score: 62,
  quality_rating: "Needs improvement",
  priority_recommendations: [],
  weak_phrases: [],
  bullet_point_templates: [],
  overall_feedback_summary: "The feedback highlights evidence opportunities.",
  priority_actions: [
    {
      id: "bullet-01-quantification",
      priority: "medium",
      category: "quantification",
      action: "Add a measured result if you have one.",
    },
  ],
  section_feedback: [
    {
      section_name: "projects",
      detected: true,
      strengths: ["Projects is clearly labeled."],
      issues: [],
      suggestions: [],
    },
  ],
  bullet_feedback: [
    {
      id: "bullet-01",
      section_name: "projects",
      evidence: "Worked on an API.",
      issues: [
        {
          id: "bullet-01-weak-opening",
          message: "Clarify the contribution without overstating ownership.",
        },
      ],
    },
  ],
};


describe("ImprovementPanel", () => {
  it("renders advanced feedback with expandable details", async () => {
    const user = userEvent.setup();
    render(<ImprovementPanel improvement={improvement} />);

    expect(screen.getByText("Feedback summary")).toBeInTheDocument();
    expect(screen.getByText(/Add a measured result/i)).toBeInTheDocument();

    await user.click(screen.getByText(/projects — detected/i));
    expect(screen.getByText("Projects is clearly labeled.")).toBeInTheDocument();

    await user.click(screen.getByText("projects bullet"));
    expect(screen.getByText("Worked on an API.")).toBeInTheDocument();
  });

  it("keeps legacy improvement responses usable", () => {
    render(
      <ImprovementPanel
        improvement={{
          quality_score: 75,
          quality_rating: "Good",
          priority_recommendations: [],
          weak_phrases: [],
          bullet_point_templates: [],
        }}
      />,
    );

    expect(screen.getByText(/No major resume-quality issues/i)).toBeInTheDocument();
    expect(screen.queryByText("Feedback summary")).not.toBeInTheDocument();
  });
});
