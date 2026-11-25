import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import ProductsPage from "./pages/ProductsPage";
import StockPage from "./pages/StockPage";

// The dashboard pulls in the charting library: load it only when visited.
const Dashboard = lazy(() => import("./pages/Dashboard"));
import NewOrderPage from "./pages/NewOrderPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={<Login onSuccess={() => (window.location.href = "/products")} />}
        />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/stock" element={<StockPage />} />
            <Route
              path="/dashboard"
              element={
                <Suspense fallback={<p>Loading…</p>}>
                  <Dashboard />
                </Suspense>
              }
            />
            <Route path="/orders/new" element={<NewOrderPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/products" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
