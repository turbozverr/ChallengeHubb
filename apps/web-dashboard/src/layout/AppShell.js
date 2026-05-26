import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
const roleLabels = {
    ADMIN: "Адміністратор",
    MODERATOR: "Модератор",
    BUSINESS_CLIENT: "Бізнес-клієнт"
};
export function AppShell() {
    const { user, logout } = useAuth();
    const links = user?.role === "ADMIN"
        ? [
            { to: "/app/admin", label: "Панель адміністратора" },
            { to: "/app/moderation", label: "Модерація" },
            { to: "/app/business", label: "Бізнес-аналітика" }
        ]
        : user?.role === "MODERATOR"
            ? [{ to: "/app/moderation", label: "Модерація" }]
            : [{ to: "/app/business", label: "Мої кампанії" }];
    return (_jsxs("div", { className: "shell", children: [_jsxs("aside", { className: "sidebar", children: [_jsxs("div", { className: "sidebarTop", children: [_jsxs("div", { className: "brand", children: [_jsx("img", { src: "/logo-placeholder.svg", alt: "ChallengeHub logo", className: "logo" }), _jsx("h2", { children: "ChallengeHub" })] }), _jsx("nav", { children: links.map((item) => (_jsx(Link, { to: item.to, children: item.label }, item.to))) })] }), _jsx("div", { className: "sidebarBottom", children: _jsx("button", { onClick: logout, children: "\u0412\u0438\u0439\u0442\u0438" }) })] }), _jsxs("section", { className: "content", children: [_jsx("header", { className: "topbar", children: _jsxs("div", { children: [_jsx("strong", { children: user?.fullName }), _jsxs("span", { className: "muted", children: [" (", user?.role ? roleLabels[user.role] ?? user.role : "", ")"] })] }) }), _jsx("main", { children: _jsx(Outlet, {}) })] })] }));
}
