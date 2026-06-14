import { Link } from "react-router-dom";
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
import PrismMount from "@/components/landing/PrismMount";

const SAMPLE_METRICS = [
  { label: "Demographic parity", value: "0.0421", status: "pass" },
  { label: "Disparate impact", value: "0.83", status: "pass" },
  { label: "Equal opportunity", value: "0.1280", status: "fail" },
  { label: "Equalized odds", value: "0.1410", status: "fail" },
  { label: "Predictive parity", value: "0.0612", status: "pass" },
  { label: "Calibration", value: "0.0392", status: "pass" },
];

const STEPS = [
  {
    icon: Upload,
    n: "01",
    title: "Upload your CSV",
    copy: "Bring your model's predictions alongside the ground-truth labels and the demographic columns you care about.",
  },
  {
    icon: Gauge,
    n: "02",
    title: "Run the audit",
    copy: "FairLens computes demographic parity, disparate impact, equalized odds, calibration, predictive parity, and SHAP explainability.",
  },
  {
    icon: FileText,
    n: "03",
    title: "Prove compliance",
    copy: "Get a multi-page PDF mapping every metric to EU AI Act, NIST AI RMF, and ISO 42001 clauses — ready for your file.",
  },
];

const STATS = [
  { n: "7", label: "Fairness metrics" },
  { n: "3", label: "Regulatory frameworks" },
  { n: "<5min", label: "Audit runtime" },
  { n: "100%", label: "Self-serve" },
];

