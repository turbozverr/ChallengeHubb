import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RoleGuard } from "./auth/RoleGuard";
import { AppShell } from "./layout/AppShell";
import { AdminPage } from "./pages/AdminPage";
import { BusinessPage } from "./pages/BusinessPage";
import { ForbiddenPage } from "./pages/ForbiddenPage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { ModerationPage } from "./pages/ModerationPage";
import { RoleHomeRedirect } from "./pages/RoleHomeRedirect";
export function App() {
    return (_jsx(AuthProvider, { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(LandingPage, {}) }), _jsx(Route, { path: "/login", element: _jsx(LoginPage, {}) }), _jsx(Route, { path: "/home", element: _jsx(RoleHomeRedirect, {}) }), _jsx(Route, { path: "/403", element: _jsx(ForbiddenPage, {}) }), _jsxs(Route, { path: "/app", element: _jsx(ProtectedRoute, { children: _jsx(AppShell, {}) }), children: [_jsx(Route, { index: true, element: _jsx(Navigate, { to: "/app/admin", replace: true }) }), _jsx(Route, { path: "admin", element: _jsx(RoleGuard, { allow: ["ADMIN"], children: _jsx(AdminPage, {}) }) }), _jsx(Route, { path: "moderation", element: _jsx(RoleGuard, { allow: ["ADMIN", "MODERATOR"], children: _jsx(ModerationPage, {}) }) }), _jsx(Route, { path: "business", element: _jsx(RoleGuard, { allow: ["ADMIN", "BUSINESS_CLIENT"], children: _jsx(BusinessPage, {}) }) })] }), _jsx(Route, { path: "*", element: _jsx(Navigate, { to: "/", replace: true }) })] }) }));
}
