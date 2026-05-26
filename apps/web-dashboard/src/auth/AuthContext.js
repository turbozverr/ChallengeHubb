import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    useEffect(() => {
        const rawUser = localStorage.getItem("ch_user");
        const rawToken = localStorage.getItem("ch_token");
        if (rawUser && rawToken) {
            setUser(JSON.parse(rawUser));
            setToken(rawToken);
        }
    }, []);
    const value = useMemo(() => ({
        user,
        token,
        login: async (email, password) => {
            const response = await api.login(email, password);
            const mappedUser = {
                id: response.user.id,
                fullName: response.user.full_name,
                email: response.user.email,
                role: response.user.role
            };
            setUser(mappedUser);
            setToken(response.access_token);
            localStorage.setItem("ch_user", JSON.stringify(mappedUser));
            localStorage.setItem("ch_token", response.access_token);
            return mappedUser;
        },
        logout: () => {
            setUser(null);
            setToken(null);
            localStorage.removeItem("ch_user");
            localStorage.removeItem("ch_token");
        }
    }), [user, token]);
    return _jsx(AuthContext.Provider, { value: value, children: children });
}
export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) {
        throw new Error("useAuth must be used inside AuthProvider");
    }
    return ctx;
}
