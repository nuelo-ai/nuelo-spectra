"use client";

import * as React from "react";
import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient, setTokens, clearTokens, isAuthenticated as checkAuth } from "@/lib/api-client";
import type {
  UserResponse,
  LoginRequest,
  SignupRequest,
  TokenResponse,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from "@/types/auth";

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (
    email: string,
    password: string,
    firstName?: string,
    lastName?: string
  ) => Promise<void>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Auth provider component that manages authentication state.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Load user on mount if tokens exist
  useEffect(() => {
    async function loadUser() {
      if (checkAuth()) {
        try {
          const response = await apiClient.get("/auth/me");
          if (response.ok) {
            const userData: UserResponse = await response.json();
            setUser(userData);
          } else {
            clearTokens();
          }
        } catch (error) {
          clearTokens();
        }
      }
      setIsLoading(false);
    }

    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    const payload: LoginRequest = { email, password };
    const response = await apiClient.post("/auth/login", payload);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    const data: TokenResponse = await response.json();
    setTokens(data.access_token, data.refresh_token);

    // Load user data
    const userResponse = await apiClient.get("/auth/me");
    if (userResponse.ok) {
      const userData: UserResponse = await userResponse.json();
      setUser(userData);
      router.push("/dashboard");
    } else {
      throw new Error("Failed to load user data");
    }
  };

  const signup = async (
    email: string,
    password: string,
    firstName?: string,
    lastName?: string
  ) => {
    const payload: SignupRequest = {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
    };
    const response = await apiClient.post("/auth/signup", payload);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Signup failed");
    }

    const data: TokenResponse = await response.json();
    setTokens(data.access_token, data.refresh_token);

    // Load user data
    const userResponse = await apiClient.get("/auth/me");
    if (userResponse.ok) {
      const userData: UserResponse = await userResponse.json();
      setUser(userData);
      router.push("/dashboard");
    } else {
      throw new Error("Failed to load user data");
    }
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    router.push("/login");
  };

  const forgotPassword = async (email: string) => {
    const payload: ForgotPasswordRequest = { email };
    const response = await apiClient.post("/auth/forgot-password", payload);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to send reset email");
    }
  };

  const resetPassword = async (token: string, newPassword: string) => {
    const payload: ResetPasswordRequest = { token, new_password: newPassword };
    const response = await apiClient.post("/auth/reset-password", payload);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to reset password");
    }
  };

  const value = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    signup,
    logout,
    forgotPassword,
    resetPassword,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access auth context.
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
