import { Link, NavLink, useNavigate } from "react-router-dom";
import { LogOut, ShieldCheck } from "lucide-react";
import { useAuthStore } from "@/store/authStore";

export default function Navbar() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);

  function logout() {
    clear();
    navigate("/login");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-black/50 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-accent" />
          <span className="font-semibold tracking-tight">FairLens</span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <NavLink to="/dashboard" className={navClass}>
            Dashboard
          </NavLink>
          <NavLink to="/audits/new" className={navClass}>
            New audit
          </NavLink>
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
  );
}

function navClass({ isActive }: { isActive: boolean }) {
  return (
    "px-3 py-1.5 rounded-lg transition-colors " +
    (isActive ? "bg-accent/10 text-accent" : "text-muted hover:text-fg hover:bg-white/5")
  );
}
