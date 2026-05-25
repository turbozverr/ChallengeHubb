import { Link } from "react-router-dom";

export function ForbiddenPage() {
  return (
    <div className="card">
      <h1>403</h1>
      <p>Недостатньо прав доступу до цього розділу.</p>
      <Link to="/app">Повернутися до системи</Link>
    </div>
  );
}
