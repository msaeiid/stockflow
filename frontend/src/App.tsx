import { useEffect, useState } from "react";
import { getProducts } from "./api/products";
import { isAuthenticated, logout } from "./api/auth";
import Login from "./pages/Login";
import type { Product } from "./types";

function App() {
  const [authed, setAuthed] = useState(isAuthenticated());
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authed) return;
    getProducts()
      .then(setProducts)
      .catch(() => setError("Failed to load products."));
  }, [authed]);

  if (!authed) return <Login onSuccess={() => setAuthed(true)} />;

  return (
    <div style={{ padding: 24, fontFamily: "system-ui" }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h1>StockFlow — Products</h1>
        <button onClick={() => { logout(); setAuthed(false); }}>Log out</button>
      </div>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      <table cellPadding={8} style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Name</th><th align="left">SKU</th>
            <th align="left">Category</th><th align="right">Price</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id} style={{ borderTop: "1px solid #ddd" }}>
              <td>{p.name}</td><td>{p.sku}</td>
              <td>{p.category_name}</td><td align="right">${p.sale_price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
