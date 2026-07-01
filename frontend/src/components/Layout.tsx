import { Link, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";

function Layout() {
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div>
      <nav className="top-nav">
        <strong className="brand">StockFlow</strong>
        <Link to="/products">Products</Link>
        <Link to="/stock">Stock</Link>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/orders/new">New order</Link>
        <button className="btn btn-secondary" onClick={handleLogout}>Log out</button>
      </nav>
      <main className="page-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
