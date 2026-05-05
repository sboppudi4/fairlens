import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { ShieldCheck, LogOut } from "lucide-react";
import { useAuthStore } from "@/store/authStore";

export default function Layout() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);

  function logout() {
    clear();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border bg-surface">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-accent" />
            <span className="font-bold tracking-tight">FairLens</span>
          </Link>
          <nav className="flex items-center gap-1 text-sm">
            <NavLink to="/dashboard" className={navClass}>Dashboard</NavLink>
            <NavLink to="/audits/new" className={navClass}>New audit</NavLink>
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-muted hidden sm:inline">{user?.email}</span>
            <button onClick={logout} className="btn-ghost py-1.5 px-3 text-xs" title="Log out">
              <LogOut className="w-3.5 h-3.5" />
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

function navClass({ isActive }: { isActive: boolean }) {
  return (
    "px-3 py-1.5 rounded-md transition-colors " +
    (isActive ? "bg-accent/10 text-accent" : "text-muted hover:text-fg hover:bg-surface")
  );
}
