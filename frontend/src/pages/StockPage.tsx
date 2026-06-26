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
    <div>
      <h2>Stock levels</h2>
      <table className="table stock-table">
        <thead>
          <tr>
            <th align="left">Product</th><th align="left">Warehouse</th>
            <th align="right">Quantity</th><th align="left">Status</th><th></th>
          </tr>
        </thead>
        <tbody>
          {stock.map((s) => (
            <tr key={s.id}>
              <td>{s.product_name}</td>
              <td>{s.warehouse_name}</td>
              <td align="right">{s.quantity}</td>
              <td>{s.is_low ? <span className="badge-low">Low</span> : <span className="badge-ok">OK</span>}</td>
              <td><button className="btn btn-secondary" onClick={() => setSelected(s)}>Select</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && (
        <div className="card movement-card">
          <h3>Record movement</h3>
          <p className="muted-text">
            {selected.product_name} @ {selected.warehouse_name} (current: {selected.quantity})
          </p>
          <div className="movement-controls">
            <select
              className="select movement-select"
              value={type}
              onChange={(e) => setType(e.target.value as "IN" | "OUT")}
            >
              <option value="IN">Stock In</option>
              <option value="OUT">Stock Out</option>
            </select>
            <input
              className="input movement-qty"
              type="number"
              min={1}
              value={qty}
              onChange={(e) => setQty(Number(e.target.value))}
            />
            <button className="btn" onClick={handleSubmit}>Submit</button>
          </div>
          {message && (
            <p className={message.ok ? "status-message status-ok" : "status-message error-text"}>
              {message.text}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default StockPage;
