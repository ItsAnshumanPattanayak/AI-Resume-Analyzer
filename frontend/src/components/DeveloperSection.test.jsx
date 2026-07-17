import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import DeveloperSection from "./DeveloperSection";


test("renders the developer profile and verified project technologies", () => {
  render(<DeveloperSection />);

  expect(screen.getByText("Anshuman Pattanayak")).toBeInTheDocument();
  expect(screen.getByText("FastAPI")).toBeInTheDocument();
  expect(screen.getByText("Sentence Transformers")).toBeInTheDocument();
  expect(screen.getByText("JWT Authentication")).toBeInTheDocument();
});


test("provides accessible developer contact links", () => {
  render(<DeveloperSection />);

  expect(screen.getByRole("link", { name: "Email Me" })).toHaveAttribute(
    "href",
    "mailto:anshumanpattanayak931@gmail.com",
  );

  expect(screen.getByRole("link", { name: "GitHub Profile" })).toHaveAttribute(
    "href",
    "https://github.com/ItsAnshumanPattanayak",
  );
});
