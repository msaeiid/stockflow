import { useEffect, useState } from "react";
import { getProducts } from "./api/products";
import type { Product } from "./types";

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProducts()
      .then(setProducts)
      .catch(() => setError("Failed to load products. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ padding: 24 }}>Loading…</p>;
  if (error) return <p style={{ padding: 24, color: "crimson" }}>{error}</p>;

  return (
    <div style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>StockFlow — Products</h1>
      <table cellPadding={8} style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Name</th>
            <th align="left">SKU</th>
            <th align="left">Category</th>
            <th align="right">Price</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id} style={{ borderTop: "1px solid #ddd" }}>
              <td>{p.name}</td>
              <td>{p.sku}</td>
              <td>{p.category_name}</td>
              <td align="right">${p.sale_price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
