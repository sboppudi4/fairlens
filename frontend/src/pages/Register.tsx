import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { register } from "@/api/auth";
import { extractErrorMessage } from "@/api/client";
import { useAuthStore } from "@/store/authStore";

export default function Register() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const resp = await register(email, password, fullName);
      setAuth(resp.access_token, resp.user);
      navigate("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err, "Registration failed"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <ShieldCheck className="w-8 h-8 text-accent" />
          <h1 className="text-2xl font-bold">FairLens</h1>
        </div>
        <form onSubmit={onSubmit} className="card space-y-4">
          <h2 className="text-xl font-semibold">Create account</h2>
          <div>
            <label className="block text-sm text-muted mb-1">Full name</label>
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="input" required minLength={1} />
          </div>
          <div>
            <label className="block text-sm text-muted mb-1">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input" required />
          </div>
          <div>
            <label className="block text-sm text-muted mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              required
              minLength={8}
            />
            <p className="text-xs text-muted mt-1">At least 8 characters.</p>
          </div>
          {error && <p className="text-sm text-danger">{error}</p>}
          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? "Creating…" : "Create account"}
          </button>
          <p className="text-sm text-muted text-center">
            Already have an account?{" "}
            <Link to="/login" className="text-accent hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
