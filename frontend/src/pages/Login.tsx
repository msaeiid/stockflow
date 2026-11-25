import { useEffect, useState } from "react";
import { login } from "../api/auth";
import { getDemoInfo, type DemoInfo } from "../api/demo";

interface LoginProps {
  onSuccess: () => void;
}

function Login({ onSuccess }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demo, setDemo] = useState<DemoInfo | null>(null);

  useEffect(() => {
    // Public demo: show the shared login when the server allows it.
    getDemoInfo()
      .then(setDemo)
      .catch(() => setDemo(null));
  }, []);

  async function handleSubmit() {
    if (!username || !password) {
      setError("Enter your username and password.");
      return;
    }
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
      {demo?.demo_mode && demo.username && demo.password && (
        <div className="demo-hint">
          Public demo — sign in as <code>{demo.username}</code> / <code>{demo.password}</code>. Data
          is reset every night.{" "}
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setUsername(demo.username ?? "");
              setPassword(demo.password ?? "");
            }}
          >
            Fill in
          </button>
        </div>
      )}
      <input
        className="input login-input"
        placeholder="Username"
        aria-label="Username"
        autoComplete="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        className="input login-input login-input-last"
        type="password"
        placeholder="Password"
        aria-label="Password"
        autoComplete="current-password"
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
