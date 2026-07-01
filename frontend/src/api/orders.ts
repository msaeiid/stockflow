import apiClient from "./client";

export interface OrderLine {
  product: number;
  quantity: number;
}

export async function createOrder(payload: {
  warehouse: number;
  customer_name: string;
  items: OrderLine[];
}): Promise<void> {
  await apiClient.post("/orders/", payload);
}
