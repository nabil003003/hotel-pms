# D12 — night-audit-service : périmètre des rapports, verrous cross-service, bascule J+1

**Statut** : Adopté, Sprint 5.

## Contexte

Le Workflow I (§4.9, lignes 578-650) décrit une saga en 3 étapes (vérification
pré-audit → clôture irréversible → post-audit) qui touche potentiellement
6 microservices. Plusieurs éléments ne sont pas dans le schéma SQL transcrit
(§5.6) et demandent des choix : génération de PDF, stockage MinIO, verrouillage
cross-service, et 3 endpoints "rapport" qui n'existaient pas encore côté
front-office/reservation/analytics.

## Décisions

**Génération PDF & stockage** : `reportlab` (pur Python, aucune dépendance
système supplémentaire dans l'image Docker `python:3.11-slim`, contrairement
à `weasyprint`/`wkhtmltopdf`) génère les 6 rapports listés spec ligne 625-632.
Upload vers MinIO via `boto3` (client S3-compatible, `endpoint_url` pointant
vers le service `minio`), bucket unique `audit-reports`, chemin
`{establishment_id}/audit/{business_date}/{rapport}.pdf` (UUID d'établissement
à la place du `hotel_id` littéral du spec — cohérent avec le reste du
monorepo qui n'a pas de "hotel_id" court, seulement des UUID). `report_hash`
= SHA-256 de la concaténation ordonnée des 6 PDFs. **`minio` passe du profil
Compose `storage` à `core`** : il devient une dépendance fonctionnelle réelle
de `night-audit-service`, plus un composant optionnel.

**Pas de Celery** (continuité de la décision Sprint 3 : "no real Celery
anywhere in this codebase") : la génération des 6 PDF se fait de façon
synchrone dans la requête `POST /night-audit/close`, comme tout le reste de
ce monorepo (asyncio, pas de job planifié séparé). Le SLA "< 30s" du spec
(ligne 1368, qui mentionne Celery) est traité comme un objectif de perf, pas
une contrainte d'architecture async.

**Verrou cross-service (business_date_locked)** : le spec dit explicitement
que front-office-service ET reservation-service l'activent (ligne 620).
front-office-service le fait déjà depuis le Sprint 4 (D9). Ce sprint ajoute à
reservation-service : une table `business_date_locks` (même schéma que
front-office), un consumer `audit.closed`, et un contrôle appliqué à la
création de réservation (`check_in_date <= date verrouillée` → `423 LOCKED`)
et à l'annulation/transition de statut d'une réservation dont le
`check_in_date` est verrouillé — pas de contrôle sur les *lectures*, ni sur
les dates futures (seule la date qui vient d'être clôturée, et les
antérieures non encore purgées, sont verrouillées : une nouvelle date J+1
n'est jamais verrouillée tant qu'elle n'a pas elle-même été clôturée).

**Bascule chambres (housekeeping)** : plutôt que night-audit-service appelle
housekeeping-service directement (non prévu dans le schéma de communication
Appendix D, qui ne relie pas ces deux services), housekeeping-service
**consomme `audit.closed`** lui-même — cohérent avec l'entrée Appendix C
`audit.closed → ALL services`. Un nouveau handler y bascule toutes les
chambres `Occupée` de l'établissement en `Sale`.

**Rapport `occupancy_forecast_J+1`** : analytics-service n'a pas de moteur de
prévision — `GET /api/v1/forecast/occupancy` est une estimation simplifiée
(arrivées J+1 connues via reservation-service ÷ capacité totale, ADR
proxy = moyenne des 7 derniers jours de `daily_kpi_snapshot`), pas un vrai
forecast statistique. Documenté comme approximation, pas un chiffre
contractuel.

**Alertes & email de rapport (notification-service)** : appels REST directs
synchrones (`POST /api/v1/notifications/send`), pas d'événement — voir D11
pour le pourquoi (payload de `audit.closed` insuffisant pour transporter le
détail de l'écart ou les URLs des rapports).

**`GET /api/v1/night-audit/business-date`** : lit `system_state`, mis en
cache Redis 5 min (TTL, pas d'invalidation active au changement — le spec dit
"refresh forcé au changement" mais aucun mécanisme de push n'existe entre
services dans ce monorepo ; un TTL court est le choix pragmatique déjà utilisé
ailleurs, ex. `kpi_today_cache_seconds` d'analytics-service).

**Token d'audit** : `token_audit` (retourné par `/verify`, requis en header
`X-Audit-Token` sur `/close`) est un UUID aléatoire stocké dans Redis
(`audit_token:{token}` → `establishment_id`, TTL 30 min), même famille de
pattern que les jetons d'élévation de reservation-service (D8) — pas un JWT,
pas de dépendance Keycloak supplémentaire pour un jeton à usage unique et
courte durée.

## Conséquences

- Sortir `minio` du profil `storage` change la commande de démarrage
  documentée dans le README (désormais implicitement inclus dans `core`).
- Le verrou côté reservation-service ne couvre que création/annulation —
  d'autres écritures (room-shift, upsell) datées ≤ J restent non bloquées
  explicitement ce sprint ; gap documenté, pas un oubli caché.
- Les prévisions analytics et le hash de rapport ne sont pas des garanties
  d'exactitude comptable/statistique — seulement des approximations de dev
  cohérentes avec le reste des simplifications déjà actées (D10).
