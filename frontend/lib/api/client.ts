/**
 * Axios API client with automatic JWT injection and token refresh.
 */

import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ---------------------------------------------------------------------------
// Request interceptor: inject access token
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // We import lazily to avoid circular deps with the store
    const token =
      typeof window !== "undefined"
        ? (() => {
            try {
              const raw = localStorage.getItem("auth-storage");
              if (!raw) return null;
              const parsed = JSON.parse(raw);
              return parsed?.state?.accessToken ?? null;
            } catch {
              return null;
            }
          })()
        : null;

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// Response interceptor: handle 401 → refresh → retry
// ---------------------------------------------------------------------------
let isRefreshing = false;
let refreshQueue: Array<{
  resolve: (value: string) => void;
  reject: (reason?: unknown) => void;
}> = [];

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue the request until refresh completes
        return new Promise<string>((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const raw =
          typeof window !== "undefined"
            ? localStorage.getItem("auth-storage")
            : null;
        const refreshToken = raw
          ? JSON.parse(raw)?.state?.refreshToken
          : null;

        if (!refreshToken) throw new Error("No refresh token");

        const res = await axios.post<{
          access_token: string;
          refresh_token: string;
        }>(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newAccessToken = res.data.access_token;

        // Update store
        const authStorage = localStorage.getItem("auth-storage");
        if (authStorage) {
          const parsed = JSON.parse(authStorage);
          parsed.state.accessToken = newAccessToken;
          parsed.state.refreshToken = res.data.refresh_token;
          localStorage.setItem("auth-storage", JSON.stringify(parsed));
        }

        // Flush queue
        refreshQueue.forEach((q) => q.resolve(newAccessToken));
        refreshQueue = [];

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        refreshQueue.forEach((q) => q.reject(error));
        refreshQueue = [];

        // Redirect to login
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);