import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

// Same origin by default: in production Django serves this app and the API
// from one host; in development Vite proxies /api to the backend
// (vite.config.ts). Set VITE_API_URL only when the API lives elsewhere.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) return null;
  try {
    const response = await axios.post<{ access: string }>(
      `${apiClient.defaults.baseURL}/auth/refresh/`,
      { refresh },
    );
    localStorage.setItem("access", response.data.access);
    return response.data.access;
  } catch {
    return null;
  }
}

function sendToLogin(): void {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

// An expired access token is refreshed once; if that fails the session is over.
apiClient.interceptors.response.use(undefined, async (error: AxiosError) => {
  const original = error.config as
    (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
  const isAuthCall = original?.url?.startsWith("/auth/");
  if (error.response?.status !== 401 || !original || original._retried || isAuthCall) {
    throw error;
  }
  original._retried = true;
  refreshing ??= refreshAccessToken().finally(() => {
    refreshing = null;
  });
  const token = await refreshing;
  if (!token) {
    sendToLogin();
    throw error;
  }
  original.headers.Authorization = `Bearer ${token}`;
  return apiClient(original);
});

interface Page<T> {
  next: string | null;
  results: T[];
}

/** Read every page of a paginated DRF list (or a plain array response). */
export async function fetchAll<T>(url: string, params: Record<string, unknown> = {}): Promise<T[]> {
  const items: T[] = [];
  for (let page = 1; ; page++) {
    const response = await apiClient.get<Page<T> | T[]>(url, { params: { ...params, page } });
    if (Array.isArray(response.data)) return response.data;
    items.push(...response.data.results);
    if (!response.data.next) return items;
  }
}

export default apiClient;
