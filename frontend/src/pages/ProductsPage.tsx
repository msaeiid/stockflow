import { useEffect, useState } from "react";
import { getProducts } from "../api/products";
import type { Product } from "../types";

function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProducts()
      .then(setProducts)
      .catch(() => setError("Failed to load products."));
  }, []);

  return (
    <div>
      <h2>Products</h2>
      {error && <p className="error-text">{error}</p>}
      <table className="table">
        <thead>
          <tr>
            <th align="left">Name</th><th align="left">SKU</th>
            <th align="left">Category</th><th align="right">Price</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td>{p.name}</td><td>{p.sku}</td>
              <td>{p.category_name}</td><td align="right">${p.sale_price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ProductsPage;
