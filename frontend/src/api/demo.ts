import apiClient from "./client";

export interface DemoInfo {
  demo_mode: boolean;
  username: string | null;
  password: string | null;
}

export async function getDemoInfo(): Promise<DemoInfo> {
  const response = await apiClient.get<DemoInfo>("/demo/");
  return response.data;
}
