import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const roleLabels: Record<string, string> = {
  ADMIN: "Адміністратор",
  MODERATOR: "Модератор",
  BUSINESS_CLIENT: "Бізнес-клієнт"
};

export function AppShell() {
  const { user, logout } = useAuth();

  const links =
    user?.role === "ADMIN"
      ? [
          { to: "/app/admin", label: "Панель адміністратора" },
          { to: "/app/moderation", label: "Модерація" },
          { to: "/app/business", label: "Бізнес-аналітика" }
        ]
      : user?.role === "MODERATOR"
        ? [{ to: "/app/moderation", label: "Модерація" }]
        : [{ to: "/app/business", label: "Мої кампанії" }];

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebarTop">
          <div className="brand">
            <img src="/logo-placeholder.svg" alt="ChallengeHub logo" className="logo" />
            <h2>ChallengeHub</h2>
          </div>
          <nav>
            {links.map((item) => (
              <Link key={item.to} to={item.to}>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="sidebarBottom">
          <button onClick={logout}>Вийти</button>
        </div>
      </aside>
      <section className="content">
        <header className="topbar">
          <div>
            <strong>{user?.fullName}</strong>
            <span className="muted"> ({user?.role ? roleLabels[user.role] ?? user.role : ""})</span>
          </div>
        </header>
        <main>
          <Outlet />
        </main>
      </section>
    </div>
  );
}
