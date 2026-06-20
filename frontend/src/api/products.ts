import apiClient from "./clients";
import type { Product } from "../types";

export async function getProducts(): Promise<Product[]> {
  const response = await apiClient.get<{ results: Product[] }>("/products/");
  return response.data.results;
}
