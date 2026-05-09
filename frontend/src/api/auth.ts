import { api } from "./client";
import type { TokenResponse, User } from "@/types";

export async function register(email: string, password: string, full_name: string) {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/register", { email, password, full_name });
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/login", { email, password });
  return data;
}

export async function getMe() {
  const { data } = await api.get<User>("/api/v1/auth/me");
  return data;
}

export const fetchMe = getMe;

export async function logout(): Promise<void> {
  await api.post("/api/v1/auth/logout");
}

export async function refreshToken(refreshToken: string) {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/refresh", {
    refresh_token: refreshToken,
  });
  return data;
}
