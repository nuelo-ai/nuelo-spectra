"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import { AdminUser, AdminLoginResponse } from "@/types/admin-auth";
import {
  adminApiClient,
  setAdminToken,
  getAdminToken,
  clearAdminToken,
} from "@/lib/admin-api-client";

interface AdminAuthContextType {
  user: AdminUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(
  undefined
);

export function AdminAuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const fetchMe = useCallback(async (): Promise<AdminUser | null> => {
    try {
      const response = await adminApiClient.get("/api/admin/auth/me");
      if (!response.ok) {
        return null;
      }
      return await response.json();
    } catch {
      return null;
    }
  }, []);

  // On mount: verify existing session
  useEffect(() => {
    const token = getAdminToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    fetchMe().then((adminUser) => {
      if (adminUser) {
        setUser(adminUser);
      } else {
        clearAdminToken();
      }
      setIsLoading(false);
    });
  }, [fetchMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await adminApiClient.post("/api/admin/auth/login", {
        email,
        password,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || "Login failed. Please check your credentials."
        );
      }

      const data: AdminLoginResponse = await response.json();
      setAdminToken(data.access_token);

      // Fetch user profile after login
      const adminUser = await fetchMe();
      if (adminUser) {
        setUser(adminUser);
      }
    },
    [fetchMe]
  );

  const logout = useCallback(() => {
    clearAdminToken();
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AdminAuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth(): AdminAuthContextType {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error("useAdminAuth must be used within an AdminAuthProvider");
  }
  return context;
}
