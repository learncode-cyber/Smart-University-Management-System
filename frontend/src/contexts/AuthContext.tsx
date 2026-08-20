import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiClient, loginRequest, logoutRequest } from "@/lib/apiClient";
import { getRefreshToken, setAccessToken } from "@/lib/tokenStore";
import type { CurrentUser } from "@/types/api";

interface AuthContextValue {
  user: CurrentUser | null;
  isLoading: boolean; // true only during the initial session-restore check
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: CurrentUser) => void; // lets ProfilePage sync topbar/sidebar after an edit, without a full session refetch
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On first load, if a refresh token exists in storage, silently try to
  // restore the session (get a fresh access token, then fetch /users/me)
  // rather than forcing a re-login on every page refresh.
  useEffect(() => {
    async function restoreSession() {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        setIsLoading(false);
        return;
      }
      try {
        const response = await apiClient.post<{ access_token: string }>("/auth/refresh", {
          refresh_token: refreshToken,
        });
        setAccessToken(response.data.access_token);
        const me = await apiClient.get<CurrentUser>("/users/me");
        setUser(me.data);
      } catch {
        // refresh token invalid/expired — just land on the login page,
        // no error banner needed for this silent, expected case
      } finally {
        setIsLoading(false);
      }
    }
    restoreSession();
  }, []);

  async function login(email: string, password: string) {
    await loginRequest(email, password);
    const me = await apiClient.get<CurrentUser>("/users/me");
    setUser(me.data);
  }

  async function logout() {
    await logoutRequest();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