export default function Landing() {
  const token = useAuthStore((s) => s.token);
  const ctaTarget = token ? "/dashboard" : "/register";

  return (
    <div className="min-h-screen bg-black font-sans text-[#f5f5f7] antialiased">
      {/* Frosted nav */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] bg-black/40 backdrop-blur-xl">
        <nav className="mx-auto flex h-14 max-w-[1100px] items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2 text-sm font-semibold tracking-tight">
            <span className="inline-block h-4 w-4 rounded-full border border-[#8e9196] ring-1 ring-inset ring-white/20" />
            FairLens
          </Link>
          <div className="hidden items-center gap-8 text-[13px] text-[#86868b] md:flex">
            <a className="transition-colors hover:text-[#f5f5f7]" href="#how">How it works</a>
            <a className="transition-colors hover:text-[#f5f5f7]" href="#metrics">Metrics</a>
            <a className="transition-colors hover:text-[#f5f5f7]" href="#frameworks">Frameworks</a>
          </div>
          <Link
            to={ctaTarget}
            className="rounded-full bg-[#0a84ff] px-4 py-1.5 text-[13px] font-medium text-white transition hover:brightness-110"
          >
            Start audit
          </Link>
        </nav>
      </header>

      <main>
        {/* Hero — floating dark-glass prism with the copy wrapping around it */}
        <section className="relative isolate flex min-h-screen items-center overflow-hidden">
          <div className="mx-auto w-full max-w-[1100px] px-6">
            {/* Floated WebGL prism; the copy below wraps around it (see .prism-float). */}
            <PrismMount />

            <p className="lens-focus font-mono text-[13px] uppercase tracking-[0.18em] text-[#86868b]">
              AI fairness, audited
            </p>
            <h1
              className="lens-focus mt-6 text-[clamp(2.75rem,7vw,5.5rem)] font-semibold leading-[1.0] tracking-[-0.03em]"
              style={{ animationDelay: "0.08s" }}
            >
              See the bias before it ships.
            </h1>
            <p
              className="lens-focus mt-7 text-[clamp(1.05rem,2vw,1.3rem)] leading-relaxed text-[#86868b]"
              style={{ animationDelay: "0.16s" }}
            >
              FairLens computes seven fairness metrics, maps every finding to the{" "}
              <span className="text-[#f5f5f7]">EU AI Act, NIST AI RMF, and ISO&nbsp;42001</span>, and
              produces a compliance-ready report — in minutes.
            </p>
            <div
              className="lens-focus mt-10 flex flex-wrap items-center gap-5"
              style={{ animationDelay: "0.24s" }}
            >
              <Link
                to={ctaTarget}
                className="group inline-flex items-center gap-2 rounded-full bg-[#f5f5f7] px-7 py-3 text-[15px] font-medium text-black transition duration-300 hover:scale-[1.02] hover:bg-white"
              >
                Start free audit
                <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
              </Link>
              <a
                href="#how"
                className="inline-flex items-center gap-2 text-[15px] text-[#0a84ff] transition hover:brightness-125"
              >
                See how it works
              </a>
            </div>
            <p
              className="lens-focus mt-16 font-mono text-[12px] tracking-[0.12em] text-[#5e5e63] clear-both"
              style={{ animationDelay: "0.32s" }}
            >
              MAPPED TO · EU AI ACT · NIST AI RMF · ISO 42001
            </p>
          </div>
        </section>

        {/* The readout — seven fairness metrics */}
        <section id="metrics" className="border-t border-white/[0.06] bg-[#0a0a0c] py-24 sm:py-32">
          <div className="mx-auto max-w-[980px] px-6">
            <p className="font-mono text-[13px] uppercase tracking-[0.18em] text-[#86868b]">
              The readout
            </p>
            <h2 className="mt-4 max-w-[18ch] text-[clamp(2rem,4vw,3.25rem)] font-semibold leading-tight tracking-[-0.02em]">
              Seven metrics. One verdict.
            </h2>

            <div className="mt-10 rounded-2xl border border-white/[0.08] bg-black/40 p-6 backdrop-blur animate-scale-in">
              <div className="mb-5 flex items-center justify-between border-b border-white/[0.06] pb-4">
                <div>
                  <div className="font-mono text-[12px] uppercase tracking-[0.14em] text-[#86868b]">
                    Audit summary
                  </div>
                  <div className="mt-1 font-medium">Hiring model · gender, race</div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-4xl font-semibold text-[#e0a106]">68</div>
                  <div className="text-[12px] text-[#e0a106]">Medium risk</div>
                </div>
              </div>
              <div>
                {SAMPLE_METRICS.map((m) => (
                  <div
                    key={m.label}
                    className="flex items-center justify-between border-b border-white/[0.04] py-2.5 text-sm last:border-0"
                  >
                    <span className="text-[#86868b]">{m.label}</span>
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-[#f5f5f7]">{m.value}</span>
                      {m.status === "pass" ? (
                        <CheckCircle2 className="h-4 w-4 text-[#30d158]" />
                      ) : (
                        <XCircle className="h-4 w-4 text-[#ff453a]" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="border-t border-white/[0.06] bg-black py-24 sm:py-32">
          <div className="mx-auto max-w-[980px] px-6">
            <p className="font-mono text-[13px] uppercase tracking-[0.18em] text-[#86868b]">
              How it works
            </p>
            <h2 className="mt-4 max-w-[18ch] text-[clamp(2rem,4vw,3.25rem)] font-semibold leading-tight tracking-[-0.02em]">
              Upload. Audit. Prove.
            </h2>
            <div className="mt-12 grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.06] md:grid-cols-3">
              {STEPS.map((s) => (
                <div key={s.n} className="bg-[#0a0a0c] p-8">
                  <div className="flex items-center justify-between">
                    <s.icon className="h-6 w-6 text-[#0a84ff]" />
                    <span className="font-mono text-[13px] text-[#5e5e63]">{s.n}</span>
                  </div>
                  <h3 className="mt-6 text-lg font-medium">{s.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#86868b]">{s.copy}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Frameworks / authority */}
        <section
          id="frameworks"
          className="border-t border-white/[0.06] bg-[#0a0a0c] py-24 sm:py-32"
        >
          <div className="mx-auto max-w-[980px] px-6">
            <div className="max-w-[40ch]">
              <p className="font-mono text-[13px] uppercase tracking-[0.18em] text-[#86868b]">
                Built for the EU AI Act era
              </p>
              <h2 className="mt-4 text-[clamp(2rem,4vw,3.25rem)] font-semibold leading-tight tracking-[-0.02em]">
                We speak the regulator's language.
              </h2>
              <p className="mt-5 leading-relaxed text-[#86868b]">
                Article 9 risk management. Article 10 bias examination. Article 13 transparency.
                Article 15 accuracy and robustness — each finding mapped to the clause it answers.
              </p>
            </div>
            <div className="mt-14 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.06] md:grid-cols-4">
              {STATS.map((s) => (
                <div key={s.label} className="bg-[#0a0a0c] p-8 text-center">
                  <div className="font-mono text-4xl font-semibold tracking-tight text-[#f5f5f7]">
                    {s.n}
                  </div>
                  <div className="mt-2 text-[12px] uppercase tracking-[0.12em] text-[#86868b]">
                    {s.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="border-t border-white/[0.06] bg-black py-28 text-center sm:py-36">
          <div className="mx-auto max-w-[980px] px-6">
            <h2 className="mx-auto max-w-[16ch] text-[clamp(2.25rem,5vw,4rem)] font-semibold leading-[1.02] tracking-[-0.03em]">
              Audit your model today.
            </h2>
            <div className="mt-10 flex items-center justify-center">
              <Link
                to={ctaTarget}
                className="group inline-flex items-center gap-2 rounded-full bg-[#f5f5f7] px-8 py-3.5 text-[15px] font-medium text-black transition duration-300 hover:scale-[1.02] hover:bg-white"
              >
                Start free audit
                <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
              </Link>
            </div>
            <p className="mt-8 font-mono text-[12px] tracking-[0.08em] text-[#5e5e63]">
              Demo account · demo@fairlens.dev / fairlens2026
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/[0.06] bg-black py-10">
        <div className="mx-auto flex max-w-[1100px] flex-col items-center justify-between gap-3 px-6 text-[12px] text-[#5e5e63] sm:flex-row">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-[#86868b]" />
            <span>FairLens — AI Fairness Audit Platform</span>
          </div>
          <div>© {new Date().getFullYear()} FairLens. MIT licensed.</div>
        </div>
      </footer>
    </div>
  );
}
