import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  expect,
  test,
  vi,
} from "vitest";

import ResumeForm from "./ResumeForm";

test("requires a resume before submission", async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();

  render(
    <ResumeForm
      mode="parse"
      onSubmit={onSubmit}
      loading={false}
    />,
  );

  await user.click(
    screen.getByRole("button", {
      name: /parse resume/i,
    }),
  );

  expect(
    screen.getByRole("alert"),
  ).toHaveTextContent(
    "Please select a PDF or DOCX resume.",
  );

  expect(onSubmit).not.toHaveBeenCalled();
});

test("shows job description only in analysis mode", () => {
  const { rerender } = render(
    <ResumeForm
      mode="parse"
      onSubmit={vi.fn()}
      loading={false}
    />,
  );

  expect(
    screen.queryByLabelText(/job description/i),
  ).not.toBeInTheDocument();

  rerender(
    <ResumeForm
      mode="analyze"
      onSubmit={vi.fn()}
      loading={false}
    />,
  );

  expect(
    screen.getByLabelText(/job description/i),
  ).toBeInTheDocument();
});

test("prevents duplicate submissions while a request is pending", async () => {
  let finishRequest;
  const onSubmit = vi.fn(
    () => new Promise((resolve) => {
      finishRequest = resolve;
    }),
  );

  render(
    <ResumeForm
      mode="parse"
      onSubmit={onSubmit}
      loading={false}
    />,
  );

  const resume = new File(
    ["resume"],
    "resume.pdf",
    { type: "application/pdf" },
  );
  fireEvent.change(
    screen.getByLabelText("Resume"),
    { target: { files: [resume] } },
  );

  const form = screen
    .getByRole("button", { name: /parse resume/i })
    .closest("form");
  fireEvent.submit(form);
  fireEvent.submit(form);

  expect(onSubmit).toHaveBeenCalledTimes(1);
  finishRequest();
});
