import type { ReactElement } from "react";
import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuthStore } from "@/store/authStore";

// Route-level code splitting: each page (and its heavy transitive deps such as
// recharts and framer-motion) is fetched only when its route is visited, instead
// of being bundled into the initial download served on `/`.
const Layout = lazy(() => import("@/components/layout/Layout"));
const Login = lazy(() => import("@/pages/Login"));
const Register = lazy(() => import("@/pages/Register"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const NewAudit = lazy(() => import("@/pages/NewAudit"));
const AuditResults = lazy(() => import("@/pages/AuditResults"));
const Landing = lazy(() => import("@/pages/Landing"));

function RequireAuth({ children }: { children: ReactElement }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function RouteFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center text-muted">
      <Loader2 className="w-6 h-6 animate-spin text-accent" />
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/audits/new" element={<NewAudit />} />
          <Route path="/audits/:id" element={<AuditResults />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
