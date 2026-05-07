import { useEffect, useRef, useState } from "react";

/** Poll an async function on an interval until `shouldContinue` returns false. */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  shouldContinue: (data: T | null) => boolean,
  intervalMs = 2000,
  enabled = true,
): { data: T | null; error: unknown; isPolling: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [isPolling, setIsPolling] = useState(false);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    if (!enabled) return;
    let timer: ReturnType<typeof setTimeout> | null = null;

    async function tick() {
      if (cancelled.current) return;
      try {
        setIsPolling(true);
        const next = await fetcher();
        if (cancelled.current) return;
        setData(next);
        if (shouldContinue(next)) {
          timer = setTimeout(tick, intervalMs);
        } else {
          setIsPolling(false);
        }
      } catch (e) {
        if (!cancelled.current) {
          setError(e);
          setIsPolling(false);
        }
      }
    }
    void tick();
    return () => {
      cancelled.current = true;
      if (timer) clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, intervalMs]);

  return { data, error, isPolling };
}
