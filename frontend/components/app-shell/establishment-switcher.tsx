"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { fetchEstablishments } from "@/lib/api-clients/establishment";
import { useSessionStore } from "@/store/session-store";

/**
 * Sélecteur de Riad (D2) — pour un utilisateur normal, n'affiche que les
 * établissements du JWT (`establishment_ids`). Un super-admin n'a
 * délibérément **aucun** `establishment_ids` dans son JWT (il a accès à
 * tous) — ce qui, avant ce correctif (Sprint 7, trouvé par les tests E2E
 * Playwright), le laissait sans aucun moyen de choisir un établissement
 * actif : `activeEstablishmentId` restait `null` en permanence et toute
 * page établissement-scoped affichait "Aucun établissement sélectionné."
 * Pour ce cas, la liste complète est chargée depuis establishment-service.
 * La vérification serveur (`assert_path_establishment_access`) reste la
 * seule qui compte réellement pour la sécurité — ce sélecteur n'est qu'un
 * outil de navigation.
 */
export function EstablishmentSwitcher() {
  const claims = useSessionStore((s) => s.claims);
  const activeEstablishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const setActiveEstablishment = useSessionStore((s) => s.setActiveEstablishment);

  const isSuperAdminWithoutList = Boolean(claims?.is_super_admin && claims.establishment_ids.length === 0);

  const { data: allEstablishments } = useQuery({
    queryKey: ["establishments"],
    queryFn: fetchEstablishments,
    enabled: isSuperAdminWithoutList,
  });

  useEffect(() => {
    if (isSuperAdminWithoutList && !activeEstablishmentId && allEstablishments && allEstablishments.length > 0) {
      setActiveEstablishment(allEstablishments[0].id);
    }
  }, [isSuperAdminWithoutList, activeEstablishmentId, allEstablishments, setActiveEstablishment]);

  if (!claims) return null;

  if (isSuperAdminWithoutList) {
    if (!allEstablishments || allEstablishments.length === 0) {
      return <span className="text-sm text-muted-foreground">Vue super-admin (aucun établissement)</span>;
    }
    return (
      <Select value={activeEstablishmentId ?? undefined} onValueChange={setActiveEstablishment}>
        <SelectTrigger className="w-56">
          <SelectValue placeholder="Choisir un établissement" />
        </SelectTrigger>
        <SelectContent>
          {allEstablishments.map((est) => (
            <SelectItem key={est.id} value={est.id}>
              {est.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  }

  if (claims.establishment_ids.length === 0) return null;

  if (claims.establishment_ids.length === 1) {
    return null; // rien à choisir, pas la peine d'afficher un select à une seule option
  }

  return (
    <Select value={activeEstablishmentId ?? undefined} onValueChange={setActiveEstablishment}>
      <SelectTrigger className="w-56">
        <SelectValue placeholder="Choisir un établissement" />
      </SelectTrigger>
      <SelectContent>
        {claims.establishment_ids.map((id) => (
          <SelectItem key={id} value={id}>
            {id}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
