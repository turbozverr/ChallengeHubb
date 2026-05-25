import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type {
  AdminDashboardAnalyticsResponse,
  ModerationVideoResponse,
  SponsoredChallengeResponse,
  SystemSettingsResponse,
  WebUserResponse
} from "../api/types";
import { useAuth } from "../auth/AuthContext";

type AdminTab = "dashboard" | "web-users" | "challenges" | "ad-videos" | "videos" | "settings";

const tabLabels: Record<AdminTab, string> = {
  dashboard: "Дашборд",
  "web-users": "Веб-користувачі",
  challenges: "Спонсорські челенджі",
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
  const [challenges, setChallenges] = useState<SponsoredChallengeResponse[]>([]);
  const [videos, setVideos] = useState<ModerationVideoResponse[]>([]);
  const [settings, setSettings] = useState<SystemSettingsResponse | null>(null);
  const [dashboard, setDashboard] = useState<AdminDashboardAnalyticsResponse | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [userSearch, setUserSearch] = useState("");
  const [userRoleFilter, setUserRoleFilter] = useState("ALL");
  const [challengeSearch, setChallengeSearch] = useState("");
  const [challengeDifficultyFilter, setChallengeDifficultyFilter] = useState("ALL");
  const [challengeStatusFilter, setChallengeStatusFilter] = useState("ALL");
  const [videoStatusFilter, setVideoStatusFilter] = useState("ALL");
  const [videoAdFilter, setVideoAdFilter] = useState("ALL");

  const [usersPage, setUsersPage] = useState(1);
  const [challengesPage, setChallengesPage] = useState(1);
  const [videosPage, setVideosPage] = useState(1);
  const pageSize = 8;

  const [confirm, setConfirm] = useState<{ title: string; message: string; action: () => Promise<void> } | null>(null);
  const [editUser, setEditUser] = useState<WebUserResponse | null>(null);
  const [editChallenge, setEditChallenge] = useState<SponsoredChallengeResponse | null>(null);
  const [editVideo, setEditVideo] = useState<ModerationVideoResponse | null>(null);

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
  const [adTitle, setAdTitle] = useState("");
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
        const statusOk = videoStatusFilter === "ALL" || v.status === videoStatusFilter;
        const adOk = videoAdFilter === "ALL" || (videoAdFilter === "AD" ? v.is_ad : !v.is_ad);
        return statusOk && adOk;
      }),
    [videos, videoStatusFilter, videoAdFilter]
  );

  const usersTotalPages = Math.max(1, Math.ceil(usersFiltered.length / pageSize));
  const challengesTotalPages = Math.max(1, Math.ceil(challengesFiltered.length / pageSize));
  const videosTotalPages = Math.max(1, Math.ceil(videosFiltered.length / pageSize));

  const usersRows = usersFiltered.slice((usersPage - 1) * pageSize, usersPage * pageSize);
  const challengeRows = challengesFiltered.slice((challengesPage - 1) * pageSize, challengesPage * pageSize);
  const videoRows = videosFiltered.slice((videosPage - 1) * pageSize, videosPage * pageSize);

  const load = async () => {
    if (!token) return;
    try {
      const [ov, wu, ch, vd, st, da] = await Promise.all([
        api.adminOverview(token),
        api.listWebUsers(token),
        api.listSponsoredChallenges(token),
        api.adminVideos(token),
        api.getSettings(token),
        api.adminDashboardAnalytics(token)
      ]);
      setOverview(ov);
      setUsers(wu);
      setChallenges(ch);
      setVideos(vd);
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
  useEffect(() => setChallengesPage(1), [challengeSearch, challengeDifficultyFilter, challengeStatusFilter]);
  useEffect(() => setVideosPage(1), [videoStatusFilter, videoAdFilter]);

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
        {(["dashboard", "web-users", "challenges", "ad-videos", "videos", "settings"] as AdminTab[]).map((t) => (
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
              <h2>Щоденна, тижнева та місячна активність користувачів</h2>
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
              <h2>Реєстрації мобільних користувачів</h2>
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
              <h2>Середній час рішення модератора (години)</h2>
              <LineChart
                labels={dashboard?.moderation_decision_time_hours.map((p) => p.date) ?? []}
                yLabel="Години"
                series={[{ name: "Середній час", color: "#F6339A", values: dashboard?.moderation_decision_time_hours.map((p) => p.value) ?? [] }]}
              />
            </section>

            <section>
              <h2>Зростання контенту (рекламні та звичайні відео)</h2>
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
              <h2>Топ челенджі за залученням аудиторії</h2>
              <LineChart
                labels={dashboard?.top_challenges_engagement.map((c, i) => `${i + 1}`) ?? []}
                yLabel="Значення"
                series={[
                  { name: "Перегляди", color: "#AD46FF", values: dashboard?.top_challenges_engagement.map((c) => c.views) ?? [] },
                  { name: "Сабміти", color: "#F6339A", values: dashboard?.top_challenges_engagement.map((c) => c.submissions) ?? [] },
                  { name: "Репости", color: "#36CFC9", values: dashboard?.top_challenges_engagement.map((c) => c.shares) ?? [] }
                ]}
              />
            </section>

            <section>
              <h2>Якість AI-модерації (частка змінених рішень)</h2>
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
            <div><label>&nbsp;</label><button type="submit">Створити</button></div>
          </form>

          <hr className="sectionDivider" />
          <div className="row">
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
                    <td className="row">
                      <button onClick={() => setEditUser(u)}>Редагувати</button>
                      <button onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити користувача ${u.full_name}?`, action: async () => { if (!token) return; await api.deleteWebUser(token, u.id); setToast({ type: "success", message: "Користувача видалено" }); await load(); } })}>Видалити</button>
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
              {newChallenge.promo_mode === "SINGLE" ? <input placeholder="Промокод" value={newChallenge.promo_single_code} onChange={(e) => setNewChallenge((s) => ({ ...s, promo_single_code: e.target.value }))} /> : null}
              {newChallenge.promo_mode === "LIST" ? <textarea placeholder="Промокоди по одному на рядок" value={newChallenge.promo_codes_text} onChange={(e) => setNewChallenge((s) => ({ ...s, promo_codes_text: e.target.value }))} /> : null}
            </div>
            <div><label>&nbsp;</label><button type="submit">Створити</button></div>
          </form>

          <hr className="sectionDivider" />
          <div className="row">
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
                    <td className="row">
                      <button onClick={() => setEditChallenge(c)}>Редагувати</button>
                      <button onClick={async () => { if (!token) return; await api.publishSponsoredChallenge(token, c.id); setToast({ type: "success", message: "Челендж опубліковано" }); await load(); }}>Публікувати</button>
                      <button onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити челендж ${c.title}?`, action: async () => { if (!token) return; await api.deleteSponsoredChallenge(token, c.id); setToast({ type: "success", message: "Челендж видалено" }); await load(); } })}>Видалити</button>
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

      {tab === "ad-videos" && (
        <form className="grid2" onSubmit={async (e: FormEvent) => {
          e.preventDefault();
          if (!token) return;
          if (!adTitle) return fieldError("Назва рекламного відео");
          if (!adFile) return fieldError("Файл рекламного відео");
          await api.uploadAdVideo(token, { title: adTitle, file: adFile });
          setAdTitle("");
          setAdFile(null);
          setToast({ type: "success", message: "Рекламне відео завантажено" });
        }}>
          <div><label>Назва рекламного відео</label><input value={adTitle} onChange={(e) => setAdTitle(e.target.value)} /></div>
          <div><label>Файл відео</label><input type="file" accept="video/*" onChange={(e) => setAdFile(e.target.files?.[0] ?? null)} /></div>
          <div><label>&nbsp;</label><button type="submit">Завантажити</button></div>
        </form>
      )}

      {tab === "videos" && (
        <>
          <div className="row">
            <select value={videoStatusFilter} onChange={(e) => setVideoStatusFilter(e.target.value)}><option value="ALL">Всі статуси</option><option value="PUBLISHED">Опубліковано</option><option value="PENDING_MANUAL">На модерації</option><option value="BLOCKED">Заблоковано</option></select>
            <select value={videoAdFilter} onChange={(e) => setVideoAdFilter(e.target.value)}><option value="ALL">Всі типи</option><option value="AD">Рекламні</option><option value="NON_AD">Звичайні</option></select>
          </div>
          <div className="tableWrap">
            <table>
              <thead><tr><th>ID</th><th>Опис</th><th>Посилання</th><th>Статус</th><th>Тип</th><th>Перегляди</th><th>Лайки</th><th>Репости</th><th>Дії</th></tr></thead>
              <tbody>
                {videoRows.map((v) => (
                  <tr key={v.id}>
                    <td>{v.id}</td>
                    <td>{v.description ?? "-"}</td>
                    <td><a href={v.url} target="_blank" rel="noreferrer">Відкрити</a></td>
                    <td>{statusLabels[v.status] ?? v.status}</td>
                    <td>{v.is_ad ? "Рекламне" : "Звичайне"}</td>
                    <td>{v.views_count}</td>
                    <td>{v.likes_count}</td>
                    <td>{v.shares_count}</td>
                    <td className="row">
                      <button onClick={() => setEditVideo(v)}>Редагувати</button>
                      {v.status !== "BLOCKED" ? (
                        <button onClick={() => setConfirm({ title: "Підтвердження", message: `Заблокувати відео ${v.id}?`, action: async () => { if (!token) return; await api.updateVideo(token, v.id, { status: "BLOCKED" }); setToast({ type: "success", message: "Відео заблоковано" }); await load(); } })}>Заблокувати</button>
                      ) : (
                        <button onClick={() => setConfirm({ title: "Підтвердження", message: `Розблокувати відео ${v.id}?`, action: async () => { if (!token) return; await api.updateVideo(token, v.id, { status: "PUBLISHED" }); setToast({ type: "success", message: "Відео розблоковано" }); await load(); } })}>Розблокувати</button>
                      )}
                      <button onClick={() => setConfirm({ title: "Підтвердження", message: `Видалити відео ${v.id}?`, action: async () => { if (!token) return; await api.deleteVideo(token, v.id); setToast({ type: "success", message: "Відео видалено" }); await load(); } })}>Видалити</button>
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
          <div><label>&nbsp;</label><button type="submit">Зберегти</button></div>
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

      {editChallenge ? (
        <div className="modalBackdrop" onClick={() => setEditChallenge(null)}>
          <div className="modalCard" onClick={(e) => e.stopPropagation()}>
            <h3>Редагувати челендж</h3>
            <div className="grid2">
              <div><label>Назва</label><input value={editChallenge.title} onChange={(e) => setEditChallenge({ ...editChallenge, title: e.target.value })} /></div>
              <div><label>Складність</label><select value={editChallenge.difficulty} onChange={(e) => setEditChallenge({ ...editChallenge, difficulty: e.target.value })}><option value="easy">Легка</option><option value="normal">Середня</option><option value="hard">Складна</option></select></div>
              <div><label>Тривалість (днів)</label><input type="number" value={editChallenge.duration_days} onChange={(e) => setEditChallenge({ ...editChallenge, duration_days: Number(e.target.value) })} /></div>
              <div><label>XP нагорода</label><input type="number" value={editChallenge.xp_reward} onChange={(e) => setEditChallenge({ ...editChallenge, xp_reward: Number(e.target.value) })} /></div>
            </div>
            <div className="row">
              <button onClick={async () => { if (!token) return; await api.updateSponsoredChallenge(token, editChallenge.id, { title: editChallenge.title, difficulty: editChallenge.difficulty, duration_days: editChallenge.duration_days, xp_reward: editChallenge.xp_reward }); setToast({ type: "success", message: "Челендж оновлено" }); setEditChallenge(null); await load(); }}>Зберегти</button>
              <button className="button secondary" onClick={() => setEditChallenge(null)}>Скасувати</button>
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
              <div><label>Тип</label><select value={editVideo.is_ad ? "AD" : "NON_AD"} onChange={(e) => setEditVideo({ ...editVideo, is_ad: e.target.value === "AD" })}><option value="NON_AD">Звичайне</option><option value="AD">Рекламне</option></select></div>
            </div>
            <div className="row">
              <button onClick={async () => { if (!token) return; await api.updateVideo(token, editVideo.id, { description: editVideo.description ?? "", status: editVideo.status, is_ad: editVideo.is_ad }); setToast({ type: "success", message: "Відео оновлено" }); setEditVideo(null); await load(); }}>Зберегти</button>
              <button className="button secondary" onClick={() => setEditVideo(null)}>Скасувати</button>
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
    </div>
  );
}







