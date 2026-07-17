import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";

import Footer from "./Footer";


test("renders project, contact, and existing workflow quick links", () => {
  render(<Footer onModeChange={vi.fn()} />);

  expect(screen.getByText("AI Resume Analyzer")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Analyze Resume" })).toHaveAttribute(
    "href",
    "#analysis-workflow",
  );
  expect(screen.getByRole("link", { name: "Analysis History" })).toHaveAttribute(
    "href",
    "#analysis-history",
  );
  expect(screen.getByRole("link", { name: "ItsAnshumanPattanayak" })).toHaveAttribute(
    "href",
    "https://github.com/ItsAnshumanPattanayak",
  );
});


test("uses existing analysis modes for relevant quick links", async () => {
  const user = userEvent.setup();
  const onModeChange = vi.fn();
  render(<Footer onModeChange={onModeChange} />);

  await user.click(screen.getByRole("link", { name: "Resume Improvement" }));

  expect(onModeChange).toHaveBeenCalledWith("improve");
});
