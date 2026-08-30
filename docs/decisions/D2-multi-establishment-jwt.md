# D2 — Claims JWT multi-établissement

**Statut** : Adopté, Sprint 1.

## Contexte

Le spec §3.4 mentionne un claim `establishment_id` (singulier) mais exige
aussi une table `user_establishments` many-to-many (un utilisateur peut être
affecté à plusieurs Riads). §3.5 mentionne un header `X-Establishment-Id`
sans détailler son articulation avec le JWT.

## Décision

- Le JWT porte `establishment_ids: string[]` (multivalué, mapper Keycloak
  dans `infra/keycloak/realm-export.json`, client scope `amh-tenant`) +
  `is_super_admin: boolean`.
- L'établissement **actif** pour une requête donnée est porté par le header
  `X-Establishment-Id` (sélecteur de Riad côté frontend, Sprint 6) ou, pour
  establishment-service, directement par l'`establishment_id` du chemin
  d'URL (`/establishments/{id}/...`).
- Chaque service vérifie : `establishment_id ∈ jwt.establishment_ids OU
  jwt.is_super_admin`. Voir `dependencies.py` (`assert_path_establishment_access`,
  `require_establishment_access`) dans auth-gateway-service,
  establishment-service, housekeeping-service — code dupliqué à l'identique
  entre services par choix (isolation microservices, pas de lib partagée).

## Conséquences

- Les comptes de service (`svc-*`) reçoivent `is_super_admin: true` pour
  bypasser le scoping tenant lors d'appels service-à-service de confiance
  (ex : resync housekeeping → establishment, D1). À revisiter si un jour ces
  comptes doivent eux aussi être scopés par tenant.
- Sprint 6 (frontend) : le sélecteur de Riad doit lire `establishment_ids`
  du token pour peupler ses options, et ne jamais laisser l'utilisateur
  choisir un ID hors de cette liste (même si la vérification serveur est la
  seule qui compte réellement).
