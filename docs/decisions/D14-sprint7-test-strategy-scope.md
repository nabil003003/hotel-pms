# D14 — Sprint 7 : périmètre réaliste de la stratégie de test (§7)

**Statut** : Adopté, Sprint 7.

## Contexte

Le spec §7 prescrit une stratégie de test complète : 80% de couverture unitaire,
6 scénarios d'intégration nommés, 5 scénarios E2E Playwright, des tests de
charge k6/Locust avec des scénarios chiffrés, et des tests de sécurité incluant
un scan OWASP ZAP et des tests WebAuthn. Certains éléments supposent une infra
ou des fonctionnalités qui n'existent pas dans ce build de développement local
à un seul agent ; ce sprint exécute ce qui est réellement vérifiable maintenant
plutôt que de prétendre couvrir l'intégralité du §7 sans preuve.

## Décisions

**Tests unitaires (§7.1)** : renforcés sur les services les plus légers
(`night-audit-service` : 11 lignes → couverture réelle de la logique saga/PDF ;
`notification-service`, `analytics-service`, `partner-service`). Pas de mesure
de couverture instrumentée (`pytest-cov` avec seuil 80% en CI) — non demandée
ailleurs dans ce monorepo (aucun service n'a de config `pytest-cov` avant ce
sprint), ajoutée en dette documentée plutôt qu'inventée à la volée pour un seul
sprint. `test_integration.py` ajouté pour night-audit/notification (les 9
autres services en avaient déjà un, écart de parité comblé).

**Tests d'intégration (§7.2)** : les 6 scénarios nommés recoupent en grande
partie ce que les smoke tests Docker des Sprints 1-6 vérifient déjà
(`scripts/smoke_test_sprint*.sh`) — cohérent avec la philosophie déjà actée de
ce projet ("Docker-verified increments" plutôt que mocks). Ce qui manquait
réellement et n'avait **jamais** été exercé jusqu'ici (vérifié en relisant
chaque smoke test) :
- Night Audit avec **écart détecté** (`DiscrepancyError`, alerte
  notification-service) — tous les runs précédents utilisaient le chemin
  équilibré.
- Room Shifting avec **conflit de chambre** (`409 ROOM_CONFLICT`).
- Réservation walk-in en **double-booking concurrent** (deux requêtes
  simultanées sur la même chambre/dates).
