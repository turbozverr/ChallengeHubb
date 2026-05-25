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
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/home" element={<RoleHomeRedirect />} />
        <Route path="/403" element={<ForbiddenPage />} />

        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route
            index
            element={<Navigate to="/app/admin" replace />}
          />
          <Route
            path="admin"
            element={
              <RoleGuard allow={["ADMIN"]}>
                <AdminPage />
              </RoleGuard>
            }
          />
          <Route
            path="moderation"
            element={
              <RoleGuard allow={["ADMIN", "MODERATOR"]}>
                <ModerationPage />
              </RoleGuard>
            }
          />
          <Route
            path="business"
            element={
              <RoleGuard allow={["ADMIN", "BUSINESS_CLIENT"]}>
                <BusinessPage />
              </RoleGuard>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
