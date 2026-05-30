import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { AuthUser, WebRole } from "./types";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  initialized: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const rawUser = localStorage.getItem("ch_user");
    const rawToken = localStorage.getItem("ch_token");
    if (rawUser && rawToken) {
      setUser(JSON.parse(rawUser) as AuthUser);
      setToken(rawToken);
    }
    setInitialized(true);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      initialized,
      login: async (email: string, password: string) => {
        const response = await api.login(email, password);
        const mappedUser: AuthUser = {
          id: response.user.id,
          fullName: response.user.full_name,
          email: response.user.email,
          role: response.user.role as WebRole
        };
        setUser(mappedUser);
        setToken(response.access_token);
        localStorage.setItem("ch_user", JSON.stringify(mappedUser));
        localStorage.setItem("ch_token", response.access_token);
        return mappedUser;
      },
      logout: () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem("ch_user");
        localStorage.removeItem("ch_token");
      }
    }),
    [initialized, user, token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
