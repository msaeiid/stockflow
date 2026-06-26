import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { getStats, type DashboardStats } from "../api/dashboard";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => setError("Failed to load dashboard."));
  }, []);

  if (error) return <p className="error-text">{error}</p>;
  if (!stats) return <p>Loading…</p>;

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="stats-grid">
        <StatCard label="Active products" value={stats.total_products} />
        <StatCard label="Low stock items" value={stats.low_stock_count} />
        <StatCard label="Inventory value" value={`$${Number(stats.inventory_value).toLocaleString()}`} />
      </div>

      <h3>Top products by quantity</h3>
      <div className="chart-wrap">
        <ResponsiveContainer>
          <BarChart data={stats.top_products}>
            <XAxis dataKey="name" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="quantity" fill="#3266ad" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default Dashboard;
