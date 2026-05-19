import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "@/lib/auth";
import { I18nProvider } from "@/lib/i18n";
import { Toaster } from "@/components/ui/sonner";

import Landing from "@/pages/Landing";
import AuthCallback from "@/pages/AuthCallback";
import Onboarding from "@/pages/Onboarding";
import EmployeeDashboard from "@/pages/EmployeeDashboard";
import EmployerDashboard from "@/pages/EmployerDashboard";
import AdminDashboard from "@/pages/AdminDashboard";
import TwoFactorChallenge from "@/components/TwoFactorChallenge";

function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth();
  if (loading || user === null) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-500" data-testid="loading-state">
        Lädt…
      </div>
    );
  }
  if (!user) return <Navigate to="/" replace />;
  if (!user.role) return <Navigate to="/onboarding" replace />;
  if (role && user.role !== role) return <Navigate to={`/${user.role}`} replace />;
  return children;
}

function RoleRouter() {
  const { user, loading } = useAuth();
  if (loading || user === null) return null;
  if (!user) return <Landing />;
  if (!user.role) return <Navigate to="/onboarding" replace />;
  return <Navigate to={`/${user.role}`} replace />;
}

function GlobalTwoFactor() {
  const { twoFactorChallenge, setTwoFactor } = useAuth();
  if (!twoFactorChallenge) return null;
  return (
    <TwoFactorChallenge
      challenge_token={twoFactorChallenge}
      onClose={() => setTwoFactor(null)}
      onSuccess={() => setTwoFactor(null)}
    />
  );
}

function AppRouter() {
  const location = useLocation();
  // Detect OAuth callback synchronously during render to avoid race conditions
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/" element={<RoleRouter />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/onboarding" element={
        <ProtectedRouteNoRole>
          <Onboarding />
        </ProtectedRouteNoRole>
      } />
      <Route path="/employee" element={<ProtectedRoute role="employee"><EmployeeDashboard /></ProtectedRoute>} />
      <Route path="/employer" element={<ProtectedRoute role="employer"><EmployerDashboard /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
    </Routes>
  );
}

function ProtectedRouteNoRole({ children }) {
  const { user, loading } = useAuth();
  if (loading || user === null) return null;
  if (!user) return <Navigate to="/" replace />;
  if (user.role) return <Navigate to={`/${user.role}`} replace />;
  return children;
}

export default function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRouter />
          <GlobalTwoFactor />
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </I18nProvider>
  );
}
