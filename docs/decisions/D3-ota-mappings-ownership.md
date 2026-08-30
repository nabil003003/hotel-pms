# D3 — Ownership de `ota_mappings`

**Statut** : Adopté, Sprint 2 (option 1 exécutée).

## Contexte

Le spec se contredit : §5.1 place littéralement la table `ota_mappings` dans
`establishment_db` (schéma SQL explicite). Mais le Workflow C (§4.3) la décrit
comme "table `ota_mappings` dans `channel-manager-service`", et Workflow K
(§4.11 étape 5) poste la config OTA sur `/api/v1/channel/connections`
(préfixe qui suggère channel-manager-service).

## Décision provisoire (Sprint 1)

La table est créée dans `establishment_db` (fidélité au schéma littéral du
spec) mais **sans aucun endpoint exposé** par establishment-service. Aucun
autre service n'y accède non plus. Elle reste une table posée, inerte.

## À trancher au Sprint 2

Deux options, à choisir avant d'implémenter channel-manager-service :

1. Garder la table dans `establishment_db` comme référence en lecture seule
   "catégorie de chambre ↔ type de chambre OTA" ; channel-manager-service
   gère ses propres tables de credentials/logs de sync et lit cette table
   via un appel REST à establishment-service.
2. Migrer la table vers `channel_db` (véritable ownership channel-manager),
   auquel cas establishment-service perd le endpoint (jamais créé de toute
   façon) et une migration de suppression sera nécessaire côté
   establishment_db.

Recommandation (non bloquante) : option 1, car §5.1 reste la définition SQL
la plus explicite du spec et la déplacer casserait la fidélité au schéma
sans bénéfice fonctionnel clair.

## Exécution (Sprint 2)

Option 1 retenue. `establishment-service` gagne `GET`/`POST
/api/v1/establishments/{id}/ota-mappings` (`admin` pour l'écriture,
authentifié pour la lecture — jamais `credentials_encrypted` dans la
réponse). `channel-manager-service` lit ce endpoint via
`app/infrastructure/establishment_client.py`, authentifié par son propre
compte de service (`svc-channel-manager`, client credentials grant) marqué
`is_super_admin=true` côté Keycloak — même mécanisme que
`svc-housekeeping` pour [[D1]] (bypass du scoping tenant pour un appel
service-à-service de confiance, cf. [[D2]]).
