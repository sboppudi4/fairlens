import axios, { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/authStore";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
  // Send the httpOnly cookies set by /api/v1/auth/* endpoints.
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---- Refresh-token logic --------------------------------------------------
// On the first 401 for a request, attempt a single refresh-token round trip.
// While the refresh is in flight, queue subsequent failed requests so we don't
// hammer the server with parallel refreshes.

let refreshPromise: Promise<string | null> | null = null;

async function attemptRefresh(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  refreshPromise = axios
    .post<{ access_token: string; refresh_token?: string | null }>(
      `${baseURL}/api/v1/auth/refresh`,
      { refresh_token: refreshToken },
      { withCredentials: true },
    )
    .then((r) => {
      useAuthStore.getState().setToken(r.data.access_token, r.data.refresh_token ?? null);
      return r.data.access_token;
    })
    .catch(() => null)
    .finally(() => {
      refreshPromise = null;
    });
  return refreshPromise;
}

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

api.interceptors.response.use(
  (resp) => resp,
  async (error: AxiosError<{ detail?: string }>) => {
    const cfg = error.config as RetriableConfig | undefined;
    const isAuthCall =
      cfg?.url?.includes("/auth/login") ||
      cfg?.url?.includes("/auth/register") ||
      cfg?.url?.includes("/auth/refresh");

    if (error.response?.status === 401 && cfg && !cfg._retried && !isAuthCall) {
      const fresh = await attemptRefresh();
      if (fresh) {
        cfg._retried = true;
        cfg.headers = cfg.headers ?? {};
        cfg.headers.Authorization = `Bearer ${fresh}`;
        return api.request(cfg as AxiosRequestConfig);
      }
      useAuthStore.getState().clear();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export function extractErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  const axerr = err as AxiosError<{ detail?: string | Array<{ msg?: string }> }>;
  const detail = axerr.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return axerr.message || fallback;
}
