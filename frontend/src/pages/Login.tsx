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
    <div className="card login-container">
      <h1>StockFlow</h1>
      <p className="muted-text">Sign in to continue</p>
      <input
        className="input login-input"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        className="input login-input login-input-last"
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
      />
      {error && <p className="error-text">{error}</p>}
      <button className="btn login-submit" onClick={handleSubmit} disabled={loading}>
        {loading ? "Signing in…" : "Sign in"}
      </button>
    </div>
  );
}

export default Login;
