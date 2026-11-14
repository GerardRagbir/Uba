"use client";

import { useEffect, useRef } from "react";

// Calls `load` now and then every few seconds, so the page picks up changes
// made by other people (a driver accepting your booking, for example).
export function usePolling(load: () => void, enabled: boolean, everyMs = 5000) {
  const latest = useRef(load);

  useEffect(() => {
    latest.current = load;
  });

  useEffect(() => {
    if (!enabled) return;
    latest.current();
    const timer = setInterval(() => latest.current(), everyMs);
    return () => clearInterval(timer);
  }, [enabled, everyMs]);
}
