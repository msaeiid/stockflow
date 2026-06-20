import apiClient from "./client";
import type { Stock } from "../types";

export async function getStock(): Promise<Stock[]> {
  const response = await apiClient.get<Stock[]>("/stocks/");
  return response.data;
}

export interface MovementPayload {
  product: number;
  warehouse: number;
  movement_type: "IN" | "OUT";
  quantity: number;
}

export async function createMovement(payload: MovementPayload): Promise<void> {
  await apiClient.post("/movements/", payload);
}
