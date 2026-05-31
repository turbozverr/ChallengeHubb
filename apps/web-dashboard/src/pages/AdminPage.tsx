import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { resolveMediaUrl } from "../api/media";
import type {
  AdVideoResponse,
  AdminDashboardAnalyticsResponse,
  MobileUserResponse,
  ModerationVideoResponse,
  SponsoredChallengeResponse,
  SystemSettingsResponse,
  UserChallengeAdminResponse,
  WebUserResponse
} from "../api/types";
import { useAuth } from "../auth/AuthContext";

type AdminTab = "dashboard" | "web-users" | "mobile-users" | "challenges" | "user-challenges" | "ad-videos" | "videos" | "settings";

const tabLabels: Record<AdminTab, string> = {
  dashboard: "Дешборд",
  "mobile-users": "Користувачі",
  "web-users": "Веб-користувачі",
  challenges: "Спонсорські челенджі",
  "user-challenges": "Челенджі",
  "ad-videos": "Рекламні відео",
  videos: "Відео",
  settings: "Налаштування"
};

const roleLabels: Record<string, string> = {
  ADMIN: "Адміністратор",
  MODERATOR: "Модератор",
  BUSINESS_CLIENT: "Бізнес-клієнт"
};

const difficultyLabels: Record<string, string> = {
  easy: "Легка",
  normal: "Середня",
  hard: "Складна"
};

const statusLabels: Record<string, string> = {
  DRAFT: "Чернетка",
  PUBLISHED: "Опубліковано",
  BLOCKED: "Заблоковано",
  PENDING_MANUAL: "На модерації"
};

const overviewLabels: Record<string, string> = {
  web_users_total: "Всього веб-користувачів",
  sponsored_challenges_total: "Всього спонсорських челенджів",
  videos_pending_manual: "Відео в ручній модерації",
  open_reports: "Відкриті скарги"
};

type ChartSeries = { name: string; color: string; values: number[] };

