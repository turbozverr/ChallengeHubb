import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
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
export function BusinessPage() {
    const { token } = useAuth();
    const [dashboard, setDashboard] = useState(null);
    const [promos, setPromos] = useState([]);
    const [error, setError] = useState(null);
    useEffect(() => {
        const load = async () => {
            if (!token)
                return;
            try {
                const [d, p] = await Promise.all([api.businessDashboardAnalytics(token), api.unsentPromoCodes(token)]);
                setDashboard(d);
                setPromos(p);
            }
            catch (e) {
                setError(e instanceof Error ? e.message : "Помилка завантаження");
            }
        };
        void load();
    }, [token]);
    const totals = useMemo(() => {
        const views = (dashboard?.views_by_day ?? []).reduce((a, x) => a + x.value, 0);
        const submissions = (dashboard?.submissions_by_day ?? []).reduce((a, x) => a + x.value, 0);
        const completed = (dashboard?.completed_by_day ?? []).reduce((a, x) => a + x.value, 0);
        const conversion = views > 0 ? Number(((completed / views) * 100).toFixed(2)) : 0;
        return { views, submissions, completed, conversion };
    }, [dashboard]);
    return (_jsxs("div", { className: "card", children: [_jsx("h1", { children: "\u0410\u043D\u0430\u043B\u0456\u0442\u0438\u043A\u0430 \u0431\u0456\u0437\u043D\u0435\u0441-\u043A\u0430\u0431\u0456\u043D\u0435\u0442\u0443" }), error ? _jsx("p", { className: "error", children: error }) : null, _jsxs("div", { className: "grid3", children: [_jsxs("div", { className: "stat", children: [_jsx("strong", { children: totals.views }), _jsx("span", { children: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434\u0438" })] }), _jsxs("div", { className: "stat", children: [_jsx("strong", { children: totals.submissions }), _jsx("span", { children: "\u0412\u0456\u0434\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u0456 \u0432\u0456\u0434\u0435\u043E" })] }), _jsxs("div", { className: "stat", children: [_jsxs("strong", { children: [totals.conversion, "%"] }), _jsx("span", { children: "\u041A\u043E\u043D\u0432\u0435\u0440\u0441\u0456\u044F" })] })] }), _jsxs("div", { className: "chartGrid", children: [_jsxs("section", { children: [_jsx("h2", { children: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434\u0438 \u043A\u0430\u043C\u043F\u0430\u043D\u0456\u0439 \u0437\u0430 \u0434\u043D\u044F\u043C\u0438" }), _jsx(LineChart, { labels: dashboard?.views_by_day.map((x) => x.date) ?? [], yLabel: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434\u0438", series: [{ name: "Перегляди", color: "#AD46FF", values: dashboard?.views_by_day.map((x) => x.value) ?? [] }] })] }), _jsxs("section", { children: [_jsx("h2", { children: "\u0423\u0447\u0430\u0441\u0442\u044C \u0443 \u0447\u0435\u043B\u0435\u043D\u0434\u0436\u0430\u0445 \u0437\u0430 \u0434\u043D\u044F\u043C\u0438" }), _jsx(LineChart, { labels: dashboard?.submissions_by_day.map((x) => x.date) ?? [], yLabel: "\u0412\u0456\u0434\u043F\u0440\u0430\u0432\u043A\u0438", series: [{ name: "Відправлені відео", color: "#F6339A", values: dashboard?.submissions_by_day.map((x) => x.value) ?? [] }] })] })] }), _jsxs("div", { className: "chartGrid", children: [_jsxs("section", { children: [_jsx("h2", { children: "\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043D\u043D\u044F \u0447\u0435\u043B\u0435\u043D\u0434\u0436\u0456\u0432 \u0437\u0430 \u0434\u043D\u044F\u043C\u0438" }), _jsx(LineChart, { labels: dashboard?.completed_by_day.map((x) => x.date) ?? [], yLabel: "\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043D\u043D\u044F", series: [{ name: "Завершені", color: "#36CFC9", values: dashboard?.completed_by_day.map((x) => x.value) ?? [] }] })] }), _jsxs("section", { children: [_jsx("h2", { children: "\u041A\u043E\u043D\u0432\u0435\u0440\u0441\u0456\u044F \u043A\u0430\u043C\u043F\u0430\u043D\u0456\u0439 \u0437\u0430 \u0434\u043D\u044F\u043C\u0438" }), _jsx(LineChart, { labels: dashboard?.conversion_by_day.map((x) => x.date) ?? [], yLabel: "%", series: [{ name: "Конверсія, %", color: "#AD46FF", values: dashboard?.conversion_by_day.map((x) => x.value) ?? [] }] })] })] }), _jsxs("section", { children: [_jsx("h2", { children: "\u0412\u0437\u0430\u0454\u043C\u043E\u0434\u0456\u044F \u0437 \u043A\u043E\u043D\u0442\u0435\u043D\u0442\u043E\u043C" }), _jsx(LineChart, { labels: dashboard?.interactions_by_day.map((x) => x.date) ?? [], yLabel: "\u041A\u0456\u043B\u044C\u043A\u0456\u0441\u0442\u044C", series: [
                            { name: "Лайки", color: "#F6339A", values: dashboard?.interactions_by_day.map((x) => x.likes) ?? [] },
                            { name: "Репости", color: "#36CFC9", values: dashboard?.interactions_by_day.map((x) => x.shares) ?? [] },
                            { name: "Коментарі", color: "#9FA6B2", values: dashboard?.interactions_by_day.map((x) => x.comments) ?? [] }
                        ] })] }), _jsx("h2", { children: "\u041D\u0435\u0432\u0456\u0434\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u0456 \u043F\u0440\u043E\u043C\u043E\u043A\u043E\u0434\u0438" }), _jsx("div", { className: "tableWrap", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "ID" }), _jsx("th", { children: "\u0427\u0435\u043B\u0435\u043D\u0434\u0436" }), _jsx("th", { children: "\u041A\u043E\u0434" })] }) }), _jsx("tbody", { children: promos.map((p) => _jsxs("tr", { children: [_jsx("td", { children: p.id }), _jsx("td", { children: p.challenge_id }), _jsx("td", { children: p.code })] }, p.id)) })] }) })] }));
}
