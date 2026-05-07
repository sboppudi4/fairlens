import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  Gauge,
  ShieldCheck,
  Upload,
  XCircle,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";

const SAMPLE_METRICS = [
  { label: "Demographic parity", value: "0.0421", status: "pass" },
  { label: "Disparate impact", value: "0.83", status: "pass" },
  { label: "Equal opportunity", value: "0.1280", status: "fail" },
  { label: "Equalized odds", value: "0.1410", status: "fail" },
  { label: "Predictive parity", value: "0.0612", status: "pass" },
  { label: "Calibration", value: "0.0392", status: "pass" },
];

export default function Landing() {
  const token = useAuthStore((s) => s.token);
  const ctaTarget = token ? "/dashboard" : "/register";

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border bg-surface">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-accent" />
            <span className="font-bold tracking-tight">FairLens</span>
          </Link>
          <nav className="flex items-center gap-3 text-sm">
            <Link to="/login" className="text-muted hover:text-fg">Sign in</Link>
            <Link to="/register" className="btn-primary py-1.5 px-3 text-xs">
              Get started
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="max-w-6xl mx-auto px-6 py-20 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="text-4xl sm:text-5xl font-bold leading-tight tracking-tight"
            >
              Audit your AI for bias.
              <br />
              <span className="text-accent">Ship with confidence.</span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.08 }}
              className="text-muted mt-5 text-lg leading-relaxed max-w-xl"
            >
              FairLens computes seven fairness metrics, maps findings to EU AI Act, NIST AI RMF, and
              ISO 42001 requirements, and generates a compliance-ready audit report — in minutes.
            </motion.p>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.18 }}
              className="mt-8 flex flex-wrap gap-3"
            >
              <Link to={ctaTarget} className="btn-primary text-base">
                Start free audit <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/login" className="btn-ghost text-base">
                Sign in
              </Link>
            </motion.div>
            <p className="text-xs text-muted mt-6">
              Demo account: <span className="font-mono">demo@fairlens.dev / fairlens2026</span>
            </p>
          </div>

          {/* Animated sample metrics card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="card"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-xs text-muted uppercase tracking-wider">Audit summary</div>
                <div className="font-semibold">Hiring model · gender, race</div>
              </div>
              <div className="text-right">
                <div className="font-mono text-3xl font-bold text-warning">68</div>
                <div className="text-xs text-warning">Medium Risk</div>
              </div>
            </div>
            <div className="space-y-2">
              {SAMPLE_METRICS.map((m, i) => (
                <motion.div
                  key={m.label}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.25 + i * 0.05 }}
                  className="flex items-center justify-between text-sm border-b border-border/40 last:border-0 py-1.5"
                >
                  <span className="text-muted">{m.label}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono">{m.value}</span>
                    {m.status === "pass" ? (
                      <CheckCircle2 className="w-4 h-4 text-success" />
                    ) : (
                      <XCircle className="w-4 h-4 text-danger" />
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* Three-step flow */}
        <section className="bg-surface border-y border-border">
          <div className="max-w-6xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Upload,
                title: "1. Upload your CSV",
                copy: "Bring your model's predictions alongside the ground-truth labels and the demographic columns you care about.",
              },
              {
                icon: Gauge,
                title: "2. Run the audit",
                copy: "FairLens computes demographic parity, disparate impact, equalized odds, calibration, predictive parity, and SHAP explainability.",
              },
              {
                icon: FileText,
                title: "3. Download the report",
                copy: "Get a multi-page PDF mapping every metric to EU AI Act, NIST AI RMF, and ISO 42001 clauses — ready for your compliance file.",
              },
            ].map((b, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                viewport={{ once: true }}
                className="card"
              >
                <b.icon className="w-6 h-6 text-accent mb-3" />
                <h3 className="font-semibold">{b.title}</h3>
                <p className="text-muted text-sm mt-2 leading-relaxed">{b.copy}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Metric callout */}
        <section className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <h2 className="text-3xl font-bold tracking-tight">Built for the EU AI Act era</h2>
            <p className="text-muted mt-3">
              Article 9 risk management. Article 10 bias examination. Article 13 transparency.
              Article 15 accuracy and robustness. FairLens speaks the regulator's language.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { n: "7", label: "Fairness metrics" },
              { n: "3", label: "Regulatory frameworks" },
              { n: "<5min", label: "Audit runtime" },
              { n: "100%", label: "Self-serve" },
            ].map((s) => (
              <div key={s.label} className="card text-center">
                <div className="font-mono text-3xl font-bold text-accent">{s.n}</div>
                <div className="text-xs text-muted uppercase tracking-wider mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-border bg-surface py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-accent" />
            <span>FairLens — AI Fairness Audit Platform</span>
          </div>
          <div>© {new Date().getFullYear()} FairLens. MIT licensed.</div>
        </div>
      </footer>
    </div>
  );
}
