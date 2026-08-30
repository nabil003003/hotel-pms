# D8 — Simplifications du room shifting (Workflow F)

**Statut** : Adopté, Sprint 3.

## Contexte

Workflow F (§4.6) est le plus élaboré du spec : distinction same-category
vs upsell, élévation manager (WebAuthn/Passkeys), conflit de chambre avec
cascade automatique, chambre "bloquée". Plusieurs de ces éléments dépendent
de capacités ou de données qui n'existent pas encore.

## Décisions

1. **Same-category vs upsell** : `reservation-service` ne stocke que
   `room_id`, jamais de catégorie — déterminer si un shift change de
   catégorie demanderait un nouvel appel à establishment-service à chaque
   requête. Le endpoint accepte à la place un `same_category: bool` fourni
   par l'appelant : le frontend a déjà chargé les catégories de chambres
   depuis establishment-service pour rendre la grille de planning, donc il
   connaît la réponse sans appel supplémentaire.
2. **Élévation** : `POST /api/v1/auth/elevate` (auth-gateway-service,
   scaffoldé Sprint 1) génère un token à usage unique, consommé via le
   nouveau `POST /api/v1/auth/elevate/consume`. Remplace le WebAuthn/Passkeys
   du spec (Sprint 6+, hors scope) par une simple ré-authentification
   manager/admin déjà en place.
3. **`ROOM_BLOCKED`** : non implémenté. **Correction (Sprint 4)** :
   l'affirmation d'origine ci-dessous était inexacte —
   `housekeeping-service` a bien un statut `Bloquée` dans son enum
   (`chk_rooms_statut`, 5 valeurs : Sale/Nettoyage/Propre/Contrôlée/Bloquée).
   Le vrai motif du non-implémentation est différent : aucun endpoint ni
   flux ne permet de *poser* ce statut (pas de "bloquer une chambre" côté
   housekeeping-service), et Workflow F ne précise pas qui déclenche ce
   blocage ni pourquoi — resté hors scope faute de spec exploitable, pas
   faute de colonne. ~~`housekeeping-service` n'a que 4 statuts de chambre
   (Propre/Sale/Nettoyage/Contrôlée), aucun concept de chambre "bloquée" —
   ce chemin d'erreur du spec n'a pas de données à représenter pour
   l'instant.~~ (affirmation erronée, barrée pour traçabilité plutôt que
   supprimée silencieusement.)
4. **Cascade sur conflit forcé** : `force=true` (avec élévation) permet de
   shifter malgré un `ROOM_CONFLICT`, mais ne déplace/libère PAS
   automatiquement la réservation en conflit — limitation documentée,
   contrairement au "cascade-move ou libère la chambre" du spec. Un manager
   doit résoudre la réservation en conflit séparément.
5. **Élévation obligatoire même sans upsell** : `force=true` sur un
   conflit exige aussi un token d'élévation valide, même si la catégorie
   n'a pas changé — cohérent avec le principe du spec que forcer un
   conflit est une action manager, pas seulement l'upsell.

## Conséquences

- Un frontend malhonnête pourrait techniquement envoyer `same_category:
  true` pour une vraie upsell — la seule protection réelle est
  applicative (le total_amount ne sera pas recalculé, ce qui serait visible
  immédiatement) ; pas un problème de sécurité (aucune donnée sensible),
  mais à garder en tête si un jour la source de vérité doit être
  serveur-side (auquel cas D8.1 serait à revisiter avec un appel
  establishment-service).
- `ROOM_BLOCKED` devra être ajouté si/quand housekeeping-service gagne un
  statut de blocage de chambre.
