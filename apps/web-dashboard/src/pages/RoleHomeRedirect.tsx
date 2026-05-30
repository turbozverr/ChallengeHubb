import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function RoleHomeRedirect() {
  const { user, initialized } = useAuth();
  if (!initialized) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "ADMIN") return <Navigate to="/app" replace />;
  if (user.role === "MODERATOR") return <Navigate to="/app/moderation" replace />;
  return <Navigate to="/app/business" replace />;
}
