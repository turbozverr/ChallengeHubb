import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { resolveMediaUrl } from "../api/media";
import { useAuth } from "../auth/AuthContext";
const tabLabels = {
    dashboard: "Дашборд",
    "mobile-users": "Користувачі",
    "web-users": "Веб-користувачі",
    challenges: "Спонсорські челенджі",
    "ad-videos": "Рекламні відео",
    videos: "Відео",
    settings: "Налаштування"
};
const roleLabels = {
    ADMIN: "Адміністратор",
    MODERATOR: "Модератор",
    BUSINESS_CLIENT: "Бізнес-клієнт"
};
const difficultyLabels = {
    easy: "Легка",
    normal: "Середня",
    hard: "Складна"
};
const statusLabels = {
    DRAFT: "Чернетка",
    PUBLISHED: "Опубліковано",
    BLOCKED: "Заблоковано",
    PENDING_MANUAL: "На модерації"
};
const overviewLabels = {
    web_users_total: "Всього веб-користувачів",
    sponsored_challenges_total: "Всього спонсорських челенджів",
    videos_pending_manual: "Відео в ручній модерації",
    open_reports: "Відкриті скарги"
};
function LineChart({ labels, series, yLabel }) {
    const width = 900;
    const height = 260;
    const left = 48;
    const right = 16;
    const top = 16;
    const bottom = 36;
    const plotW = width - left - right;
    const plotH = height - top - bottom;
    const maxValue = Math.max(1, ...series.flatMap((s) => s.values));
    const xFor = (i) => left + (labels.length <= 1 ? 0 : (i / (labels.length - 1)) * plotW);
    const yFor = (v) => top + (1 - v / maxValue) * plotH;
    return (_jsxs("div", { className: "chartCard", children: [_jsxs("svg", { viewBox: `0 0 ${width} ${height}`, className: "chartSvg", role: "img", "aria-label": yLabel, children: [_jsx("line", { x1: left, y1: top, x2: left, y2: top + plotH, stroke: "#5a5a5a" }), _jsx("line", { x1: left, y1: top + plotH, x2: left + plotW, y2: top + plotH, stroke: "#5a5a5a" }), [0, 0.25, 0.5, 0.75, 1].map((m) => (_jsxs("g", { children: [_jsx("line", { x1: left, y1: yFor(maxValue * m), x2: left + plotW, y2: yFor(maxValue * m), stroke: "#2f2f2f" }), _jsx("text", { x: 8, y: yFor(maxValue * m) + 5, fill: "#b8b8b8", fontSize: "17", children: (maxValue * m).toFixed(0) })] }, m))), series.map((s) => {
                        const points = s.values.map((v, i) => `${xFor(i)},${yFor(v)}`).join(" ");
                        return _jsx("polyline", { fill: "none", stroke: s.color, strokeWidth: "2.5", points: points }, s.name);
                    }), labels.map((l, i) => (_jsx("text", { x: xFor(i), y: height - 10, fill: "#9d9d9d", fontSize: "14", textAnchor: "middle", children: l.slice(5) }, l + i)))] }), _jsx("div", { className: "chartLegend", children: series.map((s) => (_jsxs("span", { children: [_jsx("i", { style: { background: s.color } }), " ", s.name] }, s.name))) })] }));
}
export function AdminPage() {
    const { token } = useAuth();
    const [tab, setTab] = useState("dashboard");
    const [overview, setOverview] = useState({});
    const [users, setUsers] = useState([]);
    const [mobileUsers, setMobileUsers] = useState([]);
    const [challenges, setChallenges] = useState([]);
    const [videos, setVideos] = useState([]);
    const [settings, setSettings] = useState(null);
    const [dashboard, setDashboard] = useState(null);
    const [toast, setToast] = useState(null);
    const [error, setError] = useState(null);
    const [userSearch, setUserSearch] = useState("");
    const [mobileUserSearch, setMobileUserSearch] = useState("");
    const [userRoleFilter, setUserRoleFilter] = useState("ALL");
    const [challengeSearch, setChallengeSearch] = useState("");
    const [challengeDifficultyFilter, setChallengeDifficultyFilter] = useState("ALL");
    const [challengeStatusFilter, setChallengeStatusFilter] = useState("ALL");
    const [videoSearch, setVideoSearch] = useState("");
    const [videoStatusFilter, setVideoStatusFilter] = useState("ALL");
    const [videoAdFilter, setVideoAdFilter] = useState("ALL");
    const [usersPage, setUsersPage] = useState(1);
    const [mobileUsersPage, setMobileUsersPage] = useState(1);
    const [challengesPage, setChallengesPage] = useState(1);
    const [videosPage, setVideosPage] = useState(1);
    const pageSize = 8;
    const [confirm, setConfirm] = useState(null);
    const [editUser, setEditUser] = useState(null);
    const [editMobileUser, setEditMobileUser] = useState(null);
    const [editChallenge, setEditChallenge] = useState(null);
    const [editVideo, setEditVideo] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
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
    const [adFile, setAdFile] = useState(null);
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
    const videosFiltered = useMemo(() => videos.filter((v) => {
        const q = videoSearch.toLowerCase();
        const text = `${v.id} ${v.description ?? ""} ${v.url}`.toLowerCase();
        const statusOk = videoStatusFilter === "ALL" || v.status === videoStatusFilter;
        const adOk = videoAdFilter === "ALL" || (videoAdFilter === "AD" ? v.is_ad : !v.is_ad);
        return text.includes(q) && statusOk && adOk;
    }), [videos, videoSearch, videoStatusFilter, videoAdFilter]);
    const usersTotalPages = Math.max(1, Math.ceil(usersFiltered.length / pageSize));
    const mobileUsersTotalPages = Math.max(1, Math.ceil(mobileUsersFiltered.length / pageSize));
    const challengesTotalPages = Math.max(1, Math.ceil(challengesFiltered.length / pageSize));
    const videosTotalPages = Math.max(1, Math.ceil(videosFiltered.length / pageSize));
    const usersRows = usersFiltered.slice((usersPage - 1) * pageSize, usersPage * pageSize);
    const mobileUsersRows = mobileUsersFiltered.slice((mobileUsersPage - 1) * pageSize, mobileUsersPage * pageSize);
    const challengeRows = challengesFiltered.slice((challengesPage - 1) * pageSize, challengesPage * pageSize);
    const videoRows = videosFiltered.slice((videosPage - 1) * pageSize, videosPage * pageSize);
    const load = async () => {
        if (!token)
            return;
        try {
            const [ov, wu, mu, ch, vd, st, da] = await Promise.all([
                api.adminOverview(token),
                api.listWebUsers(token),
                api.listMobileUsers(token),
                api.listSponsoredChallenges(token),
                api.adminVideos(token),
                api.getSettings(token),
                api.adminDashboardAnalytics(token)
            ]);
            setOverview(ov);
            setUsers(wu);
            setMobileUsers(mu);
            setChallenges(ch);
            setVideos(vd);
            setSettings(st);
            setDashboard(da);
            setError(null);
        }
        catch (e) {
            setError(e instanceof Error ? e.message : "Помилка завантаження");
            setToast({ type: "error", message: "Не вдалося завантажити дані" });
        }
    };
    useEffect(() => {
        void load();
    }, [token]);
    useEffect(() => {
        if (!toast)
            return;
        const t = setTimeout(() => setToast(null), 2800);
        return () => clearTimeout(t);
    }, [toast]);
    useEffect(() => setUsersPage(1), [userSearch, userRoleFilter]);
    useEffect(() => setMobileUsersPage(1), [mobileUserSearch]);
    useEffect(() => setChallengesPage(1), [challengeSearch, challengeDifficultyFilter, challengeStatusFilter]);
    useEffect(() => setVideosPage(1), [videoSearch, videoStatusFilter, videoAdFilter]);
    const fieldError = (name) => setToast({ type: "error", message: `Заповніть поле: ${name}` });
    const dayLabels = useMemo(() => (dashboard ? Array.from(new Set(dashboard.dau_wau_mau.map((p) => p.date.split("|")[0]))) : []), [dashboard]);
    const dauSeries = useMemo(() => dayLabels.map((d) => dashboard?.dau_wau_mau.find((p) => p.date === `${d}|DAU`)?.value ?? 0), [dashboard, dayLabels]);
    const wauSeries = useMemo(() => dayLabels.map((d) => dashboard?.dau_wau_mau.find((p) => p.date === `${d}|WAU`)?.value ?? 0), [dashboard, dayLabels]);
    const mauSeries = useMemo(() => dayLabels.map((d) => dashboard?.dau_wau_mau.find((p) => p.date === `${d}|MAU`)?.value ?? 0), [dashboard, dayLabels]);
    return (_jsxs("div", { className: "card", children: [_jsx("h1", { children: "\u041F\u0430\u043D\u0435\u043B\u044C \u0430\u0434\u043C\u0456\u043D\u0456\u0441\u0442\u0440\u0430\u0442\u043E\u0440\u0430" }), toast ? _jsx("div", { className: `toast ${toast.type}`, children: toast.message }) : null, error ? _jsx("p", { className: "error", children: error }) : null, _jsx("div", { className: "tabs", children: ["dashboard", "mobile-users", "web-users", "challenges", "ad-videos", "videos", "settings"].map((t) => (_jsx("button", { className: tab === t ? "tab active" : "tab", onClick: () => setTab(t), children: tabLabels[t] }, t))) }), tab === "dashboard" && (_jsxs(_Fragment, { children: [_jsx("div", { className: "grid3", children: Object.entries(overview).map(([k, v]) => (_jsxs("div", { className: "stat", children: [_jsx("strong", { children: v }), _jsx("span", { children: overviewLabels[k] ?? k })] }, k))) }), _jsxs("div", { className: "chartGrid", children: [_jsxs("section", { children: [_jsx("h2", { children: "\u0429\u043E\u0434\u0435\u043D\u043D\u0430, \u0442\u0438\u0436\u043D\u0435\u0432\u0430 \u0442\u0430 \u043C\u0456\u0441\u044F\u0447\u043D\u0430 \u0430\u043A\u0442\u0438\u0432\u043D\u0456\u0441\u0442\u044C \u043A\u043E\u0440\u0438\u0441\u0442\u0443\u0432\u0430\u0447\u0456\u0432" }), _jsx(LineChart, { labels: dayLabels, yLabel: "\u0410\u043A\u0442\u0438\u0432\u043D\u0456 \u043A\u043E\u0440\u0438\u0441\u0442\u0443\u0432\u0430\u0447\u0456", series: [
                                            { name: "Активні за день", color: "#AD46FF", values: dauSeries },
                                            { name: "Активні за 7 днів", color: "#F6339A", values: wauSeries },
                                            { name: "Активні за 30 днів", color: "#36CFC9", values: mauSeries }
                                        ] })] }), _jsxs("section", { children: [_jsx("h2", { children: "\u0420\u0435\u0454\u0441\u0442\u0440\u0430\u0446\u0456\u0457 \u043C\u043E\u0431\u0456\u043B\u044C\u043D\u0438\u0445 \u043A\u043E\u0440\u0438\u0441\u0442\u0443\u0432\u0430\u0447\u0456\u0432" }), _jsx(LineChart, { labels: dashboard?.mobile_registrations.map((r) => r.date) ?? [], yLabel: "\u0420\u0435\u0454\u0441\u0442\u0440\u0430\u0446\u0456\u0457", series: [
                                            { name: "Нові користувачі", color: "#AD46FF", values: dashboard?.mobile_registrations.map((r) => r.users) ?? [] }
                                        ] })] })] }), _jsxs("div", { className: "chartGrid", children: [_jsxs("section", { children: [_jsx("h2", { children: "\u0421\u0435\u0440\u0435\u0434\u043D\u0456\u0439 \u0447\u0430\u0441 \u0440\u0456\u0448\u0435\u043D\u043D\u044F \u043C\u043E\u0434\u0435\u0440\u0430\u0442\u043E\u0440\u0430 (\u0433\u043E\u0434\u0438\u043D\u0438)" }), _jsx(LineChart, { labels: dashboard?.moderation_decision_time_hours.map((p) => p.date) ?? [], yLabel: "\u0413\u043E\u0434\u0438\u043D\u0438", series: [{ name: "Середній час", color: "#F6339A", values: dashboard?.moderation_decision_time_hours.map((p) => p.value) ?? [] }] })] }), _jsxs("section", { children: [_jsx("h2", { children: "\u0417\u0440\u043E\u0441\u0442\u0430\u043D\u043D\u044F \u043A\u043E\u043D\u0442\u0435\u043D\u0442\u0443 (\u0440\u0435\u043A\u043B\u0430\u043C\u043D\u0456 \u0442\u0430 \u0437\u0432\u0438\u0447\u0430\u0439\u043D\u0456 \u0432\u0456\u0434\u0435\u043E)" }), _jsx(LineChart, { labels: dashboard?.content_growth.map((p) => p.date) ?? [], yLabel: "\u041A\u0456\u043B\u044C\u043A\u0456\u0441\u0442\u044C \u0432\u0456\u0434\u0435\u043E", series: [
                                            { name: "Рекламні", color: "#AD46FF", values: dashboard?.content_growth.map((p) => p.ad_videos) ?? [] },
                                            { name: "Звичайні", color: "#36CFC9", values: dashboard?.content_growth.map((p) => p.regular_videos) ?? [] }
                                        ] })] })] }), _jsxs("div", { className: "chartGrid", children: [_jsxs("section", { children: [_jsx("h2", { children: "\u0422\u043E\u043F \u0447\u0435\u043B\u0435\u043D\u0434\u0436\u0456 \u0437\u0430 \u0437\u0430\u043B\u0443\u0447\u0435\u043D\u043D\u044F\u043C \u0430\u0443\u0434\u0438\u0442\u043E\u0440\u0456\u0457" }), _jsx(LineChart, { labels: dashboard?.top_challenges_engagement.map((c, i) => `${i + 1}`) ?? [], yLabel: "\u0417\u043D\u0430\u0447\u0435\u043D\u043D\u044F", series: [
                                            { name: "Перегляди", color: "#AD46FF", values: dashboard?.top_challenges_engagement.map((c) => c.views) ?? [] },
                                            { name: "Сабміти", color: "#F6339A", values: dashboard?.top_challenges_engagement.map((c) => c.submissions) ?? [] },
                                            { name: "Репости", color: "#36CFC9", values: dashboard?.top_challenges_engagement.map((c) => c.shares) ?? [] }
                                        ] })] }), _jsxs("section", { children: [_jsx("h2", { children: "\u042F\u043A\u0456\u0441\u0442\u044C AI-\u043C\u043E\u0434\u0435\u0440\u0430\u0446\u0456\u0457 (\u0447\u0430\u0441\u0442\u043A\u0430 \u0437\u043C\u0456\u043D\u0435\u043D\u0438\u0445 \u0440\u0456\u0448\u0435\u043D\u044C)" }), _jsx(LineChart, { labels: dashboard?.ai_quality_overturned_rate.map((p) => p.date) ?? [], yLabel: "%", series: [{ name: "Змінені рішення, %", color: "#F6339A", values: dashboard?.ai_quality_overturned_rate.map((p) => p.value) ?? [] }] })] })] })] })), tab === "web-users" && (_jsxs(_Fragment, { children: [_jsxs("form", { className: "grid2", onSubmit: async (e) => {
                            e.preventDefault();
                            if (!token)
                                return;
                            if (!newUser.full_name)
                                return fieldError("ПІБ");
                            if (!newUser.email)
                                return fieldError("Email");
                            if (!newUser.password)
                                return fieldError("Пароль");
                            await api.createWebUser(token, { ...newUser, company_name: newUser.company_name || undefined });
                            setNewUser({ full_name: "", email: "", password: "", role: "MODERATOR", company_name: "" });
                            setToast({ type: "success", message: "Користувача створено" });
                            await load();
                        }, children: [_jsxs("div", { children: [_jsx("label", { children: "\u041F\u0406\u0411" }), _jsx("input", { value: newUser.full_name, onChange: (e) => setNewUser((s) => ({ ...s, full_name: e.target.value })) })] }), _jsxs("div", { children: [_jsx("label", { children: "Email" }), _jsx("input", { value: newUser.email, onChange: (e) => setNewUser((s) => ({ ...s, email: e.target.value })) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u041F\u0430\u0440\u043E\u043B\u044C" }), _jsx("input", { type: "password", value: newUser.password, onChange: (e) => setNewUser((s) => ({ ...s, password: e.target.value })) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0420\u043E\u043B\u044C" }), _jsxs("select", { value: newUser.role, onChange: (e) => setNewUser((s) => ({ ...s, role: e.target.value })), children: [_jsx("option", { value: "MODERATOR", children: "\u041C\u043E\u0434\u0435\u0440\u0430\u0442\u043E\u0440" }), _jsx("option", { value: "BUSINESS_CLIENT", children: "\u0411\u0456\u0437\u043D\u0435\u0441-\u043A\u043B\u0456\u0454\u043D\u0442" }), _jsx("option", { value: "ADMIN", children: "\u0410\u0434\u043C\u0456\u043D\u0456\u0441\u0442\u0440\u0430\u0442\u043E\u0440" })] })] }), _jsxs("div", { children: [_jsx("label", { children: "\u041A\u043E\u043C\u043F\u0430\u043D\u0456\u044F (\u043D\u0435\u043E\u0431\u043E\u0432'\u044F\u0437\u043A\u043E\u0432\u043E)" }), _jsx("input", { value: newUser.company_name, onChange: (e) => setNewUser((s) => ({ ...s, company_name: e.target.value })) })] }), _jsx("div", { className: "formSubmit", children: _jsx("button", { type: "submit", children: "\u0421\u0442\u0432\u043E\u0440\u0438\u0442\u0438" }) })] }), _jsx("hr", { className: "sectionDivider" }), _jsxs("div", { className: "filtersRow", children: [_jsx("input", { placeholder: "\u041F\u043E\u0448\u0443\u043A \u0437\u0430 ID, \u041F\u0406\u0411, Email", value: userSearch, onChange: (e) => setUserSearch(e.target.value) }), _jsxs("select", { value: userRoleFilter, onChange: (e) => setUserRoleFilter(e.target.value), children: [_jsx("option", { value: "ALL", children: "\u0412\u0441\u0456 \u0440\u043E\u043B\u0456" }), _jsx("option", { value: "ADMIN", children: "\u0410\u0434\u043C\u0456\u043D\u0456\u0441\u0442\u0440\u0430\u0442\u043E\u0440" }), _jsx("option", { value: "MODERATOR", children: "\u041C\u043E\u0434\u0435\u0440\u0430\u0442\u043E\u0440" }), _jsx("option", { value: "BUSINESS_CLIENT", children: "\u0411\u0456\u0437\u043D\u0435\u0441-\u043A\u043B\u0456\u0454\u043D\u0442" })] })] }), _jsx("div", { className: "tableWrap", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "ID" }), _jsx("th", { children: "\u0406\u043C'\u044F" }), _jsx("th", { children: "Email" }), _jsx("th", { children: "\u0420\u043E\u043B\u044C" }), _jsx("th", { children: "\u0414\u0456\u0457" })] }) }), _jsx("tbody", { children: usersRows.map((u) => (_jsxs("tr", { children: [_jsx("td", { children: u.id }), _jsx("td", { children: u.full_name }), _jsx("td", { children: u.email }), _jsx("td", { children: roleLabels[u.role] ?? u.role }), _jsx("td", { children: _jsxs("div", { className: "actionBar", children: [_jsx("button", { className: "actionBtn iconOnly edit", title: "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438", "aria-label": "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438", onClick: () => setEditUser(u), children: _jsx("span", { className: "iconGlyph pencil", children: "\u270E" }) }), _jsx("button", { className: "actionBtn iconOnly danger", title: "\u0412\u0438\u0434\u0430\u043B\u0438\u0442\u0438", "aria-label": "\u0412\u0438\u0434\u0430\u043B\u0438\u0442\u0438", onClick: () => setConfirm({ title: "Підтвердження", message: `Видалити користувача ${u.full_name}?`, action: async () => { if (!token)
                                                                    return; await api.deleteWebUser(token, u.id); setToast({ type: "success", message: "Користувача видалено" }); await load(); } }), children: _jsx("span", { className: "iconGlyph delete", children: "\u232B" }) })] }) })] }, u.id))) })] }) }), _jsxs("div", { className: "pagination", children: [_jsx("button", { disabled: usersPage <= 1, onClick: () => setUsersPage((p) => p - 1), children: "\u041F\u043E\u043F\u0435\u0440\u0435\u0434\u043D\u044F" }), _jsxs("span", { children: ["\u0421\u0442\u043E\u0440\u0456\u043D\u043A\u0430 ", usersPage, " \u0437 ", usersTotalPages] }), _jsx("button", { disabled: usersPage >= usersTotalPages, onClick: () => setUsersPage((p) => p + 1), children: "\u041D\u0430\u0441\u0442\u0443\u043F\u043D\u0430" })] })] })), tab === "mobile-users" && (_jsxs(_Fragment, { children: [_jsx("div", { className: "filtersRow", children: _jsx("input", { placeholder: "\u041F\u043E\u0448\u0443\u043A \u0437\u0430 ID, @\u043B\u043E\u0433\u0456\u043D\u043E\u043C, \u0456\u043C\u0435\u043D\u0435\u043C \u0430\u0431\u043E Email", value: mobileUserSearch, onChange: (e) => setMobileUserSearch(e.target.value) }) }), _jsx("div", { className: "tableWrap", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "ID" }), _jsx("th", { children: "@\u043B\u043E\u0433\u0456\u043D" }), _jsx("th", { children: "\u0406\u043C'\u044F" }), _jsx("th", { children: "Email" }), _jsx("th", { children: "XP" }), _jsx("th", { children: "Premium" }), _jsx("th", { children: "\u0421\u0442\u0430\u0442\u0443\u0441" }), _jsx("th", { children: "\u0414\u0456\u0457" })] }) }), _jsx("tbody", { children: mobileUsersRows.map((u) => (_jsxs("tr", { children: [_jsx("td", { children: u.id }), _jsxs("td", { children: ["@", u.username] }), _jsx("td", { children: u.full_name }), _jsx("td", { children: u.email }), _jsx("td", { children: u.xp }), _jsx("td", { children: u.is_premium ? "Так" : "Ні" }), _jsx("td", { children: u.status === "ACTIVE" ? "Активний" : u.status }), _jsx("td", { children: _jsxs("div", { className: "actionBar", children: [_jsx("button", { className: "actionBtn iconOnly edit", title: "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438 \u0456\u043C'\u044F", "aria-label": "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438 \u0456\u043C'\u044F", onClick: () => setEditMobileUser(u), children: _jsx("span", { className: "iconGlyph pencil", children: "\u270E" }) }), _jsx("button", { className: "actionBtn iconOnly danger", title: "\u0412\u0438\u0434\u0430\u043B\u0438\u0442\u0438", "aria-label": "\u0412\u0438\u0434\u0430\u043B\u0438\u0442\u0438", onClick: () => setConfirm({ title: "Підтвердження", message: `Видалити користувача ${u.full_name}?`, action: async () => { if (!token)
                                                                    return; await api.deleteMobileUser(token, u.id); setToast({ type: "success", message: "Користувача видалено" }); await load(); } }), children: _jsx("span", { className: "iconGlyph delete", children: "\u232B" }) })] }) })] }, u.id))) })] }) }), _jsxs("div", { className: "pagination", children: [_jsx("button", { disabled: mobileUsersPage <= 1, onClick: () => setMobileUsersPage((p) => p - 1), children: "\u041F\u043E\u043F\u0435\u0440\u0435\u0434\u043D\u044F" }), _jsxs("span", { children: ["\u0421\u0442\u043E\u0440\u0456\u043D\u043A\u0430 ", mobileUsersPage, " \u0437 ", mobileUsersTotalPages] }), _jsx("button", { disabled: mobileUsersPage >= mobileUsersTotalPages, onClick: () => setMobileUsersPage((p) => p + 1), children: "\u041D\u0430\u0441\u0442\u0443\u043F\u043D\u0430" })] })] })), tab === "challenges" && (_jsxs(_Fragment, { children: [_jsxs("form", { className: "grid2", onSubmit: async (e) => {
                            e.preventDefault();
                            if (!token)
                                return;
                            if (!newChallenge.title)
                                return fieldError("Назва");
                            if (!newChallenge.description)
                                return fieldError("Опис");
                            if (!newChallenge.client_id)
                                return fieldError("Бізнес-клієнт");
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
                        }, children: [_jsxs("div", { children: [_jsx("label", { children: "\u041D\u0430\u0437\u0432\u0430 \u0447\u0435\u043B\u0435\u043D\u0434\u0436\u0443" }), _jsx("input", { value: newChallenge.title, onChange: (e) => setNewChallenge((s) => ({ ...s, title: e.target.value })) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0411\u0456\u0437\u043D\u0435\u0441-\u043A\u043B\u0456\u0454\u043D\u0442" }), _jsxs("select", { value: newChallenge.client_id, onChange: (e) => setNewChallenge((s) => ({ ...s, client_id: e.target.value })), children: [_jsx("option", { value: "", children: "\u041E\u0431\u0435\u0440\u0456\u0442\u044C" }), businessClients.map((c) => _jsx("option", { value: c.id, children: c.full_name }, c.id))] })] }), _jsxs("div", { children: [_jsx("label", { children: "\u041E\u043F\u0438\u0441" }), _jsx("textarea", { value: newChallenge.description, onChange: (e) => setNewChallenge((s) => ({ ...s, description: e.target.value })) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0421\u043A\u043B\u0430\u0434\u043D\u0456\u0441\u0442\u044C" }), _jsxs("select", { value: newChallenge.difficulty, onChange: (e) => setNewChallenge((s) => ({ ...s, difficulty: e.target.value })), children: [_jsx("option", { value: "easy", children: "\u041B\u0435\u0433\u043A\u0430" }), _jsx("option", { value: "normal", children: "\u0421\u0435\u0440\u0435\u0434\u043D\u044F" }), _jsx("option", { value: "hard", children: "\u0421\u043A\u043B\u0430\u0434\u043D\u0430" })] })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0422\u0440\u0438\u0432\u0430\u043B\u0456\u0441\u0442\u044C (\u0434\u043D\u0456\u0432)" }), _jsx("input", { type: "number", value: newChallenge.duration_days, onChange: (e) => setNewChallenge((s) => ({ ...s, duration_days: Number(e.target.value) })) })] }), _jsxs("div", { children: [_jsx("label", { children: "XP \u043D\u0430\u0433\u043E\u0440\u043E\u0434\u0430" }), _jsx("input", { type: "number", value: newChallenge.xp_reward, onChange: (e) => setNewChallenge((s) => ({ ...s, xp_reward: Number(e.target.value) })) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u041F\u0440\u043E\u043C\u043E\u043A\u043E\u0434\u0438" }), _jsxs("select", { value: newChallenge.promo_mode, onChange: (e) => setNewChallenge((s) => ({ ...s, promo_mode: e.target.value })), children: [_jsx("option", { value: "NONE", children: "\u0411\u0435\u0437 \u043F\u0440\u043E\u043C\u043E\u043A\u043E\u0434\u0443" }), _jsx("option", { value: "SINGLE", children: "\u041E\u0434\u0438\u043D \u043A\u043E\u0434 \u0434\u043B\u044F \u0432\u0441\u0456\u0445" }), _jsx("option", { value: "LIST", children: "\u0421\u043F\u0438\u0441\u043E\u043A \u043A\u043E\u0434\u0456\u0432" })] })] }), _jsxs("div", { children: [newChallenge.promo_mode === "SINGLE" ? _jsx("input", { placeholder: "\u041F\u0440\u043E\u043C\u043E\u043A\u043E\u0434", value: newChallenge.promo_single_code, onChange: (e) => setNewChallenge((s) => ({ ...s, promo_single_code: e.target.value })) }) : null, newChallenge.promo_mode === "LIST" ? _jsx("textarea", { placeholder: "\u041F\u0440\u043E\u043C\u043E\u043A\u043E\u0434\u0438 \u043F\u043E \u043E\u0434\u043D\u043E\u043C\u0443 \u043D\u0430 \u0440\u044F\u0434\u043E\u043A", value: newChallenge.promo_codes_text, onChange: (e) => setNewChallenge((s) => ({ ...s, promo_codes_text: e.target.value })) }) : null] }), _jsxs("div", { children: [_jsx("label", { children: "\u00A0" }), _jsx("button", { type: "submit", children: "\u0421\u0442\u0432\u043E\u0440\u0438\u0442\u0438" })] })] }), _jsx("hr", { className: "sectionDivider" }), _jsxs("div", { className: "filtersRow", children: [_jsx("input", { placeholder: "\u041F\u043E\u0448\u0443\u043A \u0437\u0430 ID, \u043D\u0430\u0437\u0432\u043E\u044E, \u043A\u043E\u043C\u043F\u0430\u043D\u0456\u0454\u044E", value: challengeSearch, onChange: (e) => setChallengeSearch(e.target.value) }), _jsxs("select", { value: challengeDifficultyFilter, onChange: (e) => setChallengeDifficultyFilter(e.target.value), children: [_jsx("option", { value: "ALL", children: "\u0412\u0441\u044F \u0441\u043A\u043B\u0430\u0434\u043D\u0456\u0441\u0442\u044C" }), _jsx("option", { value: "easy", children: "\u041B\u0435\u0433\u043A\u0430" }), _jsx("option", { value: "normal", children: "\u0421\u0435\u0440\u0435\u0434\u043D\u044F" }), _jsx("option", { value: "hard", children: "\u0421\u043A\u043B\u0430\u0434\u043D\u0430" })] }), _jsxs("select", { value: challengeStatusFilter, onChange: (e) => setChallengeStatusFilter(e.target.value), children: [_jsx("option", { value: "ALL", children: "\u0412\u0441\u0456 \u0441\u0442\u0430\u0442\u0443\u0441\u0438" }), _jsx("option", { value: "DRAFT", children: "\u0427\u0435\u0440\u043D\u0435\u0442\u043A\u0430" }), _jsx("option", { value: "PUBLISHED", children: "\u041E\u043F\u0443\u0431\u043B\u0456\u043A\u043E\u0432\u0430\u043D\u043E" }), _jsx("option", { value: "BLOCKED", children: "\u0417\u0430\u0431\u043B\u043E\u043A\u043E\u0432\u0430\u043D\u043E" })] })] }), _jsx("div", { className: "tableWrap", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "ID" }), _jsx("th", { children: "\u041D\u0430\u0437\u0432\u0430" }), _jsx("th", { children: "\u0421\u043A\u043B\u0430\u0434\u043D\u0456\u0441\u0442\u044C" }), _jsx("th", { children: "\u0414\u043D\u0456\u0432" }), _jsx("th", { children: "XP" }), _jsx("th", { children: "\u0421\u0442\u0430\u0442\u0443\u0441" }), _jsx("th", { children: "\u0414\u0456\u0457" })] }) }), _jsx("tbody", { children: challengeRows.map((c) => (_jsxs("tr", { children: [_jsx("td", { children: c.id }), _jsx("td", { children: c.title }), _jsx("td", { children: difficultyLabels[c.difficulty] ?? c.difficulty }), _jsx("td", { children: c.duration_days }), _jsx("td", { children: c.xp_reward }), _jsx("td", { children: statusLabels[c.status] ?? c.status }), _jsx("td", { children: _jsxs("div", { className: "actionBar", children: [_jsx("button", { className: "actionBtn iconOnly edit", title: "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438", "aria-label": "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438", onClick: () => setEditChallenge(c), children: _jsx("span", { className: "iconGlyph pencil", children: "\u270E" }) }), c.status === "PUBLISHED" ? (_jsx("button", { className: "actionBtn iconOnly publish", title: "\u0412\u0436\u0435 \u043E\u043F\u0443\u0431\u043B\u0456\u043A\u043E\u0432\u0430\u043D\u043E", "aria-label": "\u0412\u0436\u0435 \u043E\u043F\u0443\u0431\u043B\u0456\u043A\u043E\u0432\u0430\u043D\u043E", disabled: true, children: "\u2713" })) : (_jsx("button", { className: "actionBtn iconOnly publish", title: "\u041F\u0443\u0431\u043B\u0456\u043A\u0443\u0432\u0430\u0442\u0438", "aria-label": "\u041F\u0443\u0431\u043B\u0456\u043A\u0443\u0432\u0430\u0442\u0438", onClick: async () => { if (!token)
                                                                return; await api.publishSponsoredChallenge(token, c.id); setToast({ type: "success", message: "Челендж опубліковано" }); await load(); }, children: "\u2191" })), _jsx("button", { className: "actionBtn iconOnly danger", title: "\u0412\u0438\u0434\u0430\u043B\u0438\u0442\u0438", "aria-label": "\u0412\u0438\u0434\u0430\u043B\u0438\u0442\u0438", onClick: () => setConfirm({ title: "Підтвердження", message: `Видалити челендж ${c.title}?`, action: async () => { if (!token)
                                                                    return; await api.deleteSponsoredChallenge(token, c.id); setToast({ type: "success", message: "Челендж видалено" }); await load(); } }), children: _jsx("span", { className: "iconGlyph delete", children: "\u232B" }) })] }) })] }, c.id))) })] }) }), _jsxs("div", { className: "pagination", children: [_jsx("button", { disabled: challengesPage <= 1, onClick: () => setChallengesPage((p) => p - 1), children: "\u041F\u043E\u043F\u0435\u0440\u0435\u0434\u043D\u044F" }), _jsxs("span", { children: ["\u0421\u0442\u043E\u0440\u0456\u043D\u043A\u0430 ", challengesPage, " \u0437 ", challengesTotalPages] }), _jsx("button", { disabled: challengesPage >= challengesTotalPages, onClick: () => setChallengesPage((p) => p + 1), children: "\u041D\u0430\u0441\u0442\u0443\u043F\u043D\u0430" })] })] })), tab === "ad-videos" && (_jsxs("form", { className: "grid2", onSubmit: async (e) => {
                    e.preventDefault();
                    if (!token)
                        return;
                    if (!adTitle)
                        return fieldError("Назва рекламного відео");
                    if (!adFile)
                        return fieldError("Файл рекламного відео");
                    await api.uploadAdVideo(token, { title: adTitle, file: adFile });
                    setAdTitle("");
                    setAdFile(null);
                    setToast({ type: "success", message: "Рекламне відео завантажено" });
                }, children: [_jsxs("div", { children: [_jsx("label", { children: "\u041D\u0430\u0437\u0432\u0430 \u0440\u0435\u043A\u043B\u0430\u043C\u043D\u043E\u0433\u043E \u0432\u0456\u0434\u0435\u043E" }), _jsx("input", { value: adTitle, onChange: (e) => setAdTitle(e.target.value) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0424\u0430\u0439\u043B \u0432\u0456\u0434\u0435\u043E" }), _jsx("input", { type: "file", accept: "video/*", onChange: (e) => setAdFile(e.target.files?.[0] ?? null) })] }), _jsx("div", { className: "formSubmit", children: _jsx("button", { type: "submit", children: "\u0417\u0430\u0432\u0430\u043D\u0442\u0430\u0436\u0438\u0442\u0438" }) })] })), tab === "videos" && (_jsxs(_Fragment, { children: [_jsxs("div", { className: "filtersRow", children: [_jsx("input", { placeholder: "\u041F\u043E\u0448\u0443\u043A \u0437\u0430 ID, \u043E\u043F\u0438\u0441\u043E\u043C \u0430\u0431\u043E URL", value: videoSearch, onChange: (e) => setVideoSearch(e.target.value) }), _jsxs("select", { value: videoStatusFilter, onChange: (e) => setVideoStatusFilter(e.target.value), children: [_jsx("option", { value: "ALL", children: "\u0412\u0441\u0456 \u0441\u0442\u0430\u0442\u0443\u0441\u0438" }), _jsx("option", { value: "PUBLISHED", children: "\u041E\u043F\u0443\u0431\u043B\u0456\u043A\u043E\u0432\u0430\u043D\u043E" }), _jsx("option", { value: "PENDING_MANUAL", children: "\u041D\u0430 \u043C\u043E\u0434\u0435\u0440\u0430\u0446\u0456\u0457" }), _jsx("option", { value: "BLOCKED", children: "\u0417\u0430\u0431\u043B\u043E\u043A\u043E\u0432\u0430\u043D\u043E" })] }), _jsxs("select", { value: videoAdFilter, onChange: (e) => setVideoAdFilter(e.target.value), children: [_jsx("option", { value: "ALL", children: "\u0412\u0441\u0456 \u0442\u0438\u043F\u0438" }), _jsx("option", { value: "AD", children: "\u0420\u0435\u043A\u043B\u0430\u043C\u043D\u0456" }), _jsx("option", { value: "NON_AD", children: "\u0417\u0432\u0438\u0447\u0430\u0439\u043D\u0456" })] })] }), _jsx("div", { className: "tableWrap", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "ID" }), _jsx("th", { children: "\u041E\u043F\u0438\u0441" }), _jsx("th", { children: "\u041F\u043E\u0441\u0438\u043B\u0430\u043D\u043D\u044F" }), _jsx("th", { children: "\u0421\u0442\u0430\u0442\u0443\u0441" }), _jsx("th", { children: "\u0422\u0438\u043F" }), _jsx("th", { children: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434\u0438" }), _jsx("th", { children: "\u041B\u0430\u0439\u043A\u0438" }), _jsx("th", { children: "\u0420\u0435\u043F\u043E\u0441\u0442\u0438" }), _jsx("th", { children: "\u0414\u0456\u0457" })] }) }), _jsx("tbody", { children: videoRows.map((v) => (_jsxs("tr", { children: [_jsx("td", { children: v.id }), _jsx("td", { children: v.description ?? "-" }), _jsx("td", { children: _jsx("button", { className: "actionBtn iconOnly view", title: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434", "aria-label": "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434", onClick: () => setPreviewUrl(resolveMediaUrl(v.url)), children: "\u25B6" }) }), _jsx("td", { children: statusLabels[v.status] ?? v.status }), _jsx("td", { children: v.is_ad ? "Рекламне" : "Звичайне" }), _jsx("td", { children: v.views_count }), _jsx("td", { children: v.likes_count }), _jsx("td", { children: v.shares_count }), _jsx("td", { children: _jsxs("div", { className: "actionBar", children: [_jsx("button", { className: "actionBtn iconOnly edit", title: "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438", "aria-label": "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438", onClick: () => setEditVideo(v), children: _jsx("span", { className: "iconGlyph pencil", children: "\u270E" }) }), v.status !== "BLOCKED" ? (_jsx("button", { className: "actionBtn iconOnly warning", title: "\u0417\u0430\u0431\u043B\u043E\u043A\u0443\u0432\u0430\u0442\u0438", "aria-label": "\u0417\u0430\u0431\u043B\u043E\u043A\u0443\u0432\u0430\u0442\u0438", onClick: () => setConfirm({ title: "Підтвердження", message: `Заблокувати відео ${v.id}?`, action: async () => { if (!token)
                                                                    return; await api.updateVideo(token, v.id, { status: "BLOCKED" }); setToast({ type: "success", message: "Відео заблоковано" }); await load(); } }), children: "\u00D7" })) : (_jsx("button", { className: "actionBtn iconOnly publish", title: "\u0420\u043E\u0437\u0431\u043B\u043E\u043A\u0443\u0432\u0430\u0442\u0438", "aria-label": "\u0420\u043E\u0437\u0431\u043B\u043E\u043A\u0443\u0432\u0430\u0442\u0438", onClick: () => setConfirm({ title: "Підтвердження", message: `Розблокувати відео ${v.id}?`, action: async () => { if (!token)
                                                                    return; await api.updateVideo(token, v.id, { status: "PUBLISHED" }); setToast({ type: "success", message: "Відео розблоковано" }); await load(); } }), children: "\u21BA" })), _jsx("button", { className: "actionBtn iconOnly danger", title: "\u0412\u0438\u0434\u0430\u043B\u0438\u0442\u0438", "aria-label": "\u0412\u0438\u0434\u0430\u043B\u0438\u0442\u0438", onClick: () => setConfirm({ title: "Підтвердження", message: `Видалити відео ${v.id}?`, action: async () => { if (!token)
                                                                    return; await api.deleteVideo(token, v.id); setToast({ type: "success", message: "Відео видалено" }); await load(); } }), children: _jsx("span", { className: "iconGlyph delete", children: "\u232B" }) })] }) })] }, v.id))) })] }) }), _jsxs("div", { className: "pagination", children: [_jsx("button", { disabled: videosPage <= 1, onClick: () => setVideosPage((p) => p - 1), children: "\u041F\u043E\u043F\u0435\u0440\u0435\u0434\u043D\u044F" }), _jsxs("span", { children: ["\u0421\u0442\u043E\u0440\u0456\u043D\u043A\u0430 ", videosPage, " \u0437 ", videosTotalPages] }), _jsx("button", { disabled: videosPage >= videosTotalPages, onClick: () => setVideosPage((p) => p + 1), children: "\u041D\u0430\u0441\u0442\u0443\u043F\u043D\u0430" })] })] })), tab === "settings" && settings && (_jsxs("form", { className: "grid2", onSubmit: async (e) => {
                    e.preventDefault();
                    if (!token)
                        return;
                    await api.updateSettings(token, {
                        ai_confidence_threshold: settings.ai_confidence_threshold,
                        report_limit: settings.report_limit
                    });
                    setToast({ type: "success", message: "Налаштування збережено" });
                }, children: [_jsxs("div", { children: [_jsx("label", { children: "\u041F\u043E\u0440\u0456\u0433 \u0432\u043F\u0435\u0432\u043D\u0435\u043D\u043E\u0441\u0442\u0456 AI" }), _jsx("input", { type: "number", step: "0.01", value: settings.ai_confidence_threshold, onChange: (e) => setSettings((s) => (s ? { ...s, ai_confidence_threshold: Number(e.target.value) } : s)) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u041B\u0456\u043C\u0456\u0442 \u0441\u043A\u0430\u0440\u0433 \u0434\u043B\u044F \u0430\u0432\u0442\u043E\u043F\u0440\u0438\u0445\u043E\u0432\u0443\u0432\u0430\u043D\u043D\u044F" }), _jsx("input", { type: "number", value: settings.report_limit, onChange: (e) => setSettings((s) => (s ? { ...s, report_limit: Number(e.target.value) } : s)) })] }), _jsx("div", { className: "formSubmit", children: _jsx("button", { type: "submit", children: "\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438" }) })] })), editUser ? (_jsx("div", { className: "modalBackdrop", onClick: () => setEditUser(null), children: _jsxs("div", { className: "modalCard", onClick: (e) => e.stopPropagation(), children: [_jsx("h3", { children: "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438 \u043A\u043E\u0440\u0438\u0441\u0442\u0443\u0432\u0430\u0447\u0430" }), _jsxs("div", { className: "grid2", children: [_jsxs("div", { children: [_jsx("label", { children: "\u0406\u043C'\u044F" }), _jsx("input", { value: editUser.full_name, onChange: (e) => setEditUser({ ...editUser, full_name: e.target.value }) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0420\u043E\u043B\u044C" }), _jsxs("select", { value: editUser.role, onChange: (e) => setEditUser({ ...editUser, role: e.target.value }), children: [_jsx("option", { value: "ADMIN", children: "\u0410\u0434\u043C\u0456\u043D\u0456\u0441\u0442\u0440\u0430\u0442\u043E\u0440" }), _jsx("option", { value: "MODERATOR", children: "\u041C\u043E\u0434\u0435\u0440\u0430\u0442\u043E\u0440" }), _jsx("option", { value: "BUSINESS_CLIENT", children: "\u0411\u0456\u0437\u043D\u0435\u0441-\u043A\u043B\u0456\u0454\u043D\u0442" })] })] })] }), _jsxs("div", { className: "row", children: [_jsx("button", { onClick: async () => { if (!token)
                                        return; await api.updateWebUser(token, editUser.id, { full_name: editUser.full_name, role: editUser.role }); setToast({ type: "success", message: "Користувача оновлено" }); setEditUser(null); await load(); }, children: "\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438" }), _jsx("button", { className: "button secondary", onClick: () => setEditUser(null), children: "\u0421\u043A\u0430\u0441\u0443\u0432\u0430\u0442\u0438" })] })] }) })) : null, editMobileUser ? (_jsx("div", { className: "modalBackdrop", onClick: () => setEditMobileUser(null), children: _jsxs("div", { className: "modalCard", onClick: (e) => e.stopPropagation(), children: [_jsx("h3", { children: "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438 \u043A\u043E\u0440\u0438\u0441\u0442\u0443\u0432\u0430\u0447\u0430" }), _jsxs("div", { className: "grid2", children: [_jsxs("div", { children: [_jsx("label", { children: "\u0412\u0456\u0434\u043E\u0431\u0440\u0430\u0436\u0443\u0432\u0430\u043D\u0435 \u0456\u043C'\u044F" }), _jsx("input", { value: editMobileUser.full_name, onChange: (e) => setEditMobileUser({ ...editMobileUser, full_name: e.target.value }) })] }), _jsxs("div", { children: [_jsx("label", { children: "@\u043B\u043E\u0433\u0456\u043D" }), _jsx("input", { value: `@${editMobileUser.username}`, disabled: true })] })] }), _jsxs("div", { className: "row", children: [_jsx("button", { onClick: async () => { if (!token)
                                        return; await api.updateMobileUser(token, editMobileUser.id, { full_name: editMobileUser.full_name }); setToast({ type: "success", message: "Користувача оновлено" }); setEditMobileUser(null); await load(); }, children: "\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438" }), _jsx("button", { className: "button secondary", onClick: () => setEditMobileUser(null), children: "\u0421\u043A\u0430\u0441\u0443\u0432\u0430\u0442\u0438" })] })] }) })) : null, editChallenge ? (_jsx("div", { className: "modalBackdrop", onClick: () => setEditChallenge(null), children: _jsxs("div", { className: "modalCard", onClick: (e) => e.stopPropagation(), children: [_jsx("h3", { children: "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438 \u0447\u0435\u043B\u0435\u043D\u0434\u0436" }), _jsxs("div", { className: "grid2", children: [_jsxs("div", { children: [_jsx("label", { children: "\u041D\u0430\u0437\u0432\u0430" }), _jsx("input", { value: editChallenge.title, onChange: (e) => setEditChallenge({ ...editChallenge, title: e.target.value }) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0421\u043A\u043B\u0430\u0434\u043D\u0456\u0441\u0442\u044C" }), _jsxs("select", { value: editChallenge.difficulty, onChange: (e) => setEditChallenge({ ...editChallenge, difficulty: e.target.value }), children: [_jsx("option", { value: "easy", children: "\u041B\u0435\u0433\u043A\u0430" }), _jsx("option", { value: "normal", children: "\u0421\u0435\u0440\u0435\u0434\u043D\u044F" }), _jsx("option", { value: "hard", children: "\u0421\u043A\u043B\u0430\u0434\u043D\u0430" })] })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0422\u0440\u0438\u0432\u0430\u043B\u0456\u0441\u0442\u044C (\u0434\u043D\u0456\u0432)" }), _jsx("input", { type: "number", value: editChallenge.duration_days, onChange: (e) => setEditChallenge({ ...editChallenge, duration_days: Number(e.target.value) }) })] }), _jsxs("div", { children: [_jsx("label", { children: "XP \u043D\u0430\u0433\u043E\u0440\u043E\u0434\u0430" }), _jsx("input", { type: "number", value: editChallenge.xp_reward, onChange: (e) => setEditChallenge({ ...editChallenge, xp_reward: Number(e.target.value) }) })] })] }), _jsxs("div", { className: "row", children: [_jsx("button", { onClick: async () => { if (!token)
                                        return; await api.updateSponsoredChallenge(token, editChallenge.id, { title: editChallenge.title, difficulty: editChallenge.difficulty, duration_days: editChallenge.duration_days, xp_reward: editChallenge.xp_reward }); setToast({ type: "success", message: "Челендж оновлено" }); setEditChallenge(null); await load(); }, children: "\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438" }), _jsx("button", { className: "button secondary", onClick: () => setEditChallenge(null), children: "\u0421\u043A\u0430\u0441\u0443\u0432\u0430\u0442\u0438" })] })] }) })) : null, editVideo ? (_jsx("div", { className: "modalBackdrop", onClick: () => setEditVideo(null), children: _jsxs("div", { className: "modalCard", onClick: (e) => e.stopPropagation(), children: [_jsx("h3", { children: "\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438 \u0432\u0456\u0434\u0435\u043E" }), _jsxs("div", { className: "grid2", children: [_jsxs("div", { children: [_jsx("label", { children: "\u041E\u043F\u0438\u0441" }), _jsx("textarea", { value: editVideo.description ?? "", onChange: (e) => setEditVideo({ ...editVideo, description: e.target.value }) })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0421\u0442\u0430\u0442\u0443\u0441" }), _jsxs("select", { value: editVideo.status, onChange: (e) => setEditVideo({ ...editVideo, status: e.target.value }), children: [_jsx("option", { value: "PUBLISHED", children: "\u041E\u043F\u0443\u0431\u043B\u0456\u043A\u043E\u0432\u0430\u043D\u043E" }), _jsx("option", { value: "PENDING_MANUAL", children: "\u041D\u0430 \u043C\u043E\u0434\u0435\u0440\u0430\u0446\u0456\u0457" }), _jsx("option", { value: "BLOCKED", children: "\u0417\u0430\u0431\u043B\u043E\u043A\u043E\u0432\u0430\u043D\u043E" })] })] }), _jsxs("div", { children: [_jsx("label", { children: "\u0422\u0438\u043F" }), _jsxs("select", { value: editVideo.is_ad ? "AD" : "NON_AD", onChange: (e) => setEditVideo({ ...editVideo, is_ad: e.target.value === "AD" }), children: [_jsx("option", { value: "NON_AD", children: "\u0417\u0432\u0438\u0447\u0430\u0439\u043D\u0435" }), _jsx("option", { value: "AD", children: "\u0420\u0435\u043A\u043B\u0430\u043C\u043D\u0435" })] })] })] }), _jsxs("div", { className: "row", children: [_jsx("button", { onClick: async () => { if (!token)
                                        return; await api.updateVideo(token, editVideo.id, { description: editVideo.description ?? "", status: editVideo.status, is_ad: editVideo.is_ad }); setToast({ type: "success", message: "Відео оновлено" }); setEditVideo(null); await load(); }, children: "\u0417\u0431\u0435\u0440\u0435\u0433\u0442\u0438" }), _jsx("button", { className: "button secondary", onClick: () => setEditVideo(null), children: "\u0421\u043A\u0430\u0441\u0443\u0432\u0430\u0442\u0438" })] })] }) })) : null, confirm ? (_jsx("div", { className: "modalBackdrop", onClick: () => setConfirm(null), children: _jsxs("div", { className: "modalCard", onClick: (e) => e.stopPropagation(), children: [_jsx("h3", { children: confirm.title }), _jsx("p", { children: confirm.message }), _jsxs("div", { className: "row", children: [_jsx("button", { onClick: async () => { await confirm.action(); setConfirm(null); }, children: "\u041F\u0456\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u0438" }), _jsx("button", { className: "button secondary", onClick: () => setConfirm(null), children: "\u0421\u043A\u0430\u0441\u0443\u0432\u0430\u0442\u0438" })] })] }) })) : null, previewUrl ? (_jsx("div", { className: "modalBackdrop", onClick: () => setPreviewUrl(null), children: _jsxs("div", { className: "modalCard videoPreviewModal", onClick: (e) => e.stopPropagation(), children: [_jsxs("div", { className: "modalHeader", children: [_jsxs("div", { children: [_jsx("h3", { children: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434 \u0432\u0456\u0434\u0435\u043E" }), _jsx("p", { className: "muted", children: "\u0412\u0456\u0434\u0435\u043E \u0432\u0456\u0434\u043A\u0440\u0438\u0432\u0430\u0454\u0442\u044C\u0441\u044F \u0443 \u043C\u0435\u0436\u0430\u0445 \u0430\u0434\u043C\u0456\u043D-\u043F\u0430\u043D\u0435\u043B\u0456, \u0431\u0435\u0437 \u043F\u0435\u0440\u0435\u0445\u043E\u0434\u0443 \u043D\u0430 \u043E\u043A\u0440\u0435\u043C\u0443 \u0441\u0442\u043E\u0440\u0456\u043D\u043A\u0443." })] }), _jsx("button", { className: "iconClose", onClick: () => setPreviewUrl(null), "aria-label": "\u0417\u0430\u043A\u0440\u0438\u0442\u0438", children: "\u00D7" })] }), _jsx("div", { className: "videoFrame", children: _jsx("video", { controls: true, src: previewUrl }) }), _jsx("div", { className: "modalActions", children: _jsx("a", { className: "button secondary", href: previewUrl, target: "_blank", rel: "noreferrer", children: "\u0412\u0456\u0434\u043A\u0440\u0438\u0442\u0438 \u043E\u043A\u0440\u0435\u043C\u043E" }) })] }) })) : null] }));
}
