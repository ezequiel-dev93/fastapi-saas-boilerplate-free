"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import type { AuthContextType, AuthMode, AuthUser } from "./types";
import { setTokenProvider } from "../api/client";
import { env } from "../config/env";
import { createCognitoUserManager } from "./cognito-client";

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const authMode: AuthMode =
    env.NEXT_PUBLIC_ENVIRONMENT === "production" || env.NEXT_PUBLIC_COGNITO_USER_POOL_ID
      ? "cognito"
      : "dev";

  useEffect(() => {
    // Sync token with client
    const storedToken = localStorage.getItem("saas_access_token");
    const storedUser = localStorage.getItem("saas_auth_user");

    if (storedToken) {
      setToken(storedToken);
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch {
          // ignore parsing error
        }
      }
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    setTokenProvider(() => token);
  }, [token]);

  const loginWithDevToken = async (email: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${env.NEXT_PUBLIC_API_URL}/api/v1/auth/dev-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Dev login failed");
      }

      const data = await res.json();
      const accessToken = data.access_token;
      const devUser: AuthUser = {
        id: data.user?.id,
        email: data.user?.email,
        first_name: data.user?.first_name,
        last_name: data.user?.last_name,
        cognito_sub: data.user?.cognito_sub,
      };

      setToken(accessToken);
      setUser(devUser);
      localStorage.setItem("saas_access_token", accessToken);
      localStorage.setItem("saas_auth_user", JSON.stringify(devUser));
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithCognito = async () => {
    const userManager = createCognitoUserManager();
    if (userManager) {
      await userManager.signinRedirect();
    } else {
      console.warn("Cognito User Pool is not configured in environment variables.");
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("saas_access_token");
    localStorage.removeItem("saas_auth_user");
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token,
        authMode,
        loginWithDevToken,
        loginWithCognito,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
