import apiClient from "./client";



export interface DashboardStats {
    total_products: number;
    low_stock_count: number;
    inventory_value: number;
    top_products: { name: string; quantity: number }[];
}

export async function getStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>("/dashboard/stats");
    return response.data;
}
