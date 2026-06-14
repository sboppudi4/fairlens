import { Component, lazy, Suspense, type ReactNode } from "react";

// Same lazy three.js chunk as the hero — loaded once, cached, never in the initial bundle.
const PrismCanvas = lazy(() => import("./PrismCanvas"));

/** Silently drops the backdrop if WebGL can't initialize. */
class WebGLBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

/** Decorative ambient prism for page backgrounds. Position + opacity come from `className`. */
export default function PrismBackdrop({ className }: { className?: string }) {
  return (
    <div className={className} aria-hidden>
      <WebGLBoundary>
        <Suspense fallback={null}>
          <PrismCanvas />
        </Suspense>
      </WebGLBoundary>
    </div>
  );
}
