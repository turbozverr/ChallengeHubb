import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="landing hero">
      <div className="brand">
        <img src="/logo-full.png" alt="ChallengeHub logo" className="logoFull" />
      </div>
      <hr style={{ border: 'none', height: '1px', margin: '30px 0 40px', backgroundColor: '#3a3a3a' }} />
      <div className="row center">
        <a className="button" href="/downloads/challengehub-mobile.apk" download>
          Завантажити мобільну версію (.apk)
        </a>
        <Link className="button secondary" to="/login">
          Увійти у веб-панель
        </Link>
      </div>
    </div>
  );
}
