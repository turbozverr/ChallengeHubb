import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
export function LoginPage() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState("admin@challengehub.local");
    const [password, setPassword] = useState("admin123");
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const handleSubmit = async (event) => {
        event.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const user = await login(email, password);
            if (user.role === "ADMIN")
                navigate("/app");
            else if (user.role === "MODERATOR")
                navigate("/app/moderation");
            else
                navigate("/app/business");
        }
        catch (e) {
            setError(e instanceof Error ? e.message : "Помилка авторизації");
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsxs("div", { className: "card", children: [_jsx("h1", { children: "\u0412\u0445\u0456\u0434 \u0443 ChallengeHub WebSystem" }), _jsx("p", { className: "muted", children: "\u0414\u0435\u043C\u043E: admin/moderator/business + \u043F\u0430\u0440\u043E\u043B\u044C *123" }), _jsxs("form", { className: "column", onSubmit: handleSubmit, children: [_jsx("input", { value: email, onChange: (e) => setEmail(e.target.value), placeholder: "Email" }), _jsx("input", { value: password, onChange: (e) => setPassword(e.target.value), placeholder: "\u041F\u0430\u0440\u043E\u043B\u044C", type: "password" }), error ? _jsx("p", { className: "error", children: error }) : null, _jsx("button", { type: "submit", disabled: loading, children: loading ? "Вхід..." : "Увійти" })] })] }));
}
