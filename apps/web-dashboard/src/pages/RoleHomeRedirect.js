import { jsx as _jsx } from "react/jsx-runtime";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
export function RoleHomeRedirect() {
    const { user } = useAuth();
    if (!user)
        return _jsx(Navigate, { to: "/login", replace: true });
    if (user.role === "ADMIN")
        return _jsx(Navigate, { to: "/app", replace: true });
    if (user.role === "MODERATOR")
        return _jsx(Navigate, { to: "/app/moderation", replace: true });
    return _jsx(Navigate, { to: "/app/business", replace: true });
}
