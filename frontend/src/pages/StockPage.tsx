import { useEffect, useState } from "react";
import { getStock, createMovement } from "../api/stocks";
import { extractError } from "../api/errors";
import type { Stock } from "../types/index";

function StockPage() {
  const [stock, setStock] = useState<Stock[]>([]);
  const [selected, setSelected] = useState<Stock | null>(null);
  const [type, setType] = useState<"IN" | "OUT">("IN");
  const [qty, setQty] = useState(1);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

  async function loadStock() {
    try {
      setStock(await getStock());
    } catch {
      setMessage({ text: "Failed to load stock.", ok: false });
    }
  }

  useEffect(() => {
    loadStock();
  }, []);

  async function handleSubmit() {
    if (!selected) return;
    setMessage(null);
    try {
      await createMovement({
        product: selected.product,
        warehouse: selected.warehouse,
        movement_type: type,
        quantity: qty,
      });
      setMessage({ text: "Movement recorded successfully.", ok: true });
      await loadStock();
    } catch (err) {
      setMessage({ text: extractError(err), ok: false });
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: "system-ui" }}>
      <h2>Stock levels</h2>
      <table cellPadding={8} style={{ borderCollapse: "collapse", marginBottom: 24 }}>
        <thead>
          <tr>
            <th align="left">Product</th><th align="left">Warehouse</th>
            <th align="right">Quantity</th><th align="left">Status</th><th></th>
          </tr>
        </thead>
        <tbody>
          {stock.map((s) => (
            <tr key={s.id} style={{ borderTop: "1px solid #ddd" }}>
              <td>{s.product_name}</td>
              <td>{s.warehouse_name}</td>
              <td align="right">{s.quantity}</td>
              <td>{s.is_low ? <span style={{ color: "crimson" }}>Low</span> : "OK"}</td>
              <td><button onClick={() => setSelected(s)}>Select</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && (
        <div style={{ border: "1px solid #ddd", padding: 16, maxWidth: 360 }}>
          <h3>Record movement</h3>
          <p style={{ color: "#666" }}>
            {selected.product_name} @ {selected.warehouse_name} (current: {selected.quantity})
          </p>
          <select value={type} onChange={(e) => setType(e.target.value as "IN" | "OUT")}
            style={{ padding: 8, marginRight: 8 }}>
            <option value="IN">Stock In</option>
            <option value="OUT">Stock Out</option>
          </select>
          <input type="number" min={1} value={qty}
            onChange={(e) => setQty(Number(e.target.value))}
            style={{ padding: 8, width: 80, marginRight: 8 }} />
          <button onClick={handleSubmit}>Submit</button>
          {message && (
            <p style={{ color: message.ok ? "green" : "crimson", marginTop: 12 }}>
              {message.text}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default StockPage;
