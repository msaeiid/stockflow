export interface Product {
  id: number;
  name: string;
  sku: string;
  description: string;
  category: number;
  category_name: string;
  supplier: number | null;
  supplier_name: string | null;
  cost_price: string;
  sale_price: string;
  reorder_threshold: number;
  is_active: boolean;
  created_at: string;
}

export interface Stock {
  id: number;
  product: number;
  product_name: string;
  warehouse: number;
  warehouse_name: string;
  quantity: number;
  is_low: boolean;
}
