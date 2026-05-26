import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
export function AppHomePage() {
    const { token } = useAuth();
    const [overview, setOverview] = useState(null);
    const [stats, setStats] = useState([]);
    const [error, setError] = useState(null);
    useEffect(() => {
        const run = async () => {
            if (!token)
                return;
            try {
                const [ov, st] = await Promise.all([api.adminOverview(token), api.campaignStats(token)]);
                setOverview(ov);
                setStats(st);
            }
            catch (e) {
                setError(e instanceof Error ? e.message : "Помилка завантаження");
            }
        };
        void run();
    }, [token]);
    return (_jsxs("div", { className: "card", children: [_jsx("h1", { children: "\u0413\u043B\u043E\u0431\u0430\u043B\u044C\u043D\u0438\u0439 \u0434\u0430\u0448\u0431\u043E\u0440\u0434 \u0430\u0434\u043C\u0456\u043D\u0456\u0441\u0442\u0440\u0430\u0442\u043E\u0440\u0430" }), error ? _jsx("p", { className: "error", children: error }) : null, overview ? (_jsx("div", { className: "grid3", children: Object.entries(overview).map(([k, v]) => (_jsxs("div", { className: "stat", children: [_jsx("strong", { children: v }), _jsx("span", { children: k })] }, k))) })) : null, _jsx("h2", { children: "\u0422\u043E\u043F \u043A\u0430\u043C\u043F\u0430\u043D\u0456\u0439 \u0437\u0430 \u043A\u043E\u043D\u0432\u0435\u0440\u0441\u0456\u0454\u044E" }), _jsx("div", { className: "bars", children: stats.map((s) => (_jsxs("div", { className: "barRow", children: [_jsx("span", { children: s.title }), _jsx("div", { className: "barTrack", children: _jsx("div", { className: "barFill", style: { width: `${Math.min(s.conversion_rate * 4, 100)}%` } }) }), _jsxs("strong", { children: [s.conversion_rate, "%"] })] }, s.challenge_id))) })] }));
}