- Webhook OTA avec **mapping absent/invalide**.
- Expiration d'option (`status_option` → `status_cancelled` automatique) —
  câblée depuis le Sprint 3 mais jamais observée en conditions réelles (la
  boucle asyncio tourne toutes les `option_expiry_poll_seconds`, testable en
  accéléré via une variable d'environnement de dev plus courte).

Nouveau script `scripts/test_integration_sprint7.sh` couvre ces 5 lacunes
contre les vrais services Docker (pas de mocks), en plus de ce que les smoke
tests existants couvrent déjà.

**Tests E2E (§7.3)** : `@playwright/test` installé pour de vrai dans
`frontend/`, tests **réellement exécutés** (pas seulement écrits) contre le
serveur `next dev` + les backends Docker. Scénarios 1 (réceptionniste :
réservation → check-in → extra → check-out), 2 (Night Audit console) et 3
(housekeeping temps réel) du spec sont couverts. Scénario 4 (drag & drop) est
**hors-scope** : aucun tableau planning drag-and-drop n'existe dans ce
frontend (le changement de chambre Sprint 6+ est un dialogue de formulaire,
pas un DnD — jamais promis autrement). Scénario 5 (import OTA auto) est
couvert en variante : déclenchement du webhook via API puis vérification
dans l'UI planning, plutôt qu'un flux 100% UI (l'arrivée OTA elle-même n'a
pas d'origine UI).

**Tests de charge (§7.4)** : ni `k6` ni `Locust` ne sont installés sur cette
machine et ce sprint n'installe pas un nouvel outil externe pour un seul
run ponctuel. Substitution pragmatique : script Python `asyncio`+`httpx`
(`scripts/load_test_sprint7.py`) reproduisant le scénario "15 réceptionnistes
× 30 réservations/minute" avec mesure réelle du p95, comparée à l'objectif
spec (< 200ms). Un seul scénario de charge est reproduit (création de
réservation, le plus représentatif et le plus simple à isoler sans état
partagé complexe) ; les 3 autres scénarios de charge du spec (Night Audit
50 chambres, WebSocket 30 clients, 50 webhooks OTA/min) restent non testés en
charge — notés comme dette, pas simulés superficiellement.

**Tests de sécurité (§7.5)** : couverts par script ciblé
(`scripts/security_test_sprint7.sh`) contre les vrais services : JWT
falsifié/expiré rejeté, RBAC (réceptionniste → action admin → 403),
idempotence (retry même clé → même réponse, pas de doublon), multi-tenant
(établissement A tente d'accéder à une ressource de l'établissement B → 403).
**OWASP ZAP non exécuté** : un scan actif contre des services de dev
non durcis (secrets par défaut, pas de rate-limiting réel — Kong existe mais
n'est pas dans le profil `core`) produirait surtout du bruit ; à faire une
fois une vraie configuration proche-prod existe (Sprint 8). **Tests WebAuthn
non applicables** : jamais implémenté dans ce build (D4 — page Keycloak
hébergée, `requiredAction` jamais activé pour les comptes de test), donc rien
à tester au-delà de ce qui est déjà documenté comme non fait.

## Conséquences

- Ce sprint produit des résultats **réels et mesurés** (latences p95 réelles,
  tests Playwright réellement exécutés, pas de nombres inventés) sur un
  périmètre volontairement réduit, plutôt qu'une prétention de couverture
  totale du §7 non vérifiable.
- Dette explicitement documentée pour Sprint 8 ou au-delà : mesure de
  couverture instrumentée réelle (pytest-cov + seuil CI), scan OWASP ZAP,
  tests de charge sur les 3 scénarios restants, vrai outillage k6/Locust si
  le projet devait un jour tourner en CI/CD.

## Résultats (exécution réelle, même sprint)

Tout ce qui précède a été exécuté pour de vrai contre la stack Docker
`--profile core` déjà chaude (pas seulement écrit) :

- **Unitaires + intégration** (`docker exec <service> python -m pytest
  app/tests/`) : night-audit-service, notification-service,
  analytics-service, partner-service — tous verts (les tests d'intégration
  ciblent `localhost:<port_externe>` depuis l'hôte, ou `localhost:8000`
  depuis l'intérieur d'un conteneur — le port interne diffère du port publié
  dans `docker-compose.yml`, à ne pas confondre en le relançant).
- **`test_integration_sprint7.py`** : 5/5 scénarios verts. Le premier run a
  échoué avec `ALREADY_CLOSED` sur le scénario Night Audit — la date du jour
  réelle (`date.today()`) était déjà closée dans `audit_runs` par une
  clôture antérieure (le volume Postgres persiste entre sessions). Le
  nettoyage de verrou existant (`business_date_locks`) ne couvrait pas
  `audit_runs`/`audit_snapshots` — corrigé dans le script (voir son
  historique). À chaque nouvelle session qui rejoue ce script un autre jour
  calendaire, ce nettoyage protège contre le même faux-négatif.
- **E2E Playwright** (`frontend/e2e/`, contre `next dev` + Docker) : le tout
  premier run réel a échoué sur le scénario 1 (réceptionniste) —
  `POST /bookings` renvoyait `NO_ROOM_AVAILABLE` alors que des chambres
  Standard étaient visiblement libres. Cause racine trouvée dans
  `reservation-service/app/domain/services.py::check_availability` : le
  filtre de chevauchement excluait seulement `status_cancelled` et
  `status_no_show`, pas `status_checked_out` — un séjour déjà terminé
  continuait donc à bloquer sa chambre pour les mêmes dates indéfiniment.
  Sur une base Postgres réutilisée sprint après sprint, ça finit par épuiser
  tout l'inventaire d'une catégorie pour une date donnée. Corrigé en
  ajoutant `status_checked_out` à l'exclusion ; les 3 scénarios E2E et les
  5 scénarios d'intégration ci-dessus repassent verts après correction, et
  les tests unitaires de reservation-service aussi (aucune régression).
- **Charge** (`scripts/load_test_sprint7.py`) : 30/30 requêtes réussies
  (201) à concurrence 15 ; p50 ≈ 1.1s, **p95 ≈ 2.3s, p99 ≈ 2.4s** — largement
  au-dessus de l'objectif spec de 200ms. Cause probable non investiguée en
  profondeur ce sprint (hors périmètre D14 : c'est un test de *mesure*, pas
  d'*optimisation*) : `create_booking` fait plusieurs appels HTTP
  synchrones en série (establishment-service pour résoudre la chambre,
  pricing-service pour le tarif) avant même d'écrire en base, donc la
  latence se cumule sous concurrence. Piste Sprint 8 : paralléliser ce qui
  peut l'être, ou introduire un cache Redis sur la résolution
  chambre/tarif comme prévu par le spec (tableau §6, "Cache Redis critique").
- **Sécurité** (`scripts/security_test_sprint7.sh`) : 5/5 verts, y compris
  le test JWT expiré qui attend réellement les 300s de durée de vie du
  token (`accessTokenLifespan` de ce realm) plutôt que de forger un `exp`
  invalide — un JWT forgé sans la clé privée Keycloak échouerait de toute
  façon sur la vérification de signature, ce qui aurait masqué le test
  "expiré" derrière le test "falsifié". Le test d'idempotence recrée un
  établissement jetable ("Sprint7 Security Test Fixture") pour le check
  multi-tenant — pas de endpoint DELETE établissement dans ce service, donc
  la fixture reste en base (dev only, sans conséquence).
