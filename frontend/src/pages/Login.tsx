import { useState } from "react";
import { login } from "../api/auth";

interface LoginProps {
  onSuccess: () => void;
}

function Login({ onSuccess }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      onSuccess();
    } catch {
      setError("Invalid username or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 320, margin: "80px auto", fontFamily: "system-ui" }}>
      <h1>StockFlow</h1>
      <p style={{ color: "#666" }}>Sign in to continue</p>
      <input
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        style={{ display: "block", width: "100%", padding: 8, marginBottom: 8 }}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        style={{ display: "block", width: "100%", padding: 8, marginBottom: 12 }}
      />
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      <button onClick={handleSubmit} disabled={loading} style={{ width: "100%", padding: 10 }}>
        {loading ? "Signing in…" : "Sign in"}
      </button>
    </div>
  );
}

export default Login;
