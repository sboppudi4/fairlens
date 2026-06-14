import { Component, lazy, Suspense, type ReactNode } from "react";

// three.js is heavy, so the canvas is split into its own chunk and only fetched
// when the landing page mounts — it never enters the initial bundle.
const PrismCanvas = lazy(() => import("./PrismCanvas"));

/** CSS ring motif shown while the canvas loads, or if WebGL is unavailable. */
function PrismFallback() {
  return (
    <div className="prism-fallback" aria-hidden>
      <div className="lens-ring absolute inset-0 rounded-full border border-white/[0.06]" />
      <div
        className="lens-ring absolute inset-[14%] rounded-full border border-white/[0.04]"
        style={{ animationDirection: "reverse", animationDuration: "110s" }}
      />
      <div className="absolute inset-[28%] rounded-full border border-white/[0.03]" />
      <div className="absolute left-1/2 top-1/2 h-[40%] w-[40%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#0a84ff]/[0.06] blur-[80px]" />
    </div>
  );
}

/** Renders the CSS fallback instead of crashing if the WebGL context fails to create. */
class WebGLBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? <PrismFallback /> : this.props.children;
  }
}

/** Floating dark-glass prism for the hero. Decorative — hidden from assistive tech. */
export default function PrismMount() {
  return (
    <div className="prism-float" aria-hidden>
      <WebGLBoundary>
        <Suspense fallback={<PrismFallback />}>
          <PrismCanvas />
        </Suspense>
      </WebGLBoundary>
    </div>
  );
}
