import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { login } from "@/api/auth";
import { extractErrorMessage } from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import PrismBackdrop from "@/components/landing/PrismBackdrop";

export default function Login() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("demo@fairlens.dev");
  const [password, setPassword] = useState("fairlens2026");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const resp = await login(email, password);
      setAuth(resp.access_token, resp.user, resp.refresh_token ?? null);
      navigate("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err, "Login failed"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden px-4">
      <PrismBackdrop className="prism-auth" />
      <div className="relative z-10 w-full max-w-md">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <ShieldCheck className="w-8 h-8 text-accent" />
          <h1 className="text-2xl font-bold">FairLens</h1>
        </div>
        <form
          onSubmit={onSubmit}
          className="relative space-y-4 rounded-2xl border border-white/[0.1] bg-white/[0.04] p-6 backdrop-blur-2xl"
        >
          <h2 className="text-xl font-semibold">Sign in</h2>
          <div>
            <label className="block text-sm text-muted mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              required
              autoComplete="email"
            />
          </div>
          <div>
            <label className="block text-sm text-muted mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              required
              autoComplete="current-password"
            />
          </div>
          {error && <p className="text-sm text-danger" role="alert">{error}</p>}
          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? "Signing in…" : "Sign in"}
          </button>
          <p className="text-sm text-muted text-center">
            No account?{" "}
            <Link to="/register" className="text-accent hover:underline">
              Create one
            </Link>
          </p>
          <p className="text-xs text-muted text-center pt-2 border-t border-border">
            Demo: demo@fairlens.dev / fairlens2026
          </p>
        </form>
      </div>
    </div>
  );
}
