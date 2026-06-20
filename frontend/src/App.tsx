import { useEffect, useState } from "react";
import { getProducts } from "./api/products";
import { isAuthenticated, logout } from "./api/auth";
import Login from "./pages/Login";
import type { Product } from "./types";
import StockPage from "./pages/StockPage";

function App() {
  const [authed, setAuthed] = useState(isAuthenticated());
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"products" | "stock">("products");

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
        <div>
          <button onClick={() => setView(view === "products" ? "stock" : "products")}
            style={{ marginRight: 8 }}>
            {view === "products" ? "Go to Stock" : "Go to Products"}
          </button>
          <button onClick={() => { logout(); setAuthed(false); }}>Log out</button>
        </div>
      </div>
      {view === "products" && (
        <>
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
        </>
      )}
      {view === "stock" && <StockPage />}
    </div>
  );
}

export default App;
