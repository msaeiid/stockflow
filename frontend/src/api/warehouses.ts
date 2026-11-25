import { fetchAll } from "./client";
import type { Warehouse } from "../types";

export function getWarehouses(): Promise<Warehouse[]> {
  return fetchAll<Warehouse>("/warehouses/");
}
