import { useEffect, useState } from "react";
import { getProducts } from "../api/products";
import { getStock } from "../api/stocks";
import { createOrder, type OrderLine } from "../api/orders";
import { extractError } from "../api/errors";
import type { Product } from "../types";

function NewOrderPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouseId, setWarehouseId] = useState<number | null>(null);
  const [customer, setCustomer] = useState("");
  const [lines, setLines] = useState<OrderLine[]>([]);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

  useEffect(() => {
    getProducts().then(setProducts);
    getStock().then((s) => { if (s[0]) setWarehouseId(s[0].warehouse); });
  }, []);

  function addLine() {
    if (products[0]) setLines([...lines, { product: products[0].id, quantity: 1 }]);
  }
  function updateLine(i: number, field: keyof OrderLine, value: number) {
    const next = [...lines];
    next[i] = { ...next[i], [field]: value };
    setLines(next);
  }
  function removeLine(i: number) {
    setLines(lines.filter((_, idx) => idx !== i));
  }

  async function handleSubmit() {
    setMessage(null);
    if (!warehouseId || !customer || lines.length === 0) {
      setMessage({ text: "Fill customer, warehouse, and at least one item.", ok: false });
      return;
    }
    try {
      await createOrder({ warehouse: warehouseId, customer_name: customer, items: lines });
      setMessage({ text: "Order created successfully.", ok: true });
      setLines([]);
      setCustomer("");
    } catch (err) {
      setMessage({ text: extractError(err), ok: false });
    }
  }

  return (
    <div>
      <h2>New order</h2>
      <input className="input" placeholder="Customer name" value={customer}
        onChange={(e) => setCustomer(e.target.value)} style={{ maxWidth: 320, marginBottom: 16 }} />

      {lines.map((line, i) => (
        <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
          <select className="select" value={line.product} style={{ maxWidth: 240 }}
            onChange={(e) => updateLine(i, "product", Number(e.target.value))}>
            {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <input className="input" type="number" min={1} value={line.quantity} style={{ width: 80 }}
            onChange={(e) => updateLine(i, "quantity", Number(e.target.value))} />
          <button className="btn btn-secondary" onClick={() => removeLine(i)}>Remove</button>
        </div>
      ))}

      <div style={{ margin: "16px 0", display: "flex", gap: 8 }}>
        <button className="btn btn-secondary" onClick={addLine}>+ Add item</button>
        <button className="btn" onClick={handleSubmit}>Submit order</button>
      </div>

      {message && (
        <p style={{ color: message.ok ? "var(--color-success)" : "var(--color-danger)" }}>
          {message.text}
        </p>
      )}
    </div>
  );
}

export default NewOrderPage;
