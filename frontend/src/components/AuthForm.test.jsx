import {
  render,
  screen,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  expect,
  test,
  vi,
} from "vitest";

import AuthForm from "./AuthForm";
import { useAuth } from "../context/useAuth";


vi.mock("../context/useAuth", () => ({
  useAuth: vi.fn(),
}));


const login = vi.fn();
const register = vi.fn();
const clearAuthError = vi.fn();


beforeEach(() => {
  vi.clearAllMocks();

  useAuth.mockReturnValue({
    login,
    register,
    authLoading: false,
    authError: "",
    clearAuthError,
  });
});


test(
  "submits valid login credentials",
  async () => {
    const user = userEvent.setup();

    render(<AuthForm />);

    await user.type(
      screen.getByLabelText(/email/i),
      "test@example.com",
    );

    await user.type(
      screen.getByLabelText(/password/i),
      "StrongPassword123",
    );

    await user.click(
      screen.getByRole("button", {
        name: /^login$/i,
      }),
    );

    expect(login).toHaveBeenCalledWith({
      email: "test@example.com",
      password: "StrongPassword123",
    });

    expect(login).toHaveBeenCalledTimes(1);

    expect(register).not.toHaveBeenCalled();
  },
);


test(
  "shows validation error for short password",
  async () => {
    const user = userEvent.setup();

    render(<AuthForm />);

    await user.type(
      screen.getByLabelText(/email/i),
      "test@example.com",
    );

    await user.type(
      screen.getByLabelText(/password/i),
      "short",
    );

    await user.click(
      screen.getByRole("button", {
        name: /^login$/i,
      }),
    );

    expect(
      screen.getByRole("alert"),
    ).toHaveTextContent(
      "Password must contain at least 8 characters.",
    );

    expect(login).not.toHaveBeenCalled();
    expect(register).not.toHaveBeenCalled();
  },
);


test(
  "registers a new user",
  async () => {
    const user = userEvent.setup();

    render(<AuthForm />);

    await user.click(
      screen.getByRole("tab", {
        name: /show registration form/i,
      }),
    );

    expect(
      screen.getByRole("tab", {
        name: /show registration form/i,
      }),
    ).toHaveAttribute(
      "aria-selected",
      "true",
    );

    await user.type(
      screen.getByLabelText(/^name$/i),
      "New User",
    );

    await user.type(
      screen.getByLabelText(/email/i),
      "new@example.com",
    );

    await user.type(
      screen.getByLabelText(/password/i),
      "StrongPassword123",
    );

    await user.click(
      screen.getByRole("button", {
        name: /create account/i,
      }),
    );

    expect(register).toHaveBeenCalledWith({
      name: "New User",
      email: "new@example.com",
      password: "StrongPassword123",
    });

    expect(register).toHaveBeenCalledTimes(1);

    expect(login).not.toHaveBeenCalled();
  },
);