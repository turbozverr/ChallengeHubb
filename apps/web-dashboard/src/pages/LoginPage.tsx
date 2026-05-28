import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@challengehub.dev");
  const [password, setPassword] = useState("12345");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await login(email, password);
      if (user.role === "ADMIN") navigate("/app/admin");
      else if (user.role === "MODERATOR") navigate("/app/moderation");
      else navigate("/app/business");
    } catch (e) {
      const message = e instanceof Error ? e.message : "Помилка авторизації";
      setError(message === "Invalid credentials" ? "Невірний email або пароль" : message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 400, margin: "40px auto", padding: 30 }}>
        <h1 className="text-center">Вхід у ChallengeHub</h1>
        <p className="muted text-center">admin/moderator/business@challengehub.dev 12345</p>
        <form className="column" onSubmit={handleSubmit}>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Пароль" type="password" />
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={loading} style={{ marginTop: 12 }}>
            {loading ? "Вхід..." : "Увійти"}
          </button>
        </form>
    </div>
  );
}
