import { Link, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";

function Layout() {
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div style={{ fontFamily: "system-ui" }}>
      <nav style={{
        display: "flex", gap: 16, alignItems: "center",
        padding: "12px 24px", borderBottom: "1px solid #ddd",
      }}>
        <strong style={{ marginRight: "auto" }}>StockFlow</strong>
        <Link to="/products">Products</Link>
        <Link to="/stock">Stock</Link>
        <button onClick={handleLogout}>Log out</button>
      </nav>
      <main style={{ padding: 24 }}>
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
