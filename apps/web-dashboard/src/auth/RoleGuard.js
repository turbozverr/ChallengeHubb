import { jsx as _jsx, Fragment as _Fragment } from "react/jsx-runtime";
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
export function RoleGuard({ allow, children }) {
    const { user } = useAuth();
    if (!user) {
        return _jsx(Navigate, { to: "/login", replace: true });
    }
    if (!allow.includes(user.role)) {
        return _jsx(Navigate, { to: "/403", replace: true });
    }
    return _jsx(_Fragment, { children: children });
}
