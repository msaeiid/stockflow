import apiClient from "./client";
import type { Product } from "../types";

export async function getProducts(): Promise<Product[]> {
  const response = await apiClient.get<Product[] | { results?: Product[] }>("/products/");

  if (Array.isArray(response.data)) {
    return response.data;
  }

  return response.data.results ?? [];
}
