import axios, { AxiosError } from "axios";
import { useAuthStore } from "@/store/authStore";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clear();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export function extractErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  const axerr = err as AxiosError<{ detail?: string | Array<{ msg?: string }> }>;
  const detail = axerr.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return axerr.message || fallback;
}
