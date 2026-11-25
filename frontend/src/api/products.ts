import { fetchAll } from "./client";
import type { Product } from "../types";

export function getProducts(params: { is_active?: boolean } = {}): Promise<Product[]> {
  return fetchAll<Product>("/products/", params);
}
