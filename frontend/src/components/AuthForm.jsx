import { useState } from "react";

import { useAuth } from "../context/useAuth";


function AuthForm() {
  const {
    login,
    register,
    authLoading,
    authError,
    clearAuthError,
  } = useAuth();

  const [mode, setMode] =
    useState("login");

  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [formError, setFormError] =
    useState("");


  function changeMode(nextMode) {
    setMode(nextMode);
    setFormError("");
    clearAuthError();
  }


  async function handleSubmit(event) {
    event.preventDefault();

    setFormError("");
    clearAuthError();

    const cleanedName =
      name.trim();

    const cleanedEmail =
      email.trim().toLowerCase();

    if (
      mode === "register" &&
      cleanedName.length < 2
    ) {
      setFormError(
        "Please enter a valid name.",
      );
      return;
    }

    if (!cleanedEmail) {
      setFormError(
        "Please enter your email.",
      );
      return;
    }

    if (password.length < 8) {
      setFormError(
        "Password must contain at least 8 characters.",
      );
      return;
    }

    try {
      if (mode === "register") {
        await register({
          name: cleanedName,
          email: cleanedEmail,
          password,
        });
      } else {
        await login({
          email: cleanedEmail,
          password,
        });
      }
    } catch {
      // Authentication errors are displayed
      // through AuthContext.
    }
  }


  return (
    <div className="auth-page">
      <section className="auth-panel">
        <div className="auth-brand">
          <span className="brand-mark">
            RA
          </span>

          <div>
            <strong>
              Resume Analyzer
            </strong>

            <small>
              Secure AI career analysis
            </small>
          </div>
        </div>

        <div className="auth-heading">
          <p className="eyebrow">
            {mode === "login"
              ? "Welcome back"
              : "Create your account"}
          </p>

          <h1>
            {mode === "login"
              ? "Sign in to continue"
              : "Start analyzing your resume"}
          </h1>

          <p>
            Your saved reports are private
            and connected to your account.
          </p>
        </div>

        <div
          className="auth-tabs"
          role="tablist"
          aria-label="Authentication mode"
        >
          <button
            type="button"
            role="tab"
            aria-selected={
              mode === "login"
            }
            aria-label="Show login form"
            className={
              mode === "login"
                ? "auth-tab auth-tab-active"
                : "auth-tab"
            }
            onClick={() =>
              changeMode("login")
            }
            disabled={authLoading}
          >
            Login
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={
              mode === "register"
            }
            aria-label="Show registration form"
            className={
              mode === "register"
                ? "auth-tab auth-tab-active"
                : "auth-tab"
            }
            onClick={() =>
              changeMode("register")
            }
            disabled={authLoading}
          >
            Register
          </button>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          {mode === "register" && (
            <>
              <label
                className="field-label"
                htmlFor="auth-name"
              >
                Name
              </label>

              <input
                id="auth-name"
                type="text"
                value={name}
                onChange={(event) =>
                  setName(
                    event.target.value,
                  )
                }
                autoComplete="name"
                disabled={authLoading}
                placeholder="Your full name"
              />
            </>
          )}

          <label
            className="field-label"
            htmlFor="auth-email"
          >
            Email
          </label>

          <input
            id="auth-email"
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value,
              )
            }
            autoComplete="email"
            disabled={authLoading}
            placeholder="you@example.com"
          />

          <label
            className="field-label"
            htmlFor="auth-password"
          >
            Password
          </label>

          <input
            id="auth-password"
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value,
              )
            }
            autoComplete={
              mode === "login"
                ? "current-password"
                : "new-password"
            }
            disabled={authLoading}
            placeholder="Minimum 8 characters"
          />

          {(formError || authError) && (
            <div
              className="form-error"
              role="alert"
            >
              {formError || authError}
            </div>
          )}

          <button
            className="primary-button"
            type="submit"
            disabled={authLoading}
          >
            {authLoading
              ? "Please wait..."
              : mode === "login"
                ? "Login"
                : "Create account"}
          </button>
        </form>

        <p className="privacy-note">
          Access tokens are stored locally
          in this browser during development.
        </p>
      </section>
    </div>
  );
}


export default AuthForm;