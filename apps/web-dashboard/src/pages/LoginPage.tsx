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
      setError(e instanceof Error ? e.message : "Помилка авторизації");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h1>Вхід у ChallengeHub WebSystem</h1>
      <p className="muted">admin/moderator/business@challengehub.dev | 12345</p>
      <form className="column" onSubmit={handleSubmit}>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Пароль" type="password" />
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={loading}>{loading ? "Вхід..." : "Увійти"}</button>
      </form>
    </div>
  );
}