function LineChart({ labels, series, yLabel }: { labels: string[]; series: ChartSeries[]; yLabel: string }) {
  const width = 900;
  const height = 260;
  const left = 48;
  const right = 16;
  const top = 16;
  const bottom = 36;
  const plotW = width - left - right;
  const plotH = height - top - bottom;

  const maxValue = Math.max(1, ...series.flatMap((s) => s.values));
  const xFor = (i: number) => left + (labels.length <= 1 ? 0 : (i / (labels.length - 1)) * plotW);
  const yFor = (v: number) => top + (1 - v / maxValue) * plotH;

  return (
    <div className="chartCard">
      <svg viewBox={`0 0 ${width} ${height}`} className="chartSvg" role="img" aria-label={yLabel}>
        <line x1={left} y1={top} x2={left} y2={top + plotH} stroke="#5a5a5a" />
        <line x1={left} y1={top + plotH} x2={left + plotW} y2={top + plotH} stroke="#5a5a5a" />
        {[0, 0.25, 0.5, 0.75, 1].map((m) => (
          <g key={m}>
            <line x1={left} y1={yFor(maxValue * m)} x2={left + plotW} y2={yFor(maxValue * m)} stroke="#2f2f2f" />
            <text x={8} y={yFor(maxValue * m) + 5} fill="#b8b8b8" fontSize="17">
              {(maxValue * m).toFixed(0)}
            </text>
          </g>
        ))}
        {series.map((s) => {
          const points = s.values.map((v, i) => `${xFor(i)},${yFor(v)}`).join(" ");
          return <polyline key={s.name} fill="none" stroke={s.color} strokeWidth="2.5" points={points} />;
        })}
        {labels.map((l, i) => (
          <text key={l + i} x={xFor(i)} y={height - 10} fill="#9d9d9d" fontSize="14" textAnchor="middle">
            {l.slice(5)}
          </text>
        ))}
      </svg>
      <div className="chartLegend">
        {series.map((s) => (
          <span key={s.name}>
            <i style={{ background: s.color }} /> {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}

export function AdminPage() {
  const { token } = useAuth();
  const [tab, setTab] = useState<AdminTab>("dashboard");
  const [overview, setOverview] = useState<Record<string, number>>({});
  const [users, setUsers] = useState<WebUserResponse[]>([]);
  const [mobileUsers, setMobileUsers] = useState<MobileUserResponse[]>([]);
  const [challenges, setChallenges] = useState<SponsoredChallengeResponse[]>([]);
  const [userChallenges, setUserChallenges] = useState<UserChallengeAdminResponse[]>([]);
  const [videos, setVideos] = useState<ModerationVideoResponse[]>([]);
  const [adVideos, setAdVideos] = useState<AdVideoResponse[]>([]);
  const [settings, setSettings] = useState<SystemSettingsResponse | null>(null);
  const [dashboard, setDashboard] = useState<AdminDashboardAnalyticsResponse | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [userSearch, setUserSearch] = useState("");
  const [mobileUserSearch, setMobileUserSearch] = useState("");
  const [userRoleFilter, setUserRoleFilter] = useState("ALL");
  const [challengeSearch, setChallengeSearch] = useState("");
  const [challengeDifficultyFilter, setChallengeDifficultyFilter] = useState("ALL");
  const [challengeStatusFilter, setChallengeStatusFilter] = useState("ALL");
  const [videoSearch, setVideoSearch] = useState("");
  const [videoStatusFilter, setVideoStatusFilter] = useState("ALL");
  const [adVideoSearch, setAdVideoSearch] = useState("");
  const [adVideoStatusFilter, setAdVideoStatusFilter] = useState("ALL");

  const [usersPage, setUsersPage] = useState(1);
  const [mobileUsersPage, setMobileUsersPage] = useState(1);
  const [challengesPage, setChallengesPage] = useState(1);
  const [videosPage, setVideosPage] = useState(1);
  const [adVideosPage, setAdVideosPage] = useState(1);
  const pageSize = 8;

  const [confirm, setConfirm] = useState<{ title: string; message: string; action: () => Promise<void> } | null>(null);
  const [editUser, setEditUser] = useState<WebUserResponse | null>(null);
  const [editMobileUser, setEditMobileUser] = useState<MobileUserResponse | null>(null);
  const [editChallenge, setEditChallenge] = useState<SponsoredChallengeResponse | null>(null);
  const [editUserChallenge, setEditUserChallenge] = useState<UserChallengeAdminResponse | null>(null);
  const [editChallengePromoList, setEditChallengePromoList] = useState("");
  const [editVideo, setEditVideo] = useState<ModerationVideoResponse | null>(null);
  const [editAdVideo, setEditAdVideo] = useState<AdVideoResponse | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [newUser, setNewUser] = useState({ full_name: "", email: "", password: "", role: "MODERATOR", company_name: "" });
  const [newChallenge, setNewChallenge] = useState({
    title: "",
    description: "",
    difficulty: "normal",
    duration_days: 7,
    xp_reward: 100,
    promo_mode: "NONE",
    promo_single_code: "",
    promo_codes_text: "",
    client_id: ""
  });
  const [adDescription, setAdDescription] = useState("");
  const [adFile, setAdFile] = useState<File | null>(null);

  const businessClients = useMemo(() => users.filter((u) => u.role === "BUSINESS_CLIENT"), [users]);

  const usersFiltered = useMemo(() => {
    const q = userSearch.toLowerCase();
    return users.filter((u) => {
      const text = `${u.id} ${u.full_name} ${u.email}`.toLowerCase();
      const roleOk = userRoleFilter === "ALL" || u.role === userRoleFilter;
      return text.includes(q) && roleOk;
    });
  }, [users, userSearch, userRoleFilter]);

  const mobileUsersFiltered = useMemo(() => {
    const q = mobileUserSearch.toLowerCase();
    return mobileUsers.filter((u) => `${u.id} ${u.username} ${u.full_name} ${u.email}`.toLowerCase().includes(q));
  }, [mobileUsers, mobileUserSearch]);

  const challengesFiltered = useMemo(() => {
    const q = challengeSearch.toLowerCase();
    return challenges.filter((c) => {
      const text = `${c.id} ${c.title} ${c.client_company_name}`.toLowerCase();
      const diffOk = challengeDifficultyFilter === "ALL" || c.difficulty === challengeDifficultyFilter;
      const statusOk = challengeStatusFilter === "ALL" || c.status === challengeStatusFilter;
      return text.includes(q) && diffOk && statusOk;
    });
  }, [challenges, challengeSearch, challengeDifficultyFilter, challengeStatusFilter]);

  const videosFiltered = useMemo(
    () =>
      videos.filter((v) => {
        const q = videoSearch.toLowerCase();
        const text = `${v.id} ${v.description ?? ""} ${v.url}`.toLowerCase();
        const statusOk = videoStatusFilter === "ALL" || v.status === videoStatusFilter;
        return text.includes(q) && statusOk;
      }),
    [videos, videoSearch, videoStatusFilter]
  );
  const adVideosFiltered = useMemo(
    () =>
      adVideos.filter((v) => {
        const q = adVideoSearch.toLowerCase();
        const media = v.url ?? "";
        const text = `${v.id} ${v.description ?? ""} ${media}`.toLowerCase();
        const statusOk = adVideoStatusFilter === "ALL" || v.status === adVideoStatusFilter;
        return text.includes(q) && statusOk;
      }),
    [adVideos, adVideoSearch, adVideoStatusFilter]
  );

  const usersTotalPages = Math.max(1, Math.ceil(usersFiltered.length / pageSize));
  const mobileUsersTotalPages = Math.max(1, Math.ceil(mobileUsersFiltered.length / pageSize));
  const challengesTotalPages = Math.max(1, Math.ceil(challengesFiltered.length / pageSize));
  const videosTotalPages = Math.max(1, Math.ceil(videosFiltered.length / pageSize));
  const adVideosTotalPages = Math.max(1, Math.ceil(adVideosFiltered.length / pageSize));

  const usersRows = usersFiltered.slice((usersPage - 1) * pageSize, usersPage * pageSize);
  const mobileUsersRows = mobileUsersFiltered.slice((mobileUsersPage - 1) * pageSize, mobileUsersPage * pageSize);
  const challengeRows = challengesFiltered.slice((challengesPage - 1) * pageSize, challengesPage * pageSize);
  const videoRows = videosFiltered.slice((videosPage - 1) * pageSize, videosPage * pageSize);
  const adVideoRows = adVideosFiltered.slice((adVideosPage - 1) * pageSize, adVideosPage * pageSize);

  const load = async () => {
    if (!token) return;
    try {
      const [ov, wu, mu, ch, uch, vd, av, st, da] = await Promise.all([
        api.adminOverview(token),
        api.listWebUsers(token),
        api.listMobileUsers(token),
        api.listSponsoredChallenges(token),
        api.listUserChallenges(token),
        api.adminVideos(token),
        api.listAdVideos(token),
        api.getSettings(token),
        api.adminDashboardAnalytics(token)
      ]);
      setOverview(ov);
      setUsers(wu);
      setMobileUsers(mu);
      setChallenges(ch);
      setUserChallenges(uch);
      setVideos(vd);
      setAdVideos(av);
      setSettings(st);
      setDashboard(da);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Помилка завантаження");
      setToast({ type: "error", message: "Не вдалося завантажити дані" });
    }
  };

  useEffect(() => {
    void load();
  }, [token]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2800);
    return () => clearTimeout(t);
  }, [toast]);

  useEffect(() => setUsersPage(1), [userSearch, userRoleFilter]);
  useEffect(() => setMobileUsersPage(1), [mobileUserSearch]);
  useEffect(() => setChallengesPage(1), [challengeSearch, challengeDifficultyFilter, challengeStatusFilter]);
  useEffect(() => setVideosPage(1), [videoSearch, videoStatusFilter]);
  useEffect(() => setAdVideosPage(1), [adVideoSearch, adVideoStatusFilter]);

  const fieldError = (name: string) => setToast({ type: "error", message: `Заповніть поле: ${name}` });
  const dayLabels = useMemo(
    () => (dashboard ? Array.from(new Set(dashboard.dau_wau_mau.map((p) => p.date.split("|")[0]))) : []),
    [dashboard]
  );
  const dauSeries = useMemo(
    () =>
      dayLabels.map((d) => dashboard?.dau_wau_mau.find((p) => p.date === `${d}|DAU`)?.value ?? 0),
    [dashboard, dayLabels]
  );
  const wauSeries = useMemo(
    () =>
      dayLabels.map((d) => dashboard?.dau_wau_mau.find((p) => p.date === `${d}|WAU`)?.value ?? 0),
    [dashboard, dayLabels]
  );
  const mauSeries = useMemo(
    () =>
      dayLabels.map((d) => dashboard?.dau_wau_mau.find((p) => p.date === `${d}|MAU`)?.value ?? 0),
    [dashboard, dayLabels]
  );

  return (
    <div className="card">
      <h1>Панель адміністратора</h1>
      {toast ? <div className={`toast ${toast.type}`}>{toast.message}</div> : null}
      {error ? <p className="error">{error}</p> : null}

      <div className="tabs">
        {(["dashboard", "mobile-users", "web-users", "challenges", "user-challenges", "ad-videos", "videos", "settings"] as AdminTab[]).map((t) => (
          <button key={t} className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>
            {tabLabels[t]}
          </button>
        ))}
      </div>

      {tab === "dashboard" && (
        <>
          <div className="grid3">
            {Object.entries(overview).map(([k, v]) => (
              <div key={k} className="stat">
                <strong>{v}</strong>
                <span>{overviewLabels[k] ?? k}</span>
              </div>
            ))}
          </div>
          <div className="chartGrid">
            <section>
              <h2>Активність користувачів</h2>
              <LineChart
                labels={dayLabels}
                yLabel="Активні користувачі"
                series={[
                    { name: "Активні за день", color: "#AD46FF", values: dauSeries },
                    { name: "Активні за 7 днів", color: "#F6339A", values: wauSeries },
                    { name: "Активні за 30 днів", color: "#36CFC9", values: mauSeries }
                  ]}
              />
            </section>

            <section>
              <h2>Реєстрації користувачів</h2>
              <LineChart
                labels={dashboard?.mobile_registrations.map((r) => r.date) ?? []}
                yLabel="Реєстрації"
                series={[
                  { name: "Нові користувачі", color: "#AD46FF", values: dashboard?.mobile_registrations.map((r) => r.users) ?? [] }
                ]}
              />
            </section>
          </div>

          <div className="chartGrid">
            <section>
              <h2>Середній час рішення модератора</h2>
              <LineChart
                labels={dashboard?.moderation_decision_time_hours.map((p) => p.date) ?? []}
                yLabel="Години"
                series={[{ name: "Середній час, год.", color: "#F6339A", values: dashboard?.moderation_decision_time_hours.map((p) => p.value) ?? [] }]}
              />
            </section>

            <section>
              <h2>Зростання контенту</h2>
              <LineChart
                labels={dashboard?.content_growth.map((p) => p.date) ?? []}
                yLabel="Кількість відео"
                series={[
                  { name: "Рекламні", color: "#AD46FF", values: dashboard?.content_growth.map((p) => p.ad_videos) ?? [] },
                  { name: "Звичайні", color: "#36CFC9", values: dashboard?.content_growth.map((p) => p.regular_videos) ?? [] }
                ]}
              />
            </section>
          </div>

          <div className="chartGrid">
            <section>
              <h2>Якість AI-модерації</h2>
              <LineChart
                labels={dashboard?.ai_quality_overturned_rate.map((p) => p.date) ?? []}
                yLabel="%"
                series={[{ name: "Змінені рішення, %", color: "#F6339A", values: dashboard?.ai_quality_overturned_rate.map((p) => p.value) ?? [] }]}
              />
            </section>
          </div>
        </>
      )}

      {tab === "web-users" && (
        <>
          <form
            className="grid2"
            onSubmit={async (e: FormEvent) => {
              e.preventDefault();
              if (!token) return;
              if (!newUser.full_name) return fieldError("ПІБ");
              if (!newUser.email) return fieldError("Email");
              if (!newUser.password) return fieldError("Пароль");

              await api.createWebUser(token, { ...newUser, company_name: newUser.company_name || undefined });
              setNewUser({ full_name: "", email: "", password: "", role: "MODERATOR", company_name: "" });
              setToast({ type: "success", message: "Користувача створено" });
              await load();
            }}
          >
            <div><label>ПІБ</label><input value={newUser.full_name} onChange={(e) => setNewUser((s) => ({ ...s, full_name: e.target.value }))} /></div>
            <div><label>Email</label><input value={newUser.email} onChange={(e) => setNewUser((s) => ({ ...s, email: e.target.value }))} /></div>
            <div><label>Пароль</label><input type="password" value={newUser.password} onChange={(e) => setNewUser((s) => ({ ...s, password: e.target.value }))} /></div>
            <div><label>Роль</label><select value={newUser.role} onChange={(e) => setNewUser((s) => ({ ...s, role: e.target.value }))}><option value="MODERATOR">Модератор</option><option value="BUSINESS_CLIENT">Бізнес-клієнт</option><option value="ADMIN">Адміністратор</option></select></div>
            <div><label>Компанія (необов'язково)</label><input value={newUser.company_name} onChange={(e) => setNewUser((s) => ({ ...s, company_name: e.target.value }))} /></div>
            <div className="formSubmit"><button type="submit">Створити</button></div>
          </form>

          <hr className="sectionDivider" />
          <div className="filtersRow">
            <input placeholder="Пошук за ID, ПІБ, Email" value={userSearch} onChange={(e) => setUserSearch(e.target.value)} />
            <select value={userRoleFilter} onChange={(e) => setUserRoleFilter(e.target.value)}>
              <option value="ALL">Всі ролі</option>
              <option value="ADMIN">Адміністратор</option>
              <option value="MODERATOR">Модератор</option>
              <option value="BUSINESS_CLIENT">Бізнес-клієнт</option>
            </select>
          </div>

          <div className="tableWrap">
            <table>
              <thead><tr><th>ID</th><th>Ім'я</th><th>Email</th><th>Роль</th><th>Дії</th></tr></thead>
              <tbody>
                {usersRows.map((u) => (
                  <tr key={u.id}>
                    <td>{u.id}</td><td>{u.full_name}</td><td>{u.email}</td><td>{roleLabels[u.role] ?? u.role}</td>
                    <td>
                      <div className="actionBar">
                        <button className="actionBtn iconOnly edit" title="Редагувати" aria-label="Редагувати" onClick={() => setEditUser(u)}><span className="iconGlyph pencil">✎</span></button>
                        <button className="actionBtn iconOnly danger" title="Видалити" aria-label="Видалити" onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити користувача ${u.full_name}?`, action: async () => { if (!token) return; await api.deleteWebUser(token, u.id); setToast({ type: "success", message: "Користувача видалено" }); await load(); } })}><span className="iconGlyph delete">⌫</span></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button disabled={usersPage <= 1} onClick={() => setUsersPage((p) => p - 1)}>Попередня</button>
            <span>Сторінка {usersPage} з {usersTotalPages}</span>
            <button disabled={usersPage >= usersTotalPages} onClick={() => setUsersPage((p) => p + 1)}>Наступна</button>
          </div>
        </>
      )}

      {tab === "mobile-users" && (
        <>
          <div className="filtersRow">
            <input
              placeholder="Пошук за ID, @логіном, іменем або Email"
              value={mobileUserSearch}
              onChange={(e) => setMobileUserSearch(e.target.value)}
            />
          </div>
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>@логін</th>
                  <th>Ім'я</th>
                  <th>Email</th>
                  <th>XP</th>
                  <th>Premium</th>
                  <th>Статус</th>
                  <th>Дії</th>
                </tr>
              </thead>
              <tbody>
                {mobileUsersRows.map((u) => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>@{u.username}</td>
                    <td>{u.full_name}</td>
                    <td>{u.email}</td>
                    <td>{u.xp}</td>
                    <td>{u.is_premium ? "Так" : "Ні"}</td>
                    <td>{u.status === "ACTIVE" ? "Активний" : u.status}</td>
                    <td>
                      <div className="actionBar">
                        <button className="actionBtn iconOnly edit" title="Редагувати ім'я" aria-label="Редагувати ім'я" onClick={() => setEditMobileUser(u)}><span className="iconGlyph pencil">✎</span></button>
                        <button className="actionBtn iconOnly danger" title="Видалити" aria-label="Видалити" onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити користувача ${u.full_name}?`, action: async () => { if (!token) return; await api.deleteMobileUser(token, u.id); setToast({ type: "success", message: "Користувача видалено" }); await load(); } })}><span className="iconGlyph delete">⌫</span></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button disabled={mobileUsersPage <= 1} onClick={() => setMobileUsersPage((p) => p - 1)}>Попередня</button>
            <span>Сторінка {mobileUsersPage} з {mobileUsersTotalPages}</span>
            <button disabled={mobileUsersPage >= mobileUsersTotalPages} onClick={() => setMobileUsersPage((p) => p + 1)}>Наступна</button>
          </div>
        </>
      )}

      {tab === "challenges" && (
        <>
          <form className="grid2" onSubmit={async (e: FormEvent) => {
            e.preventDefault();
            if (!token) return;
            if (!newChallenge.title) return fieldError("Назва");
            if (!newChallenge.description) return fieldError("Опис");
            if (!newChallenge.client_id) return fieldError("Бізнес-клієнт");

            await api.createSponsoredChallenge(token, {
              ...newChallenge,
              reward_text: "",
              xp_reward: Number(newChallenge.xp_reward),
              duration_days: Number(newChallenge.duration_days),
              promo_single_code: newChallenge.promo_mode === "SINGLE" ? newChallenge.promo_single_code : undefined,
              promo_codes: newChallenge.promo_mode === "LIST" ? newChallenge.promo_codes_text.split(/\r?\n/).map((v) => v.trim()).filter(Boolean) : undefined
            });
            setToast({ type: "success", message: "Челендж створено" });
            await load();
          }}>
            <div><label>Назва челенджу</label><input value={newChallenge.title} onChange={(e) => setNewChallenge((s) => ({ ...s, title: e.target.value }))} /></div>
            <div><label>Бізнес-клієнт</label><select value={newChallenge.client_id} onChange={(e) => setNewChallenge((s) => ({ ...s, client_id: e.target.value }))}><option value="">Оберіть</option>{businessClients.map((c) => <option key={c.id} value={c.id}>{c.full_name}</option>)}</select></div>
            <div><label>Опис</label><textarea value={newChallenge.description} onChange={(e) => setNewChallenge((s) => ({ ...s, description: e.target.value }))} /></div>
            <div><label>Складність</label><select value={newChallenge.difficulty} onChange={(e) => setNewChallenge((s) => ({ ...s, difficulty: e.target.value }))}><option value="easy">Легка</option><option value="normal">Середня</option><option value="hard">Складна</option></select></div>
            <div><label>Тривалість (днів)</label><input type="number" value={newChallenge.duration_days} onChange={(e) => setNewChallenge((s) => ({ ...s, duration_days: Number(e.target.value) }))} /></div>
            <div><label>XP нагорода</label><input type="number" value={newChallenge.xp_reward} onChange={(e) => setNewChallenge((s) => ({ ...s, xp_reward: Number(e.target.value) }))} /></div>
            <div><label>Промокоди</label><select value={newChallenge.promo_mode} onChange={(e) => setNewChallenge((s) => ({ ...s, promo_mode: e.target.value }))}><option value="NONE">Без промокоду</option><option value="SINGLE">Один код для всіх</option><option value="LIST">Список кодів</option></select></div>
            <div>
              {newChallenge.promo_mode === "SINGLE" ? <div><label>Промокоди</label><input placeholder="Промокод" value={newChallenge.promo_single_code} onChange={(e) => setNewChallenge((s) => ({ ...s, promo_single_code: e.target.value }))} /></div> : null}
              {newChallenge.promo_mode === "LIST" ? <div><label>Промокоди</label><textarea placeholder="Промокоди, по одному на рядок" value={newChallenge.promo_codes_text} onChange={(e) => setNewChallenge((s) => ({ ...s, promo_codes_text: e.target.value }))} /></div> : null}
            </div>
             <div className="formSubmit"><button type="submit">Створити</button></div>
          </form>

          <hr className="sectionDivider" />
          <div className="filtersRow">
            <input placeholder="Пошук за ID, назвою, компанією" value={challengeSearch} onChange={(e) => setChallengeSearch(e.target.value)} />
            <select value={challengeDifficultyFilter} onChange={(e) => setChallengeDifficultyFilter(e.target.value)}><option value="ALL">Вся складність</option><option value="easy">Легка</option><option value="normal">Середня</option><option value="hard">Складна</option></select>
            <select value={challengeStatusFilter} onChange={(e) => setChallengeStatusFilter(e.target.value)}><option value="ALL">Всі статуси</option><option value="DRAFT">Чернетка</option><option value="PUBLISHED">Опубліковано</option><option value="BLOCKED">Заблоковано</option></select>
          </div>

          <div className="tableWrap">
            <table>
              <thead><tr><th>ID</th><th>Назва</th><th>Складність</th><th>Днів</th><th>XP</th><th>Статус</th><th>Дії</th></tr></thead>
              <tbody>
                {challengeRows.map((c) => (
                  <tr key={c.id}>
                    <td>{c.id}</td><td>{c.title}</td><td>{difficultyLabels[c.difficulty] ?? c.difficulty}</td><td>{c.duration_days}</td><td>{c.xp_reward}</td><td>{statusLabels[c.status] ?? c.status}</td>
                    <td>
                      <div className="actionBar">
                        <button className="actionBtn iconOnly edit" title="Редагувати" aria-label="Редагувати" onClick={async () => { setEditChallenge(c); if (c.promo_mode === "LIST" && token) { const rows = await api.challengePromoCodes(token, c.id); setEditChallengePromoList(rows.map((r) => r.code).join("\n")); } else { setEditChallengePromoList(""); } }}><span className="iconGlyph pencil">✎</span></button>
                        {c.status === "PUBLISHED" ? (
                          <button className="actionBtn iconOnly publish" title="Вже опубліковано" aria-label="Вже опубліковано" disabled>✓</button>
                        ) : (
                          <button className="actionBtn iconOnly publish" title="Публікувати" aria-label="Публікувати" onClick={async () => { if (!token) return; await api.publishSponsoredChallenge(token, c.id); setToast({ type: "success", message: "Челендж опубліковано" }); await load(); }}>↑</button>
                        )}
                        <button className="actionBtn iconOnly danger" title="Видалити" aria-label="Видалити" onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити челендж ${c.title}?`, action: async () => { if (!token) return; await api.deleteSponsoredChallenge(token, c.id); setToast({ type: "success", message: "Челендж видалено" }); await load(); } })}><span className="iconGlyph delete">⌫</span></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button disabled={challengesPage <= 1} onClick={() => setChallengesPage((p) => p - 1)}>Попередня</button>
            <span>Сторінка {challengesPage} з {challengesTotalPages}</span>
            <button disabled={challengesPage >= challengesTotalPages} onClick={() => setChallengesPage((p) => p + 1)}>Наступна</button>
          </div>
        </>
      )}

      {tab === "user-challenges" && (
        <>
          <div className="tableWrap">
            <table>
              <thead><tr><th>ID</th><th>Назва</th><th>Складність</th><th>Днів</th><th>XP</th><th>Статус</th><th>Дії</th></tr></thead>
              <tbody>
                {userChallenges.map((c) => (
                  <tr key={c.id}>
                    <td>{c.id}</td>
                    <td>{c.title}</td>
                    <td>{difficultyLabels[c.difficulty] ?? c.difficulty}</td>
                    <td>{c.duration_days}</td>
                    <td>{c.xp_reward}</td>
                    <td>{statusLabels[c.status] ?? c.status}</td>
                    <td>
                      <div className="actionBar">
                        <button className="actionBtn iconOnly edit" title="Редагувати" aria-label="Редагувати" onClick={() => setEditUserChallenge(c)}><span className="iconGlyph pencil">✎</span></button>
                        <button className="actionBtn iconOnly danger" title="Видалити" aria-label="Видалити" onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити челендж ${c.title}?`, action: async () => { if (!token) return; await api.deleteUserChallenge(token, c.id); setToast({ type: "success", message: "Челендж видалено" }); await load(); } })}><span className="iconGlyph delete">⌫</span></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "ad-videos" && (
        <>
          <form className="grid2" onSubmit={async (e: FormEvent) => {
            e.preventDefault();
            if (!token) return;
            if (!adDescription) return fieldError("Опис рекламного відео");
            if (!adFile) return fieldError("Файл рекламного відео");
            await api.uploadAdVideo(token, { description: adDescription, file: adFile });
            setAdDescription("");
            setAdFile(null);
            setToast({ type: "success", message: "Рекламне відео завантажено" });
            await load();
          }}>
            <div><label>Опис рекламного відео</label><input value={adDescription} onChange={(e) => setAdDescription(e.target.value)} /></div>
            <div><label>Файл відео</label><input type="file" accept="video/*" onChange={(e) => setAdFile(e.target.files?.[0] ?? null)} /></div>
            <div className="formSubmit"><button type="submit">Завантажити</button></div>
          </form>
          <hr className="sectionDivider" />
          <div className="filtersRow">
            <input placeholder="Пошук за ID, описом або URL" value={adVideoSearch} onChange={(e) => setAdVideoSearch(e.target.value)} />
            <select value={adVideoStatusFilter} onChange={(e) => setAdVideoStatusFilter(e.target.value)}>
              <option value="ALL">Всі статуси</option>
              <option value="PUBLISHED">Опубліковано</option>
              <option value="BLOCKED">Заблоковано</option>
            </select>
          </div>
          <div className="tableWrap">
            <table>
              <thead><tr><th>ID</th><th>Опис</th><th>Посилання</th><th>Статус</th><th>Перегляди</th><th>Репости</th><th>Дії</th></tr></thead>
              <tbody>
                {adVideoRows.map((v) => (
                  <tr key={v.id}>
                    <td>{v.id}</td>
                    <td>{v.description ?? "-"}</td>
                    <td><button className="actionBtn iconOnly view" title="Перегляд" aria-label="Перегляд" onClick={() => setPreviewUrl(resolveMediaUrl(v.url ?? ""))}>▶</button></td>
                    <td>{statusLabels[v.status] ?? v.status}</td>
                    <td>{v.views_count}</td>
                    <td>{v.shares_count}</td>
                    <td>
                      <div className="actionBar">
                        <button className="actionBtn iconOnly edit" title="Редагувати" aria-label="Редагувати" onClick={() => setEditAdVideo(v)}><span className="iconGlyph pencil">✎</span></button>
                        <button className="actionBtn iconOnly danger" title="Видалити" aria-label="Видалити" onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити рекламне відео ${v.id}?`, action: async () => { if (!token) return; await api.deleteAdVideo(token, v.id); setToast({ type: "success", message: "Рекламне відео видалено" }); await load(); } })}><span className="iconGlyph delete">⌫</span></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button disabled={adVideosPage <= 1} onClick={() => setAdVideosPage((p) => p - 1)}>Попередня</button>
            <span>Сторінка {adVideosPage} з {adVideosTotalPages}</span>
            <button disabled={adVideosPage >= adVideosTotalPages} onClick={() => setAdVideosPage((p) => p + 1)}>Наступна</button>
          </div>
        </>
      )}

      {tab === "videos" && (
        <>
          <div className="filtersRow">
            <input
              placeholder="Пошук за ID, описом або URL"
              value={videoSearch}
              onChange={(e) => setVideoSearch(e.target.value)}
            />
            <select value={videoStatusFilter} onChange={(e) => setVideoStatusFilter(e.target.value)}><option value="ALL">Всі статуси</option><option value="PUBLISHED">Опубліковано</option><option value="PENDING_MANUAL">На модерації</option><option value="BLOCKED">Заблоковано</option></select>
          </div>
          <div className="tableWrap">
            <table>
              <thead><tr><th>ID</th><th>Опис</th><th>Посилання</th><th>Статус</th><th>Перегляди</th><th>Лайки</th><th>Репости</th><th>Дії</th></tr></thead>
              <tbody>
                {videoRows.map((v) => (
                  <tr key={v.id}>
                    <td>{v.id}</td>
                    <td>{v.description ?? "-"}</td>
                    <td><button className="actionBtn iconOnly view" title="Перегляд" aria-label="Перегляд" onClick={() => setPreviewUrl(resolveMediaUrl(v.url))}>▶</button></td>
                    <td>{statusLabels[v.status] ?? v.status}</td>
                    <td>{v.views_count}</td>
                    <td>{v.likes_count}</td>
                    <td>{v.shares_count}</td>
                    <td>
                      <div className="actionBar">
                      <button className="actionBtn iconOnly edit" title="Редагувати" aria-label="Редагувати" onClick={() => setEditVideo(v)}><span className="iconGlyph pencil">✎</span></button>
                      {v.status !== "BLOCKED" ? (
                        <button className="actionBtn iconOnly warning" title="Заблокувати" aria-label="Заблокувати" onClick={() => setConfirm({ title: "Підтвердження", message: `Заблокувати відео ${v.id}?`, action: async () => { if (!token) return; await api.updateVideo(token, v.id, { status: "BLOCKED" }); setToast({ type: "success", message: "Відео заблоковано" }); await load(); } })}>×</button>
                      ) : (
                        <button className="actionBtn iconOnly publish" title="Розблокувати" aria-label="Розблокувати" onClick={() => setConfirm({ title: "Підтвердження", message: `Розблокувати відео ${v.id}?`, action: async () => { if (!token) return; await api.updateVideo(token, v.id, { status: "PUBLISHED" }); setToast({ type: "success", message: "Відео розблоковано" }); await load(); } })}>↺</button>
                      )}
                      <button className="actionBtn iconOnly danger" title="Видалити" aria-label="Видалити" onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити відео ${v.id}?`, action: async () => { if (!token) return; await api.deleteVideo(token, v.id); setToast({ type: "success", message: "Відео видалено" }); await load(); } })}><span className="iconGlyph delete">⌫</span></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <button disabled={videosPage <= 1} onClick={() => setVideosPage((p) => p - 1)}>Попередня</button>
            <span>Сторінка {videosPage} з {videosTotalPages}</span>
            <button disabled={videosPage >= videosTotalPages} onClick={() => setVideosPage((p) => p + 1)}>Наступна</button>
          </div>
        </>
      )}

      {tab === "settings" && settings && (
        <form className="grid2" onSubmit={async (e: FormEvent) => {
          e.preventDefault();
          if (!token) return;
          await api.updateSettings(token, {
            ai_confidence_threshold: settings.ai_confidence_threshold,
            report_limit: settings.report_limit
          });
          setToast({ type: "success", message: "Налаштування збережено" });
        }}>
          <div><label>Поріг впевненості AI</label><input type="number" step="0.01" value={settings.ai_confidence_threshold} onChange={(e) => setSettings((s) => (s ? { ...s, ai_confidence_threshold: Number(e.target.value) } : s))} /></div>
          <div><label>Ліміт скарг для автоприховування</label><input type="number" value={settings.report_limit} onChange={(e) => setSettings((s) => (s ? { ...s, report_limit: Number(e.target.value) } : s))} /></div>
          <div className="formSubmit"><button type="submit">Зберегти</button></div>
        </form>
      )}

      {editUser ? (
        <div className="modalBackdrop" onClick={() => setEditUser(null)}>
          <div className="modalCard" onClick={(e) => e.stopPropagation()}>
            <h3>Редагувати користувача</h3>
            <div className="grid2">
              <div><label>Ім'я</label><input value={editUser.full_name} onChange={(e) => setEditUser({ ...editUser, full_name: e.target.value })} /></div>
              <div><label>Роль</label><select value={editUser.role} onChange={(e) => setEditUser({ ...editUser, role: e.target.value as WebUserResponse["role"] })}><option value="ADMIN">Адміністратор</option><option value="MODERATOR">Модератор</option><option value="BUSINESS_CLIENT">Бізнес-клієнт</option></select></div>
            </div>
            <div className="row">
              <button onClick={async () => { if (!token) return; await api.updateWebUser(token, editUser.id, { full_name: editUser.full_name, role: editUser.role }); setToast({ type: "success", message: "Користувача оновлено" }); setEditUser(null); await load(); }}>Зберегти</button>
              <button className="button secondary" onClick={() => setEditUser(null)}>Скасувати</button>
            </div>
          </div>
        </div>
      ) : null}

      {editMobileUser ? (
        <div className="modalBackdrop" onClick={() => setEditMobileUser(null)}>
          <div className="modalCard" onClick={(e) => e.stopPropagation()}>
            <h3>Редагувати користувача</h3>
            <div className="grid2">
              <div>
                <label>Відображуване ім'я</label>
                <input
                  value={editMobileUser.full_name}
                  onChange={(e) => setEditMobileUser({ ...editMobileUser, full_name: e.target.value })}
                />
              </div>
              <div>
                <label>@логін</label>
                <input value={`@${editMobileUser.username}`} disabled />
              </div>
            </div>
            <div className="row">
              <button onClick={async () => { if (!token) return; await api.updateMobileUser(token, editMobileUser.id, { full_name: editMobileUser.full_name }); setToast({ type: "success", message: "Користувача оновлено" }); setEditMobileUser(null); await load(); }}>Зберегти</button>
              <button className="button secondary" onClick={() => setEditMobileUser(null)}>Скасувати</button>
            </div>
          </div>
        </div>
      ) : null}

      {editChallenge ? (
        <div className="modalBackdrop" onClick={() => setEditChallenge(null)}>
          <div className="modalCard" onClick={(e) => e.stopPropagation()}>
            <h3>Редагувати челендж</h3>
            <div className="grid2">
              <div><label>Назва</label><input value={editChallenge.title} onChange={(e) => setEditChallenge({ ...editChallenge, title: e.target.value })} /></div>
              <div><label>Складність</label><select value={editChallenge.difficulty} onChange={(e) => setEditChallenge({ ...editChallenge, difficulty: e.target.value })}><option value="easy">Легка</option><option value="normal">Середня</option><option value="hard">Складна</option></select></div>
              <div><label>Тривалість (днів)</label><input type="number" value={editChallenge.duration_days} onChange={(e) => setEditChallenge({ ...editChallenge, duration_days: Number(e.target.value) })} /></div>
              <div><label>XP нагорода</label><input type="number" value={editChallenge.xp_reward} onChange={(e) => setEditChallenge({ ...editChallenge, xp_reward: Number(e.target.value) })} /></div>
              <div><label>Режим промокодів</label><select value={editChallenge.promo_mode} onChange={(e) => setEditChallenge({ ...editChallenge, promo_mode: e.target.value })}><option value="NONE">Без промокоду</option><option value="SINGLE">Один код для всіх</option><option value="LIST">Список кодів</option></select></div>
              {editChallenge.promo_mode === "SINGLE" ? <div><label>Промокод</label><input value={editChallenge.promo_single_code ?? ""} onChange={(e) => setEditChallenge({ ...editChallenge, promo_single_code: e.target.value })} /></div> : null}
              {editChallenge.promo_mode === "LIST" ? <div><label>Список промокодів (по одному в рядку)</label><textarea value={editChallengePromoList} onChange={(e) => setEditChallengePromoList(e.target.value)} /></div> : null}
            </div>
            <div className="row">
              <button onClick={async () => { if (!token) return; await api.updateSponsoredChallenge(token, editChallenge.id, { title: editChallenge.title, difficulty: editChallenge.difficulty, duration_days: editChallenge.duration_days, xp_reward: editChallenge.xp_reward, promo_mode: editChallenge.promo_mode, promo_single_code: editChallenge.promo_mode === "SINGLE" ? (editChallenge.promo_single_code ?? "") : undefined, promo_codes: editChallenge.promo_mode === "LIST" ? editChallengePromoList.split(/\r?\n/).map((v) => v.trim()).filter(Boolean) : undefined }); setToast({ type: "success", message: "Челендж оновлено" }); setEditChallenge(null); setEditChallengePromoList(""); await load(); }}>Зберегти</button>
              <button className="button secondary" onClick={() => setEditChallenge(null)}>Скасувати</button>
            </div>
          </div>
        </div>
      ) : null}

      {editUserChallenge ? (
        <div className="modalBackdrop" onClick={() => setEditUserChallenge(null)}>
          <div className="modalCard" onClick={(e) => e.stopPropagation()}>
            <h3>Редагувати челендж</h3>
            <div className="grid2">
              <div><label>Назва</label><input value={editUserChallenge.title} onChange={(e) => setEditUserChallenge({ ...editUserChallenge, title: e.target.value })} /></div>
              <div><label>Складність</label><select value={editUserChallenge.difficulty} onChange={(e) => setEditUserChallenge({ ...editUserChallenge, difficulty: e.target.value })}><option value="easy">Легка</option><option value="normal">Середня</option><option value="hard">Складна</option></select></div>
              <div><label>Тривалість (днів)</label><input type="number" value={editUserChallenge.duration_days} onChange={(e) => setEditUserChallenge({ ...editUserChallenge, duration_days: Number(e.target.value) })} /></div>
              <div><label>XP нагорода</label><input type="number" value={editUserChallenge.xp_reward} onChange={(e) => setEditUserChallenge({ ...editUserChallenge, xp_reward: Number(e.target.value) })} /></div>
              <div><label>Опис</label><textarea value={editUserChallenge.description} onChange={(e) => setEditUserChallenge({ ...editUserChallenge, description: e.target.value })} /></div>
              <div><label>Статус</label><select value={editUserChallenge.status} onChange={(e) => setEditUserChallenge({ ...editUserChallenge, status: e.target.value })}><option value="PUBLISHED">Опубліковано</option><option value="BLOCKED">Заблоковано</option></select></div>
            </div>
            <div className="row">
              <button onClick={async () => { if (!token) return; await api.updateUserChallenge(token, editUserChallenge.id, { title: editUserChallenge.title, description: editUserChallenge.description, difficulty: editUserChallenge.difficulty, duration_days: editUserChallenge.duration_days, xp_reward: editUserChallenge.xp_reward, status: editUserChallenge.status }); setToast({ type: "success", message: "Челендж оновлено" }); setEditUserChallenge(null); await load(); }}>Зберегти</button>
              <button className="button secondary" onClick={() => setEditUserChallenge(null)}>Скасувати</button>
            </div>
          </div>
        </div>
      ) : null}

      {editVideo ? (
        <div className="modalBackdrop" onClick={() => setEditVideo(null)}>
          <div className="modalCard" onClick={(e) => e.stopPropagation()}>
            <h3>Редагувати відео</h3>
            <div className="grid2">
              <div><label>Опис</label><textarea value={editVideo.description ?? ""} onChange={(e) => setEditVideo({ ...editVideo, description: e.target.value })} /></div>
              <div><label>Статус</label><select value={editVideo.status} onChange={(e) => setEditVideo({ ...editVideo, status: e.target.value })}><option value="PUBLISHED">Опубліковано</option><option value="PENDING_MANUAL">На модерації</option><option value="BLOCKED">Заблоковано</option></select></div>
            </div>
            <div className="row">
              <button onClick={async () => { if (!token) return; await api.updateVideo(token, editVideo.id, { description: editVideo.description ?? "", status: editVideo.status }); setToast({ type: "success", message: "Відео оновлено" }); setEditVideo(null); await load(); }}>Зберегти</button>
              <button className="button secondary" onClick={() => setEditVideo(null)}>Скасувати</button>
            </div>
          </div>
        </div>
      ) : null}

      {editAdVideo ? (
        <div className="modalBackdrop" onClick={() => setEditAdVideo(null)}>
          <div className="modalCard" onClick={(e) => e.stopPropagation()}>
            <h3>Редагувати рекламне відео</h3>
            <div className="grid2">
              <div><label>Опис</label><textarea value={editAdVideo.description ?? ""} onChange={(e) => setEditAdVideo({ ...editAdVideo, description: e.target.value })} /></div>
              <div><label>Статус</label><select value={editAdVideo.status} onChange={(e) => setEditAdVideo({ ...editAdVideo, status: e.target.value })}><option value="PUBLISHED">Опубліковано</option><option value="BLOCKED">Заблоковано</option></select></div>
            </div>
            <div className="row">
              <button onClick={async () => { if (!token) return; await api.updateAdVideo(token, editAdVideo.id, { description: editAdVideo.description ?? "", status: editAdVideo.status }); setToast({ type: "success", message: "Рекламне відео оновлено" }); setEditAdVideo(null); await load(); }}>Зберегти</button>
              <button className="button secondary" onClick={() => setEditAdVideo(null)}>Скасувати</button>
            </div>
          </div>
        </div>
      ) : null}

      {confirm ? (
        <div className="modalBackdrop" onClick={() => setConfirm(null)}>
          <div className="modalCard" onClick={(e) => e.stopPropagation()}>
            <h3>{confirm.title}</h3>
            <p>{confirm.message}</p>
            <div className="row">
              <button onClick={async () => { await confirm.action(); setConfirm(null); }}>Підтвердити</button>
              <button className="button secondary" onClick={() => setConfirm(null)}>Скасувати</button>
            </div>
          </div>
        </div>
      ) : null}

      {previewUrl ? (
        <div className="modalBackdrop" onClick={() => setPreviewUrl(null)}>
          <div className="modalCard videoPreviewModal" onClick={(e) => e.stopPropagation()}>
            <div className="modalHeader">
              <div>
                <h3>Перегляд відео</h3>
                <p className="muted">Відео відкривається у межах адмін-панелі, без переходу на окрему сторінку.</p>
              </div>
              <button className="iconClose" onClick={() => setPreviewUrl(null)} aria-label="Закрити">×</button>
            </div>
            <div className="videoFrame">
              <video controls src={previewUrl} />
            </div>
            <div className="modalActions">
              <a className="button secondary" href={previewUrl} target="_blank" rel="noreferrer">Відкрити окремо</a>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
