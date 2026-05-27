import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="landing hero">
      <div className="brand">
        <img src="/logo-full.png" alt="ChallengeHub logo" className="logo logoFull" />
        <h1>ChallengeHub</h1>
      </div>
      <p>Панель керування для ролей Admin, Moderator та BusinessClient.</p>
      <div className="row">
        <a className="button" href="/downloads/challengehub-mobile.vpk" download>
          Завантажити мобільну версію (.vpk)
        </a>
        <Link className="button secondary" to="/login">
          Увійти у веб-панель
        </Link>
      </div>
    </div>
  );
}
