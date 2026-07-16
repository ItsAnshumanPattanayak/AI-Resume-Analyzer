import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getCurrentUser,
  loginUser,
  registerUser,
  TOKEN_STORAGE_KEY,
} from "../services/api";
import AuthContext from "./auth-context";


export function AuthProvider({
  children,
}) {
  const [user, setUser] = useState(null);

  const [authLoading, setAuthLoading] =
    useState(true);

  const [authError, setAuthError] =
    useState("");


  const restoreSession =
    useCallback(async () => {
      const token =
        window.localStorage.getItem(
          TOKEN_STORAGE_KEY,
        );

      if (!token) {
        setAuthLoading(false);
        return;
      }

      try {
        const currentUser =
          await getCurrentUser();

        setUser(currentUser);
      } catch {
        window.localStorage.removeItem(
          TOKEN_STORAGE_KEY,
        );

        setUser(null);
      } finally {
        setAuthLoading(false);
      }
    }, []);


  useEffect(() => {
    const timeoutId =
      window.setTimeout(() => {
        void restoreSession();
      }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [restoreSession]);


  const login = useCallback(
    async (credentials) => {
      setAuthLoading(true);
      setAuthError("");

      try {
        const response =
          await loginUser(credentials);

        window.localStorage.setItem(
          TOKEN_STORAGE_KEY,
          response.access_token,
        );

        setUser(response.user);

        return response.user;
      } catch (error) {
        setAuthError(
          error.message ||
            "Login failed.",
        );

        throw error;
      } finally {
        setAuthLoading(false);
      }
    },
    [],
  );


  const register = useCallback(
    async (details) => {
      setAuthLoading(true);
      setAuthError("");

      try {
        await registerUser(details);

        const userData = await login({
          email: details.email,
          password: details.password,
        });

        return userData;
      } catch (error) {
        setAuthError(
          error.message ||
            "Registration failed.",
        );

        throw error;
      } finally {
        setAuthLoading(false);
      }
    },
    [login],
  );


  const logout = useCallback(() => {
    window.localStorage.removeItem(
      TOKEN_STORAGE_KEY,
    );

    setUser(null);
    setAuthError("");
  }, []);


  const clearAuthError =
    useCallback(() => {
      setAuthError("");
    }, []);


  const contextValue = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      authLoading,
      authError,
      login,
      register,
      logout,
      clearAuthError,
    }),
    [
      user,
      authLoading,
      authError,
      login,
      register,
      logout,
      clearAuthError,
    ],
  );


  return (
    <AuthContext.Provider
      value={contextValue}
    >
      {children}
    </AuthContext.Provider>
  );
}