import { create } from "zustand";

import type { SessionClaims } from "@/lib/auth/constants";

interface SessionState {
  claims: SessionClaims | null;
  activeEstablishmentId: string | null;
  setClaims: (claims: SessionClaims | null) => void;
  setActiveEstablishment: (id: string) => void;
}

/**
 * État global léger (Zustand, spec §1) — le sélecteur de Riad (D2) écrit ici
 * l'établissement actif, lu ensuite par les hooks React Query
 * (hooks/use-rooms.ts) pour peupler `establishment_id` / header
 * X-Establishment-Id des appels API.
 */
export const useSessionStore = create<SessionState>((set) => ({
  claims: null,
  activeEstablishmentId: null,
  setClaims: (claims) =>
    set({
      claims,
      activeEstablishmentId: claims?.establishment_ids[0] ?? null,
    }),
  setActiveEstablishment: (id) => set({ activeEstablishmentId: id }),
}));
