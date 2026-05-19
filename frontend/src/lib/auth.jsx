import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, formatApiError } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null=checking, false=anon, {}=user
  const [loading, setLoading] = useState(true);
  const [twoFactorChallenge, setTwoFactor] = useState(null);

  const hydrate = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setUser(false);
      setLoading(false);
      return null;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
      return data;
    } catch {
      localStorage.removeItem("token");
      setUser(false);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // If returning from Google OAuth (hash session_id), let AuthCallback handle it.
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return;
    }
    hydrate();
  }, [hydrate]);

  const login = async (email, password) => {
    try {
      const { data } = await api.post("/auth/login", { email, password });
      if (data.requires_2fa) {
        return { ok: false, requires_2fa: true, challenge_token: data.challenge_token };
      }
      localStorage.setItem("token", data.token);
      setUser(data.user);
      return { ok: true, user: data.user };
    } catch (e) {
      return { ok: false, error: formatApiError(e.response?.data?.detail) || e.message };
    }
  };

  const register = async (email, password, role) => {
    try {
      const { data } = await api.post("/auth/register", { email, password, role });
      localStorage.setItem("token", data.token);
      setUser(data.user);
      return { ok: true, user: data.user };
    } catch (e) {
      return { ok: false, error: formatApiError(e.response?.data?.detail) || e.message };
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(false);
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, hydrate, twoFactorChallenge, setTwoFactor }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
