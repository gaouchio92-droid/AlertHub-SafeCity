/* eslint-disable react-refresh/only-export-components */
import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react';

import { CurrentUser, getCurrentUser, login as loginRequest } from '../services/api';

const TOKEN_KEY = 'alerthub-access-token';

type AuthContextValue = {
  user: CurrentUser | null;
  isLoading: boolean;
  isAdmin: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (!window.localStorage.getItem(TOKEN_KEY)) {
        setIsLoading(false);
        return;
      }
      try {
        setUser(await getCurrentUser());
      } catch {
        window.localStorage.removeItem(TOKEN_KEY);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    void loadUser();
  }, []);

  const value = useMemo<AuthContextValue>(() => {
    async function login(username: string, password: string) {
      const token = await loginRequest({ username, password });
      window.localStorage.setItem(TOKEN_KEY, token.access_token);
      setUser(await getCurrentUser());
    }

    function logout() {
      window.localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    }

    return {
      user,
      isLoading,
      isAdmin: Boolean(user?.permissions.includes('settings:admin')),
      login,
      logout,
    };
  }, [isLoading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
