import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { resolveMediaUrl } from "../api/media";
import { useAuth } from "../auth/AuthContext";
const aiLabels = {
    REJECTED: "Відхилено AI",
    APPROVED: "Схвалено AI",
    PENDING: "Очікує AI"
};
export function ModerationPage() {
    const { token } = useAuth();
    const [videos, setVideos] = useState([]);
    const [reports, setReports] = useState([]);
    const [error, setError] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const load = async () => {
        if (!token)
            return;
        try {
            const [v, r] = await Promise.all([api.moderationVideoQueue(token), api.moderationReportsQueue(token)]);
            setVideos(v);
            setReports(r);
            setError(null);
        }
        catch (e) {
            setError(e instanceof Error ? e.message : "Помилка завантаження модерації");
        }
    };
    useEffect(() => {
        void load();
    }, [token]);
    return (_jsxs(_Fragment, { children: [_jsxs("div", { className: "card", children: [_jsx("h1", { children: "\u0426\u0435\u043D\u0442\u0440 \u043C\u043E\u0434\u0435\u0440\u0430\u0446\u0456\u0457" }), error ? _jsx("p", { className: "error", children: error }) : null, _jsx("h2", { children: "\u0427\u0435\u0440\u0433\u0430 \u0432\u0456\u0434\u0435\u043E, \u0432\u0456\u0434\u0445\u0438\u043B\u0435\u043D\u0438\u0445 AI" }), _jsx("div", { className: "tableWrap", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "ID" }), _jsx("th", { children: "\u041A\u043E\u043D\u0442\u0435\u043D\u0442" }), _jsx("th", { children: "\u0420\u0456\u0448\u0435\u043D\u043D\u044F AI" }), _jsx("th", { children: "\u0421\u043A\u0430\u0440\u0433\u0438" }), _jsx("th", { children: "\u0420\u0456\u0448\u0435\u043D\u043D\u044F" })] }) }), _jsx("tbody", { children: videos.map((video) => (_jsxs("tr", { children: [_jsx("td", { children: video.id }), _jsx("td", { children: _jsx("button", { className: "actionBtn iconOnly view", title: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434", "aria-label": "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434", onClick: () => setPreviewUrl(resolveMediaUrl(video.url)), children: "\u25B6" }) }), _jsx("td", { children: aiLabels[video.ai_status] ?? video.ai_status }), _jsx("td", { children: video.reports_count }), _jsx("td", { children: _jsxs("div", { className: "actionBar", children: [_jsx("button", { className: "actionBtn iconOnly publish", title: "\u0421\u0445\u0432\u0430\u043B\u0438\u0442\u0438", "aria-label": "\u0421\u0445\u0432\u0430\u043B\u0438\u0442\u0438", onClick: async () => { if (!token)
                                                                return; await api.decideVideo(token, video.id, "APPROVE"); await load(); }, children: "\u2713" }), _jsx("button", { className: "actionBtn iconOnly danger", title: "\u0417\u0430\u0431\u043B\u043E\u043A\u0443\u0432\u0430\u0442\u0438", "aria-label": "\u0417\u0430\u0431\u043B\u043E\u043A\u0443\u0432\u0430\u0442\u0438", onClick: async () => { if (!token)
                                                                return; await api.decideVideo(token, video.id, "BLOCK"); await load(); }, children: "\u00D7" })] }) })] }, video.id))) })] }) }), _jsx("h2", { children: "\u0427\u0435\u0440\u0433\u0430 \u0441\u043A\u0430\u0440\u0433" }), _jsx("div", { className: "tableWrap", children: _jsxs("table", { children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "ID" }), _jsx("th", { children: "\u0412\u0456\u0434\u0435\u043E" }), _jsx("th", { children: "\u041F\u0440\u0438\u0447\u0438\u043D\u0430" }), _jsx("th", { children: "\u0420\u0456\u0448\u0435\u043D\u043D\u044F" })] }) }), _jsx("tbody", { children: reports.map((report) => (_jsxs("tr", { children: [_jsx("td", { children: report.id }), _jsx("td", { children: _jsx("button", { className: "actionBtn iconOnly view", title: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434", "aria-label": "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434", disabled: !report.video_url, onClick: () => report.video_url && setPreviewUrl(resolveMediaUrl(report.video_url)), children: "\u25B6" }) }), _jsx("td", { children: report.reason }), _jsx("td", { children: _jsxs("div", { className: "actionBar", children: [_jsx("button", { className: "actionBtn iconOnly publish", title: "\u0421\u0445\u0432\u0430\u043B\u0438\u0442\u0438", "aria-label": "\u0421\u0445\u0432\u0430\u043B\u0438\u0442\u0438", onClick: async () => { if (!token)
                                                                return; await api.decideReport(token, report.id, "REJECT"); await load(); }, children: "\u2713" }), _jsx("button", { className: "actionBtn iconOnly danger", title: "\u0417\u0430\u0431\u043B\u043E\u043A\u0443\u0432\u0430\u0442\u0438", "aria-label": "\u0417\u0430\u0431\u043B\u043E\u043A\u0443\u0432\u0430\u0442\u0438", onClick: async () => { if (!token)
                                                                return; await api.decideReport(token, report.id, "CONFIRM"); await load(); }, children: "\u00D7" })] }) })] }, report.id))) })] }) })] }), previewUrl ? (_jsx("div", { className: "modalBackdrop", onClick: () => setPreviewUrl(null), children: _jsxs("div", { className: "modalCard videoPreviewModal", onClick: (e) => e.stopPropagation(), children: [_jsxs("div", { className: "modalHeader", children: [_jsxs("div", { children: [_jsx("h3", { children: "\u041F\u0435\u0440\u0435\u0433\u043B\u044F\u0434 \u0432\u0456\u0434\u0435\u043E" }), _jsx("p", { className: "muted", children: "\u041F\u0435\u0440\u0435\u0432\u0456\u0440\u0442\u0435 \u043A\u043E\u043D\u0442\u0435\u043D\u0442 \u043F\u0435\u0440\u0435\u0434 \u0440\u0456\u0448\u0435\u043D\u043D\u044F\u043C \u043C\u043E\u0434\u0435\u0440\u0430\u0446\u0456\u0457." })] }), _jsx("button", { className: "iconClose", onClick: () => setPreviewUrl(null), "aria-label": "\u0417\u0430\u043A\u0440\u0438\u0442\u0438", children: "\u00D7" })] }), _jsx("div", { className: "videoFrame", children: _jsx("video", { controls: true, src: previewUrl }) }), _jsx("div", { className: "modalActions", children: _jsx("a", { className: "button secondary", href: previewUrl, target: "_blank", rel: "noreferrer", children: "\u0412\u0456\u0434\u043A\u0440\u0438\u0442\u0438 \u043E\u043A\u0440\u0435\u043C\u043E" }) })] }) })) : null] }));
}
