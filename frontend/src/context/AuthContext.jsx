import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const cached = localStorage.getItem("nextweet_user");
    return cached ? JSON.parse(cached) : null;
  });
  const [loading, setLoading] = useState(true);

  const refreshMe = useCallback(async () => {
    const token = localStorage.getItem("nextweet_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const res = await api.get("/auth/me");
      setUser(res.data);
      localStorage.setItem("nextweet_user", JSON.stringify(res.data));
    } catch {
      localStorage.removeItem("nextweet_token");
      localStorage.removeItem("nextweet_user");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshMe();
  }, [refreshMe]);

  const login = async (identifier, password) => {
    const res = await api.post("/auth/login", { username: identifier, password });
    localStorage.setItem("nextweet_token", res.data.token);
    localStorage.setItem("nextweet_user", JSON.stringify(res.data.user));
    setUser(res.data.user);
    return res.data.user;
  };

  const register = async (payload) => {
    const res = await api.post("/auth/register", payload);
    localStorage.setItem("nextweet_token", res.data.token);
    localStorage.setItem("nextweet_user", JSON.stringify(res.data.user));
    setUser(res.data.user);
    return res.data.user;
  };

  const logout = () => {
    localStorage.removeItem("nextweet_token");
    localStorage.removeItem("nextweet_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, register, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
