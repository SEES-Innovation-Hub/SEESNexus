import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import type { Envelope } from "../types/envelope";
import { tokenStore } from "./tokenStore";

export const api = axios.create({
  baseURL: "/api/v1",
});

api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Every endpoint replies with the {status, message, data} envelope — this
// pulls the payload out so callers work with plain types, not the wrapper.
export async function unwrap<T>(
  request: Promise<AxiosResponse<Envelope<T>>>,
): Promise<T> {
  const { data } = await request;
  return data.data as T;
}

// The backend's own explanation ("Email already registered", …) when the
// error carries one; `fallback` covers network failures and non-envelope errors.
export function errorMessage(error: unknown, fallback: string): string {
  return (
    (axios.isAxiosError<Envelope<unknown>>(error) &&
      error.response?.data?.message) ||
    fallback
  );
}

// True when the server answered 404, e.g. a project link to something deleted.
export function isNotFoundError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404;
}

// Lets the auth context drop its user when the session dies mid-use. A hard
// redirect here would also bounce public pages (Landing) for stale tokens.
let onSessionExpired: (() => void) | null = null;

export function setSessionExpiredHandler(handler: () => void) {
  onSessionExpired = handler;
}

// A 401 from one of these means "wrong credentials" / "bad code", never
// "expired token" — they must never trigger a refresh attempt below.
const UNAUTHENTICATED_PATHS = [
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
  "/notify/",
];

function isUnauthenticatedRequest(url?: string): boolean {
  return !!url && UNAUTHENTICATED_PATHS.some((path) => url.includes(path));
}

// Only one refresh call is ever in flight. Any request that 401s while a
// refresh is already running awaits this same promise instead of firing
// its own — avoids a stampede of parallel refresh calls.
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = tokenStore.getRefresh();
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }
  const { data } = await axios.post<Envelope<{ access_token: string }>>(
    "/api/v1/auth/refresh",
    {
      refresh_token: refreshToken,
    },
  );
  const accessToken = data.data!.access_token;
  tokenStore.setAccess(accessToken);
  return accessToken;
}

type RetryableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableConfig | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isUnauthenticatedRequest(originalRequest.url)
    ) {
      return Promise.reject(error);
    }
    originalRequest._retry = true;

    try {
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
      const accessToken = await refreshPromise;
      originalRequest.headers.set("Authorization", `Bearer ${accessToken}`);
      return api(originalRequest);
    } catch (refreshError) {
      tokenStore.clear();
      onSessionExpired?.();
      return Promise.reject(refreshError);
    }
  },
);
