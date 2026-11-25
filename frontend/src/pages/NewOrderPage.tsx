import { useEffect, useState } from "react";
import { getProducts } from "../api/products";
import { getWarehouses } from "../api/warehouses";
import { createOrder, type OrderLine } from "../api/orders";
import { extractError } from "../api/errors";
import type { Product, Warehouse } from "../types";

function NewOrderPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseId, setWarehouseId] = useState<number | null>(null);
  const [customer, setCustomer] = useState("");
  const [lines, setLines] = useState<OrderLine[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

  useEffect(() => {
    Promise.all([getProducts({ is_active: true }), getWarehouses()])
      .then(([productList, warehouseList]) => {
        setProducts(productList);
        setWarehouses(warehouseList);
        if (warehouseList[0]) setWarehouseId(warehouseList[0].id);
      })
      .catch(() => setMessage({ text: "Failed to load products or warehouses.", ok: false }));
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
    if (!warehouseId || !customer.trim() || lines.length === 0) {
      setMessage({ text: "Fill customer, warehouse, and at least one item.", ok: false });
      return;
    }
    if (lines.some((line) => !Number.isInteger(line.quantity) || line.quantity < 1)) {
      setMessage({ text: "Each quantity must be a whole number of at least 1.", ok: false });
      return;
    }
    setSubmitting(true);
    try {
      await createOrder({ warehouse: warehouseId, customer_name: customer.trim(), items: lines });
      setMessage({ text: "Order created successfully.", ok: true });
      setLines([]);
      setCustomer("");
    } catch (err) {
      setMessage({ text: extractError(err), ok: false });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h2>New order</h2>
      <div className="order-header">
        <input
          className="input"
          placeholder="Customer name"
          aria-label="Customer name"
          value={customer}
          maxLength={150}
          onChange={(e) => setCustomer(e.target.value)}
        />
        <select
          className="select"
          aria-label="Warehouse"
          value={warehouseId ?? ""}
          onChange={(e) => setWarehouseId(Number(e.target.value))}
        >
          {warehouses.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
      </div>

      {lines.map((line, i) => (
        <div key={i} className="order-line">
          <select
            className="select order-line-product"
            aria-label={`Product for line ${i + 1}`}
            value={line.product}
            onChange={(e) => updateLine(i, "product", Number(e.target.value))}
          >
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input
            className="input order-line-qty"
            type="number"
            min={1}
            aria-label={`Quantity for line ${i + 1}`}
            value={line.quantity}
            onChange={(e) => updateLine(i, "quantity", Number(e.target.value))}
          />
          <button className="btn btn-secondary" onClick={() => removeLine(i)}>
            Remove
          </button>
        </div>
      ))}

      <div className="order-actions">
        <button className="btn btn-secondary" onClick={addLine} disabled={!products.length}>
          + Add item
        </button>
        <button className="btn" onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Submitting…" : "Submit order"}
        </button>
      </div>

      {message && (
        <p className={message.ok ? "status-message status-ok" : "status-message error-text"}>
          {message.text}
        </p>
      )}
    </div>
  );
}

export default NewOrderPage;
