
import apiClient from "./clients";

interface TokenResponse {
  access: string;
  refresh: string;
}

export async function login(username: string, password: string): Promise<void> {
  const response = await apiClient.post<TokenResponse>("/auth/login/", {
    username,
    password,
  });
  localStorage.setItem("access", response.data.access);
  localStorage.setItem("refresh", response.data.refresh);
}

export function logout(): void {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem("access");
}
