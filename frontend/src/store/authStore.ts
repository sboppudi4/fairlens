import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  setAuth: (token: string, user: User, refreshToken?: string | null) => void;
  setToken: (token: string, refreshToken?: string | null) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      setAuth: (token, user, refreshToken = null) =>
        set({ token, user, refreshToken: refreshToken ?? undefined }),
      setToken: (token, refreshToken = null) =>
        set({ token, refreshToken: refreshToken ?? undefined }),
      clear: () => set({ token: null, refreshToken: null, user: null }),
    }),
    { name: "fairlens.auth" },
  ),
);
