import apiClient, { fetchAll } from "./client";
import type { Stock } from "../types";

export function getStock(): Promise<Stock[]> {
  return fetchAll<Stock>("/stocks/");
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
