"use client";

import { useEffect } from "react";

import { useSessionStore } from "@/store/session-store";

/** Hydrate le store Zustand depuis /api/auth/session au montage de l'AppShell. */
export function SessionHydrator() {
  const setClaims = useSessionStore((s) => s.setClaims);

  useEffect(() => {
    fetch("/api/auth/session")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.authenticated) setClaims(data.claims);
      });
  }, [setClaims]);

  return null;
}
