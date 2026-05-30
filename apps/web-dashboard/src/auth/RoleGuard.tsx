import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { WebRole } from "./types";

interface RoleGuardProps {
  allow: WebRole[];
  children: React.ReactNode;
}

export function RoleGuard({ allow, children }: RoleGuardProps) {
  const { user, initialized } = useAuth();
  if (!initialized) {
    return null;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allow.includes(user.role)) {
    return <Navigate to="/403" replace />;
  }

  return <>{children}</>;
}
