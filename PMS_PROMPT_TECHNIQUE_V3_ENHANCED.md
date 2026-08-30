# PROMPT TECHNIQUE — Développement du PMS Hôtelier AMH Hospitality
## Architecture Microservices — Next.js / FastAPI / Keycloak / PostgreSQL

**Version**: 3.0-Enhanced  
**Date**: Juillet 2026  
**Projet**: PMS AMH Hospitality — Système de Gestion Hôtelière Multi-Établissements (Riads)  
**Statut**: Spécifications techniques complètes pour développement

---

## 0. CONTEXTE & MISSION

Tu es une équipe d'ingénierie logicielle chargée de concevoir et développer un **PMS (Property Management System) hôtelier** complet pour le groupe **AMH Hospitality**, à partir du cahier des charges fonctionnel fourni (5 modules : Authentification & Dashboard, Front Office & Housekeeping, Night Audit, Tarification & Fiscalité, Réservations & Analytics).

Le système doit être pensé **pour un usage réel en réception d'hôtel / Riad** : rapidité de saisie, fiabilité comptable absolue (le Night Audit ne pardonne aucune erreur), traçabilité totale, et données exploitables pour le pilotage stratégique (KPI, segmentation).

**Nouveau contexte** : Le système est désormais conçu pour une chaîne de **Riads à Marrakech**, chaque établissement ayant une architecture et une offre uniques. La plateforme doit être **100% configurable par établissement** (multi-tenant).

**Contrainte non négociable** : l'architecture est **microservices**, un service = un domaine métier = une base de données (ou schéma) dédiée = un déploiement indépendant.

### 0.1 Hypothèses & Contraintes Opérationnelles

| Paramètre | Valeur | Impact |
|---|---|---|
| Taille de l'établissement | 5–30 chambres (Riad typique) | Architecture scalable jusqu'à 200 chambres |
| Nombre d'établissements | 5–15 Riads (phase 1) | Multi-tenant obligatoire |
| Utilisateurs simultanés (pic) | 5–15 réceptionnistes par Riad | Verrouillage distribué obligatoire |
| Heures de pic | 07h–10h (check-out) / 14h–18h (check-in) | Cache Redis critique, WebSocket obligatoire |
| Réglementation | Droit marocain — TVA hôtelière, TS, TPT | Fiscalité codée en dur, non paramétrable |
| Langues UI | FR (principal), AR, EN | i18n obligatoire dès le Sprint 1 |
| Devise | MAD (Dirham marocain) — 2 décimales | Formatage monétaire strict |
| SLA Night Audit | < 2 minutes pour 50 chambres | Optimisation requêtes + transactions parallèles |
| SLA Planning temps réel | < 500ms de propagation du statut | WebSocket + Redis pub/sub |
| SLA Synchronisation Channel Manager | < 30 secondes (OTA → PMS) | Webhook + queue asynchrone |
| RPO données financières | < 1 heure | Backup continu des folios et audit_logs |
| RTO données financières | < 4 heures | Multi-région ou hot-standby recommandé |
| Rétention données chaudes | 2 ans (folios actifs) | Archivage automatique vers stockage froid |
| Rétention audit_logs | 10 ans (obligation légale) | Partitionnement par année, immuabilité garantie |

### 0.2 Exigences de Conformité

- **Immuabilité comptable** : Après Night Audit, aucune modification rétroactive. Toute correction passe par une écriture de régularisation datée du jour courant.
- **Traçabilité totale** : Chaque action financière = `user_id` + `timestamp` + `ip_address` + `correlation_id`.
- **Soft-delete universel** : Aucune suppression physique de données comptables. Table `audit_log` sur tous les services touchant au financier.
- **RGPD / Loi 09-08 (Maroc)** : Données clients anonymisables après 3 ans d'inactivité. Consentement explicite pour le marketing.
- **Multi-tenant isolation** : Données d'un Riad strictement isolées des autres (row-level security + schéma par tenant optionnel).

---

## 1. STACK TECHNIQUE IMPOSÉE

| Couche | Technologie | Rôle | Version Minimale |
|---|---|---|---|
| Frontend | **Next.js** | UI planning, dashboards, formulaires. SSR pour dashboard KPI, CSR pour planning interactif (Drag & Drop) | 14+ (App Router, TypeScript strict) |
| Backend | **FastAPI** | Un service FastAPI par domaine métier, API REST + WebSocket | Python 3.11+ |
| Sécurité / IAM | **Keycloak** | Authentification centralisée, SSO, RBAC, WebAuthn/Passkeys, JWT OIDC | 24+ |
| Base de données | **PostgreSQL** | Une base (ou schéma isolé) par microservice — pattern *Database per Service* | 15+ |
| Message Broker | **RabbitMQ** | Événements asynchrones inter-services | 3.12+ |
| Cache / Temps réel | **Redis** | Cache KPI, verrous distribués, pub/sub WebSocket | 7+ |
| API Gateway | **Kong** | Point d'entrée unique, routage, validation JWT, rate limiting | 3.5+ |
| Conteneurisation | **Docker + Docker Compose (dev) / Kubernetes (prod)** | Isolation par service | Compose v2 / K8s 1.29+ |
| Observabilité | **OpenTelemetry + Prometheus/Grafana + ELK** | Traces, métriques, logs centralisés | OTLP 1.0+ |
| Planification jobs | **Celery + Redis** | Jobs planifiés (expiration options, rappels, sync OTA) | 5.3+ |
| Stockage fichiers | **MinIO** (S3-compatible) | Archives PDF Night Audit, factures | RELEASE.2024+ |
| Frontend State | **React Query (TanStack Query) + Zustand** | Cache serveur + état global léger | RQ v5, Zustand v4 |
| UI Components | **shadcn/ui + Tailwind CSS** | Design system cohérent, accessible | Tailwind v3.4+ |
| Tests E2E | **Playwright** | Tests workflows critiques bout-en-bout | 1.42+ |
| Channel Manager | **API REST / Webhook** | Intégration Booking.com, Expedia, Airbnb, site web direct | Protocoles OTA standards |
| Mobile (Housekeeping) | **React Native / PWA** | Interface simplifiée pour gouvernante/femme de chambre | Expo SDK 50+ |

---

## 2. DÉCOUPAGE DES MICROSERVICES (Bounded Contexts)

Chaque service possède : son propre schéma PostgreSQL, son propre repo/déploiement, son propre client Keycloak (confidential client), et communique avec les autres **uniquement via API ou événements** (jamais d'accès direct à la base d'un autre service).

```
+-----------------------------------------------------------------------------+
|                    NEXT.JS (Frontend + BFF) + Mobile PWA                      |
|              React Query · Zustand · shadcn/ui · Drag & Drop                  |
+---------------------------+-------------------------------------------------+
                             | (JWT Keycloak via PKCE / WebAuthn / Passkeys)
                    +--------v---------+
                    |   KONG GATEWAY    |
                    |  Rate Limit · JWT |
                    +--------+---------+
      +----------+-----------+-----------+-----------+-------------+----------+
      v          v           v           v           v             v          v
+-----------++---------++----------++----------++-----------++-----------++----------+
|auth-svc   ||reserv.  ||front-off.||housekeep.||pricing-svc||night-audit||channel-  |
|(Keycloak  ||-service ||-service  ||-service  ||           ||-service   ||manager   |
| proxy)    ||         ||(folios)  ||(rooms)   ||(tarifs)   ||(clôture)  ||-service  |
+-----------++---------++----------++----------++-----------++-----------++----------+
                    |                                              |
              +-----v------+                              +------v--------+
              |analytics-  |                              |notification-  |
              |service     |                              |service         |
              |(dashboards)|                              |(alertes)       |
              +------------+                              +----------------+
                    ^
              (event bus : booking.*, folio.*, room.*, audit.*, channel.* )
```

### 2.1 Liste Détaillée des Services

| # | Service | Domaine | Base de Données | Dépendances | Priorité |
|---|---|---|---|---|---|
| 1 | `auth-gateway-service` | Proxy Keycloak, provisioning utilisateurs, sync rôles, multi-tenant | `auth_db` | Keycloak | Sprint 1 |
| 2 | `establishment-service` | Configuration par Riad (chambres, étages, catégories, services) | `establishment_db` | Aucune | Sprint 1 |
| 3 | `housekeeping-service` | Statuts chambres, motifs blocage, planning ménage | `hk_db` | establishment-service | Sprint 1 |
| 4 | `pricing-service` | Grille tarifaire, saisons, taxes, extras, packages, services Riads | `pricing_db` | establishment-service | Sprint 2 |
| 5 | `partner-service` | Fiches agences/TO/sociétés, contrats tarifaires, OTA credentials | `partner_db` | Aucune | Sprint 2 |
| 6 | `channel-manager-service` | Synchronisation OTA (Booking, Expedia, Airbnb), 2-way sync, webhooks | `channel_db` | partner-service, pricing-service, housekeeping-service | Sprint 2 |
| 7 | `reservation-service` | Réservations, segments, CRM client, cycle de vie, drag & drop | `reserv_db` | pricing-service, partner-service, channel-manager-service | Sprint 3 |
| 8 | `front-office-service` | Check-in/out, folios A/B, facturation, encaissements | `fo_db` | reservation-service, housekeeping-service, pricing-service | Sprint 4 |
| 9 | `night-audit-service` | Clôture journalière, rapports PDF, bascule J+1 | `audit_db` | front-office-service, reservation-service, analytics-service | Sprint 5 |
| 10 | `analytics-service` | KPI temps réel, dashboards, agrégations multi-établissements | `analytics_db` | Tous (via events) | Sprint 4 (parallèle) |
| 11 | `notification-service` | Emails, push, alertes métier, SMS | `notif_db` | Tous (via events) | Sprint 5 |

---

## 3. SÉCURITÉ — KEYCLOAK & AUTHENTIFICATION BIOMÉTRIQUE

### 3.1 Realm & Clients

- **Realm dédié** : `amh-hospitality`
- **Multi-tenant** : Chaque utilisateur est associé à un ou plusieurs `establishment_id` (claim personnalisé dans le JWT).

**Clients Keycloak** :

| Client | Type | Flux | Usage |
|---|---|---|---|
| `pms-frontend` | Public | Authorization Code + PKCE | Application Next.js (navigateur) |
| `pms-mobile` | Public | Authorization Code + PKCE | Application mobile Housekeeping (React Native / PWA) |
| `pms-gateway` | Confidential | Client Credentials | Kong Gateway validation interne |
| `svc-reservation` | Confidential | Client Credentials | Appels service-à-service |
| `svc-frontoffice` | Confidential | Client Credentials | Appels service-à-service |
| `svc-housekeeping` | Confidential | Client Credentials | Appels service-à-service |
| `svc-pricing` | Confidential | Client Credentials | Appels service-à-service |
| `svc-nightaudit` | Confidential | Client Credentials | Appels service-à-service |
| `svc-analytics` | Confidential | Client Credentials | Appels service-à-service |
| `svc-notification` | Confidential | Client Credentials | Appels service-à-service |
| `svc-partner` | Confidential | Client Credentials | Appels service-à-service |
| `svc-channel` | Confidential | Client Credentials | Appels service-à-service |
| `svc-establishment` | Confidential | Client Credentials | Appels service-à-service |

### 3.2 Authentification Biométrique (WebAuthn / Passkeys / Native)

#### 3.2.1 Web / Desktop — WebAuthn & Passkeys

- **WebAuthn** configuré comme authentificateur principal dans le flow Keycloak (`webauthn-register` + `webauthn-authenticator` required actions).
- **Passkeys** support natif : les utilisateurs peuvent s'authentifier avec Windows Hello, Touch ID sur Mac, ou clés de sécurité FIDO2 directement depuis le navigateur.
- **Fallback obligatoire** : login/mot de passe classique si biométrie indisponible.
- **Niveau d'assurance (AAL)** : AAL1 (password) par défaut, AAL2 (WebAuthn/Passkeys) recommandé pour les rôles `manager` et `admin`.
- **Flow d'enregistrement** :
  1. Utilisateur crée son compte (password classique).
  2. Keycloak force l'enregistrement WebAuthn (`required_action: WEBAUTHN_REGISTER`).
  3. Prochaine connexion : prompt WebAuthn automatique.

#### 3.2.2 Mobile / Tablette — Authentification Native

- **iOS** : Utilisation de `LocalAuthentication` framework (Face ID / Touch ID).
- **Android** : Utilisation de `BiometricPrompt` API (empreinte digitale / reconnaissance faciale).
- **Intégration Keycloak** : Le mobile obtient un JWT via PKCE, puis verrouille l'application localement avec la biométrie native. Le JWT est stocké dans le Keychain (iOS) / Keystore (Android).
- **Session mobile** : Durée de session configurable (par défaut 8h). Re-authentification biométrique requise après inactivité > 15 min.
- **Note** : Aucun dispositif biométrique physique dédié/externe n'est requis au niveau matériel.

### 3.3 Rôles Métier (RBAC) & Interfaces Personnalisées

| Rôle Keycloak | Droits | Interface | Restrictions |
|---|---|---|---|
| `femme_de_chambre` | Mise à jour statut chambre (Sale → Nettoyage → Propre), signalement incidents, réassort | **Mobile simplifiée** (PWA/React Native) — vue carte chambres uniquement | Lecture seule sur réservations et folios |
| `gouvernante` | Gestion statuts chambres, motifs de blocage, supervision femmes de chambre, rapports ménage | **Mobile/Tablette** — dashboard chambres + planning ménage | Lecture seule sur réservations et folios |
| `receptionniste` | Check-in/out, création réservation (manuelle + walk-in), room shifting simple, encaissement, planning arrivées/départs | **Desktop Web** — planning réservations, dashboard du jour, facturation | Ne peut pas valider upsell, ne peut pas débloquer chambre bloquée, ne peut pas configurer tarifs |
| `manager` | Validation upsell, déblocage room shifting avec conflit, accès dashboards, lancement Night Audit, gestion Channel Manager, rapports financiers | **Desktop Web** — accès complet sauf gestion utilisateurs | Ne peut pas configurer tarifs/taxes ni gérer utilisateurs |
| `admin` | Configuration tarifs/taxes, gestion utilisateurs, configuration établissement (chambres, catégories, services), lancement Night Audit, accès rapports archivés | **Desktop Web** — accès total | — |
| `comptable` | Journaux de ventes, encaissements, factures, exportations comptables, rapports fiscaux | **Desktop Web** — vue comptable restreinte | Pas d'accès aux réservations ni au planning opérationnel |
| `agence_externe` (futur) | Accès lecture seule à ses propres réservations | **Portail web dédié** | Scope limité par `partner_id` dans le JWT |

### 3.4 Multi-Tenant & Isolation des Données

- **Claim JWT** : `establishment_id` (UUID) présent dans chaque token. Les services filtrent automatiquement les données par ce claim.
- **Row-Level Security (RLS)** : Activé sur toutes les tables métier PostgreSQL. Politique : `current_setting('app.current_establishment')::uuid = establishment_id`.
- **Super-admin** : Claim `is_super_admin: true` permet d'accéder à tous les établissements (vue consolidée pour la direction du groupe).
- **Cross-establishment** : Un utilisateur peut être affecté à plusieurs Riads (table `user_establishments` many-to-many).

### 3.5 Règles Critiques de Sécurité

1. **JWT propagation** : Chaque appel entre microservices transporte le JWT utilisateur original (via header `X-User-Id`, `X-Establishment-Id` et `X-Correlation-Id`) OU un token `client_credentials` enrichi avec `on-behalf-of`. **On doit toujours savoir QUI a fait QUOI et POUR QUEL ÉTABLISSEMENT**.
2. **Scope par service** : Chaque microservice valide que le JWT contient le scope requis (ex: `frontoffice:write` pour créer un folio).
3. **Rate limiting** : Kong applique 100 req/min par utilisateur, 1000 req/min par service.
4. **CORS** : Strict, origines whitelistées (`https://pms.amhhospitality.com`, `https://pms-dev.amhhospitality.com`, `https://mobile.amhhospitality.com`).
5. **Password policy** : Min 12 caractères, 1 majuscule, 1 minuscule, 1 chiffre, 1 spécial. Rotation forcée tous les 90 jours pour les comptes admin.
6. **Biométrie fallback** : Si WebAuthn échoue 3 fois consécutives, retour forcé au mot de passe + notification admin.

---

## 4. WORKFLOWS MÉTIER RÉELS (Scénarios de Bout en Bout Testables)

Chaque workflow ci-dessous doit être développé comme un **scénario de bout en bout testable** (test d'intégration cross-service), pas juste des endpoints isolés.

### 4.1 WORKFLOW A — Création d'une Réservation Directe (Walk-in)

**Acteurs** : Réceptionniste  
**Préconditions** : Client inconnu ou connu, chambre disponible  
**Postconditions** : Réservation créée, inventaire mis à jour, événements publiés

```
+-------------+     +-------------+     +-----------------+     +-------------+     +-------------+
|  Next.js    |────▶│   Kong      │────▶│reservation-svc  │────▶│pricing-svc  │     │   Redis     │
|  Frontend   │     │  Gateway    │     │                 │     │             │◀────│  (verrou)   │
+-------------+     +-------------+     +-----------------+     +-------------+     +-------------+
                                              │
                                              ▼
                                        +-------------+
                                        │ RabbitMQ    │
                                        │ booking.*   │
                                        +-------------+
```

**Étapes détaillées** :

1. Réceptionniste ouvre le planning (`GET /api/v1/planning?from=...&to=...&establishment_id={uuid}`).
2. Recherche client : `GET /api/v1/customers?search=omar&establishment_id={uuid}` → autocomplete asynchrone (debounce 300ms, min 3 caractères).
3. Si client inconnu → `POST /api/v1/customers` (nom, email, téléphone, notes optionnelles, `establishment_id`).
4. Sélection chambre + dates → `POST /api/v1/bookings/check-availability` :
   - Vérification disponibilité avec **verrou Redis distribué** (`SETNX booking_lock:{establishment_id}:{room_id}:{date} EX 30 NX`).
   - Si verrou échoue → `409 CONFLICT` (chambre en cours de réservation par un autre utilisateur).
5. Sélection segment obligatoire (`market_segment_id`) — **champ NON NULLABLE** en base.
6. Appel `pricing-service` : `GET /api/v1/rates/calculate?category={cat}&season={season}&regime={BB|DP|PC}&dates={from}:{to}&establishment_id={uuid}` → retourne prix TTC par nuit + total.
7. Sélection option taxes de séjour (`taxes_payment_mode`: `at_booking` ou `on_site`) → stocké dans `reservation-service`, utilisé par `front-office-service` au check-in.
8. Création réservation : `POST /api/v1/bookings` avec idempotence key (`Idempotency-Key: {uuid}`) :
   - Statut initial = `status_option` (avec `option_expiry_date = NOW() + INTERVAL '48 hours'`) si aucun acompte.
   - Statut initial = `status_confirmed` si acompte encaissé immédiatement (appel synchrone `front-office-service` pour créer le paiement).
9. Événement `booking.created` publié sur RabbitMQ (exchange `amh.booking`, routing key `booking.created`) :
   - `analytics-service` : mise à jour incrémentale des stats du jour.
   - `housekeeping-service` : réservation d'un slot planning (pas de changement de statut chambre).
   - `channel-manager-service` : mise à jour inventaire OTA (si chambre liée à un channel).
10. Si `status_option` expire sans paiement → job Celery planifié (`reservation-service`) :
    - Bascule automatiquement en `status_cancelled`.
    - Publie `booking.cancelled` → libère l'inventaire (supprime le verrou Redis).
    - Notifie le client par email (`notification-service`).
    - `channel-manager-service` : libère l'inventaire OTA.

**API Contract (extrait)** :

```yaml
POST /api/v1/bookings
Headers:
  Authorization: Bearer {jwt}
  X-Idempotency-Key: {uuid}
  X-Correlation-Id: {uuid}
Body:
  establishment_id: uuid          # OBLIGATOIRE (multi-tenant)
  customer_id: uuid
  room_id: uuid
  market_segment_id: uuid         # NON NULLABLE
  check_in_date: date
  check_out_date: date
  regime: enum[BB, DP, PC]
  taxes_payment_mode: enum[at_booking, on_site]
  adults: int (min 1)
  children: int (default 0)
  notes: string (optional)
  option_expiry_date: datetime (required if no deposit)
  source: enum[walk_in, phone, email, website, ota]  # Traçabilité origine

Responses:
  201 Created: { booking_id, status, total_amount, expiry_date }
  409 Conflict: { code: "ROOM_UNAVAILABLE", message: "Chambre déjà réservée ou verrou active" }
  422 Unprocessable: { code: "INVALID_SEGMENT", message: "Segment de marché obligatoire" }
  429 Too Many Requests: { retry_after: 60 }
```

---

### 4.2 WORKFLOW B — Réservation via Agence (B2B)

**Différences avec Workflow A** :

1. Sélection segment `b2b_agency` → **champ `partner_id` obligatoire** (fiche agence dans `partner-service`).
2. Appel `pricing-service` : `GET /api/v1/rates/partner?partner_id={id}&category={cat}&season={season}&establishment_id={uuid}` → retourne **tarif négocié** (override tarif public).
3. Statut initial = `status_voucher` (pas d'acompte client requis).
4. Au check-in, `front-office-service` crée automatiquement un **Folio B** lié à l'agence.

---

### 4.3 WORKFLOW C — Réservation OTA (Booking.com, Expedia, Airbnb)

**Acteurs** : Système automatique (Channel Manager)  
**Préconditions** : Chambre connectée à un OTA, webhook reçu  
**Postconditions** : Réservation importée automatiquement, inventaire synchronisé

```
OTA (Booking.com) ──Webhook──▶ channel-manager-svc ──REST──▶ reservation-svc
                                      │
                                      ├──REST──▶ pricing-svc (tarif OTA)
                                      │
                                      ├──REST──▶ housekeeping-svc (planning)
                                      │
                                      └──MQ────▶ booking.created
                                                    ├──▶ analytics-svc
                                                    ├──▶ notification-svc (alerte réception)
                                                    └──▶ front-office-svc (pré-check-in)
```

**Étapes détaillées** :

1. **Réception webhook OTA** : `channel-manager-service` reçoit une notification de nouvelle réservation (format JSON standardisé par OTA).
2. **Mapping & Validation** :
   - Mapping `ota_room_id` → `room_id` interne (table `ota_mappings` dans `channel-manager-service`).
   - Vérification disponibilité (double-vérification, l'OTA devrait déjà avoir bloqué).
   - Si conflit → `409 CONFLICT` → alerte admin + email OTA pour annulation.
3. **Création client** : Si client inconnu → création automatique dans `reservation-service` (nom, email, téléphone depuis données OTA).
4. **Tarification** : Appel `pricing-service` pour récupérer le tarif OTA négocié (`partner_id` = ID OTA dans `partner-service`).
5. **Création réservation** : `POST /api/v1/bookings` (automatique, avec `source: ota_booking` et `ota_reference`).
   - Statut = `status_confirmed` (les OTAs ne font pas d'options).
   - Verrou Redis posé immédiatement.
6. **Synchronisation inverse** : `channel-manager-service` met à jour l'inventaire sur tous les autres OTAs connectés (2-way sync).
7. **Événements publiés** : `booking.created` → analytics, notification (alerte réceptionniste), housekeeping.
8. **Mise à jour tarifs OTA** : Si tarifs changent dans `pricing-service` → `channel-manager-service` pousse les nouveaux tarifs vers les OTAs via API.

**API Contract (Channel Manager)** :

```yaml
POST /api/v1/channel/webhook/booking-com
Headers:
  X-OTA-Signature: {hmac}
  X-Correlation-Id: {uuid}
Body:
  ota_reference: string
  property_id: string          # Mapping vers establishment_id
  room_type_id: string         # Mapping vers room_category
  guest_name: string
  guest_email: string
  guest_phone: string
  check_in: date
  check_out: date
  adults: int
  children: int
  total_amount: decimal
  currency: string
  status: enum[new, modified, cancelled]

Responses:
  200 OK: { internal_booking_id, status }
  409 Conflict: { code: "OTA_CONFLICT", message: "Conflit d'inventaire détecté" }
  422 Unprocessable: { code: "MAPPING_ERROR", message: "Room type ou property non mappé" }
```

---

### 4.4 WORKFLOW D — Check-in

**Acteurs** : Réceptionniste  
**Préconditions** : Réservation `status_confirmed` ou `status_voucher`, chambre `Propre` ou `Contrôlée`  
**Postconditions** : Client in-house, folio(s) ouvert(s), chambre marquée occupée

```
front-office-svc ──REST──▶ housekeeping-svc (vérifie statut chambre)
         │
         ├──REST──▶ reservation-svc (change status → checked_in)
         │
         ├──DB────▶ Crée Folio A (+ Folio B si B2B)
         │
         └──MQ────▶ booking.checked_in
                     ├──▶ housekeeping-svc (marque Occupée)
                     ├──▶ analytics-svc (incrémente TO)
                     └──▶ notification-svc (alerte si solde négatif)
```

**Étapes détaillées** :

1. Réceptionniste ouvre la réservation confirmée.
2. `POST /api/v1/folios/check-in` (idempotence key obligatoire) :
   - **Étape 1** : Appel REST synchrone `GET /api/v1/rooms/{room_id}/status` vers `housekeeping-service`.
     - Si statut ∉ {`Propre`, `Contrôlée`} → `409 PRECONDITION_FAILED` : `"Chambre non prête. Statut actuel: {status}"`.
   - **Étape 2** : Création Folio A (`type: A`, `status: open`, `booking_id`).
     - Si segment B2B ou garantie société → création Folio B (`type: B`, `third_party_ref: partner_id`).
   - **Étape 3** : Appel REST `PATCH /api/v1/bookings/{id}/status` vers `reservation-service` → `status_checked_in`.
     - Vérification state machine : `confirmed → checked_in` OU `voucher → checked_in` autorisé. Autres transitions = `409`.
3. Événement `booking.checked_in` publié :
   - `housekeeping-service` : marque chambre comme `Occupée` (statut dérivé, pas stocké en base — calculé à la volée).
   - `analytics-service` : incrémente `occupancy_today` en temps réel.
   - `front-office-service` : verrouille la facture pro-forma (rend l'endpoint `GET /folios/{id}/proforma` indisponible, retourne `410 GONE`).
4. **Règle stricte** : Seul l'**Extrait de compte** (Folio A/B) est éditable désormais — verrouillage applicatif côté `front-office-service` (pas seulement UI).

**Saga — Compensation en cas d'échec** :

| Étape | Action | Compensation si échec |
|---|---|---|
| 1 | Vérifier chambre propre | Aucune (pas d'effet de bord) |
| 2 | Créer Folio A/B | `DELETE /folios/{id}` (soft-delete) |
| 3 | Changer statut réservation | `PATCH /bookings/{id}/status → confirmed` |

Si compensation échoue → alerte admin via `notification-service`, intervention manuelle requise.

---

### 4.5 WORKFLOW E — Ajout d'un Extra en Cours de Séjour (In-House)

**Acteurs** : Département Restaurant/Bar/SPA (via POS) ou Réceptionniste  
**Préconditions** : Réservation `status_checked_in`, Folio A ouvert  

**Étapes** :

1. Département appelle `POST /api/v1/folios/{folio_id}/charges` (idempotence key obligatoire) :
   - `source_service` : identifiant du POS (ex: `pos-restaurant-01`).
   - `catalog_item_id` : référence vers `pricing-service.extras_catalog`.
   - `quantity`, `unit_price` (vérifié contre catalogue).
2. `front-office-service` :
   - Vérifie que le Folio est `open`.
   - Ventile la charge sur le bon poste comptable (Hébergement / Restauration / Bar / SPA / Activités / Taxes).
   - Détermine le taux TVA applicable (10% ou 20% selon le poste).
   - Calcule : `montant_ht`, `tva`, `montant_ttc`.
   - Stocke dans `folio_charges` avec `source_service`, `created_by`, `created_at`.
3. Événement `folio.charge_added` publié → `analytics-service` met à jour le CA du jour.

**Postes Comptables Obligatoires** :

| Code | Libellé | TVA | Visible sur extrait |
|---|---|---|---|
| `HEB` | Hébergement | 10% | Oui |
| `PDJ` | Petit-déjeuner | 10% | Oui |
| `RES` | Restaurant | 10% | Oui |
| `BAR` | Boissons/Bar | 20% | Oui |
| `SPA` | SPA & Bien-être | 20% | Oui |
| `ACT` | Activités | 20% | Oui |
| `TS` | Taxe de Séjour | 0% (taxe fixe/pax) | Oui |
| `TPT` | Taxe Promo Touristique | 0% (taxe fixe/pax) | Oui |
| `REM` | Remise | Négatif | Oui |
| `HAM` | Hammam | 20% | Oui |
| `TRF` | Transfert Aéroport | 20% | Oui |
| `DIN` | Dîner Traditionnel | 10% | Oui |
| `EXC` | Excursions | 20% | Oui |

---

### 4.6 WORKFLOW F — Room Shifting (Drag & Drop)

**Acteurs** : Réceptionniste (shift simple) / Manager (upsell ou conflit)  
**Préconditions** : Réservation existante, nouvelle chambre disponible  
**UI** : Drag & Drop sur le planning interactif (Next.js + react-beautiful-dnd / @dnd-kit)

**Étapes** :

1. **Frontend** : Utilisateur glisse la réservation d'une chambre vers une autre sur le planning.
2. **Frontend envoie** : `PATCH /api/v1/bookings/{id}/room` avec `new_room_id`, `new_dates` (optionnel, si changement de dates aussi).
3. `reservation-service` vérifie :
   - **Même catégorie** → OK automatique.
   - **Catégorie supérieure (upsell)** → `409 REQUIRES_VALIDATION` :
     - Frontend affiche modale : `"Changement vers catégorie supérieure. Recalculer le tarif ?"`.
     - Si oui → appel `pricing-service` pour nouveau tarif.
     - Si non → maintien tarif actuel.
     - **Validation obligatoire** : requête `POST /api/v1/auth/elevate` (re-authentification manager avec password + OTP si configuré, ou WebAuthn/Passkeys).
   - **Chambre cible occupée** → `409 ROOM_CONFLICT` :
     - Blocage sauf rôle `admin`/`manager` avec re-authentification élevée.
     - Si autorisé → déplace la réservation existante (cascade) ou libère la chambre.
   - **Chambre cible bloquée** → `409 ROOM_BLOCKED` :
     - Affiche le motif de blocage.
     - Manager peut forcer le déblocage + room shifting en une action (avec raison obligatoire).
4. **Verrouillage** : Avant la mise à jour, `reservation-service` pose un verrou Redis sur la nouvelle chambre pour la période concernée (`SETNX room_shift_lock:{establishment_id}:{new_room_id}:{date} EX 30 NX`).
5. **Mise à jour transactionnelle** :
   - Mise à jour `bookings.room_id`.
   - Mise à jour `room_planning` (suppression ancien slot, création nouveau).
   - Si changement de catégorie → mise à jour `bookings.total_amount` (nouveau tarif).
6. **Événement `booking.room_changed`** publié :
   - `housekeeping-service` : met à jour le slot planning.
   - `analytics-service` : recalcule les prévisions si changement de catégorie.
   - `channel-manager-service` : met à jour l'inventaire OTA (si applicable).
   - Frontend : mise à jour temps réel du planning via WebSocket.
7. **UI Feedback** :
   - Animation de confirmation (chambre change de couleur sur le planning).
   - Toast notification : `"Chambre changée : {ancienne} → {nouvelle}"`.
   - Si upsell → affichage du delta tarifaire à payer.

**API Contract** :

```yaml
PATCH /api/v1/bookings/{id}/room
Headers:
  Authorization: Bearer {jwt}
  X-Idempotency-Key: {uuid}
Body:
  new_room_id: uuid
  new_check_in_date: date (optional)
  new_check_out_date: date (optional)
  keep_current_rate: boolean (default false)
  force: boolean (default false)  # Pour manager uniquement
  reason: string (required if force=true, min 10 chars)

Responses:
  200 OK: { booking_id, old_room_id, new_room_id, new_amount, delta }
  409 REQUIRES_VALIDATION: { code: "UPSELL_REQUIRES_MANAGER", message: "Validation manager requise" }
  409 ROOM_CONFLICT: { code: "ROOM_CONFLICT", conflicting_booking_id: uuid }
  409 ROOM_BLOCKED: { code: "ROOM_BLOCKED", blocked_reason: string }
  423 LOCKED: { code: "ROOM_SHIFT_IN_PROGRESS", retry_after: 30 }
```

---

### 4.7 WORKFLOW G — Check-out

**Acteurs** : Réceptionniste  
**Préconditions** : Réservation `status_checked_in`, Folio A solvable  
**Postconditions** : Client parti, chambre marquée `Sale`, folio(s) clôturé(s)

**Étapes** :

1. `POST /api/v1/folios/check-out` (idempotence key obligatoire) :
   - Génère l'extrait de compte final (Folio A et/ou B).
   - Calcule le solde : `SUM(charges) - SUM(payments)`.
2. **Encaissement obligatoire** (un ou plusieurs modes) :
   - Modes : `CB`, `ESP`, `CHQ`, `Virement`, `Débiteur`.
   - **Règle** : Somme des règlements doit égaler le solde du Folio A.
   - Folio B → mode `Débiteur` obligatoire (facturation agence/société via `partner-service`).
3. Validation → statut réservation `status_checked_out` :
   - **Contrainte DB** : `CHECK (status != 'checked_out' OR previous_status != 'checked_out')` — empêche tout retour en arrière.
   - **Contrainte applicative** : endpoint `POST /folios/{id}/reopen` retourne `403 FORBIDDEN` permanent.
4. Événement `booking.checked_out` publié :
   - `housekeeping-service` : bascule chambre en `Sale`.
   - `analytics-service` : met à jour le CA final du jour, calcule DMS.
   - `notification-service` : envoie email de remerciement au client.
   - `channel-manager-service` : libère l'inventaire OTA.

---

### 4.8 WORKFLOW H — Gestion Housekeeping (Mobile / Tablette)

**Acteurs** : Gouvernante / Femme de chambre  
**Préconditions** : Chambre existe dans le système  
**Interface** : PWA / React Native optimisé mobile — vue carte des chambres

**Étapes** :

1. **Authentification** : Femme de chambre ouvre l'application mobile, s'authentifie via biométrie native (Face ID / Touch ID / empreinte).
2. **Vue quotidienne** : Liste des chambres à traiter, filtrées par étage et priorité (check-out du jour en priorité).
3. **Changement de statut** via `PATCH /api/v1/rooms/{id}/status` :
   - Machine à états stricte : `Sale → Nettoyage → Propre → Contrôlée`.
   - `Contrôlée → Bloquée` possible (avec motif obligatoire).
   - `Bloquée → Propre` possible (déblocage).
   - Toute autre transition = `409 INVALID_TRANSITION`.
4. **Signalement d'incidents** : Bouton "Signaler un problème" → `POST /api/v1/rooms/{id}/incidents` :
   - Types : `Panne technique`, `Manque de linge`, `Problème sanitaire`, `Autre`.
   - Photo optionnelle (upload MinIO).
   - Notification push à la gouvernante.
5. **Réassort** : Bouton "Besoin de réassort" → sélection items (savon, shampoing, serviettes, etc.) → notification à la gouvernante.
6. Chaque transition publie `room.status_changed` (WebSocket via Redis pub/sub) :
   - Planning Next.js s'actualise en temps réel sans reload.
   - `reservation-service` écoute pour savoir quelles chambres sont disponibles à la vente.
7. **Blocage d'une chambre** (`Bloquée`) :
   - Motif obligatoire parmi : `Day Use`, `Panne`, `Départ tardif`, `Travaux`.
   - Stocké en base avec `blocked_reason`, `blocked_by`, `blocked_at`.
   - Affiché sur le planning (indisponible à la vente).
   - `reservation-service` vérifie ce statut avant toute nouvelle réservation.

**API Contract (Housekeeping Mobile)** :

```yaml
PATCH /api/v1/rooms/{id}/status
Headers:
  Authorization: Bearer {jwt}
Body:
  new_status: enum[Sale, Nettoyage, Propre, Contrôlée, Bloquée]
  reason: string (required if new_status == Bloquée)
  incident_type: enum[...] (optional)
  incident_photo: file (optional)
  reassort_items: array[string] (optional)

Responses:
  200 OK: { room_id, old_status, new_status, updated_at }
  409 INVALID_TRANSITION: { code: "INVALID_TRANSITION", allowed: ["Propre", "Contrôlée"] }
  422 Unprocessable: { code: "REASON_REQUIRED", message: "Motif obligatoire pour blocage" }
```


---

### 4.9 WORKFLOW I — Night Audit (Le Plus Critique)

**Acteurs** : Admin / Manager  
**Préconditions** : Fin de journée, tous les encaissements saisis  
**Postconditions** : Journée J figée, rapports générés, bascule J+1

```
night-audit-svc ──REST──▶ front-office-svc (somme débits J)
         │
         ├──REST──▶ front-office-svc (somme crédits J)
         │
         ├──REST──▶ reservation-svc (arrivées prévues J+1)
         │
         ├──REST──▶ analytics-svc (prévisions J+1)
         │
         ├──REST──▶ front-office-svc (départs attendus + soldes)
         │
         └──Si équilibre OK:
            ├──DB────▶ Crée audit_run (status: closed)
            ├──S3────▶ Archive rapports PDF
            ├──MQ────▶ audit.closed (date J, hash rapport)
            └──REST──▶ Tous les services (bascule business_date → J+1)
```

**Étapes détaillées** :

#### Étape 1 — Vérification Pré-Audit (Orchestration Saga)

1. `POST /api/v1/night-audit/verify` (admin/manager uniquement) :
   - **Appel 1** : `GET /api/v1/folios/daily-debits?date=J&establishment_id={uuid}` → `total_debits`.
   - **Appel 2** : `GET /api/v1/folios/daily-credits?date=J&establishment_id={uuid}` → `total_credits`.
   - **Vérification** : `total_debits == total_credits` (tolérance : 0.01 MAD).
2. Si écart ≠ 0 :
   - **Blocage total** : Night Audit ne se lance pas.
   - Alerte via `notification-service` (email + push) à l'admin avec détail de l'écart.
   - Endpoint `GET /api/v1/night-audit/discrepancy-report?date=J&establishment_id={uuid}` retourne la liste des folios déséquilibrés.
3. Si équilibre validé → retourne `token_audit` (valide 30 min) pour lancer la clôture.

#### Étape 2 — Clôture (Action Irréversible)

1. `POST /api/v1/night-audit/close` (header `X-Audit-Token: {token_audit}`) :
   - **Verrouillage cross-service** : `front-office-service` et `reservation-service` activent le mode `business_date_locked` pour la date J.
     - Toute écriture datée ≤ J est rejetée : `423 LOCKED`.
     - Exception : écritures de régularisation (datées J+1, référençant J).
2. **Génération des rapports PDF** (stockés MinIO, nommés `{hotel_id}/audit/{date}/{rapport}.pdf`) :

| Rapport | Contenu | Source |
|---|---|---|
| `ca_detaille_J.pdf` | CA ventilé par poste (HT/TVA/TTC) | `front-office-service` |
| `encaissements_J.pdf` | Main courante par mode de règlement | `front-office-service` |
| `debiteurs_J.pdf` | Soldes débiteurs (Folio B ouverts) | `front-office-service` |
| `departs_attendus_J+1.pdf` | Chambres + soldes restants dus | `front-office-service` |
| `arrivees_prevues_J+1.pdf` | Réservations attendues + détails | `reservation-service` |
| `occupancy_forecast_J+1.pdf` | TO, ADR, RevPAR estimés | `analytics-service` |

3. **Bascule date métier** :
   - `night-audit-service` met à jour `business_date = J+1` dans sa table `system_state`.
   - Tous les services consomment cette date via `GET /api/v1/night-audit/business-date` (cache 5 min, refresh forcé au changement).
4. **Événement `audit.closed`** publié :
   - Contient : `business_date: J`, `report_hash: sha256`, `closed_by`, `closed_at`.
   - Chaque service archive son propre snapshot de la journée J dans `audit_snapshots`.

#### Étape 3 — Post-Audit

1. `notification-service` envoie les rapports par email à la direction.
2. `analytics-service` fige les KPI du jour J dans `daily_kpi_snapshot` (table immuable).
3. `housekeeping-service` marque automatiquement toutes les chambres `Occupée` de la nuit J en `Sale` (déclencheur pour le ménage du matin).

**Règles de Sécurité Absolues** :

- Une fois `audit.closed` émis, **aucun service ne peut accepter de modification sur la date J**.
- Les corrections comptables se font par **écritures de régularisation** :
  - Nouvelle ligne dans `folio_charges` ou `payments` datée J+1.
  - Champ `corrects_date: J` pour tracer la référence.
  - Champ `correction_reason` obligatoire (min 10 caractères).

---

### 4.10 WORKFLOW J — Dashboard Analytics (Temps Réel + Historique)

**Acteurs** : Manager / Admin / Comptable  
**Architecture** : Vues matérialisées rafraîchies par événements, pas de calcul à la volée  
**Multi-établissements** : Vue consolidée pour super-admin, vue par Riad pour manager

**Endpoints** :

```yaml
GET /api/v1/kpi/today
  Cache: Redis 5 min
  Retourne:
    - establishment_id: uuid
    - occupancy_rate: float (%)  # TO journalier
    - adr: float (MAD)           # Prix moyen chambre louée
    - revpar: float (MAD)        # Revenu par chambre disponible
    - ca_total: float (MAD)      # CA jour
    - compare_n1: object         # Comparaison N-1 (même jour)
    - compare_last_month: object # Comparaison mois précédent

GET /api/v1/kpi/monthly?month=YYYY-MM&establishment_id={uuid}
  Cache: Redis 1 heure
  Retourne:
    - occupancy_rate: float (%)
    - adr: float
    - revpar: float
    - dms: float (jours)          # Durée moyenne séjour
    - ca_total: float
    - compare_n1: object

GET /api/v1/kpi/consolidated?month=YYYY-MM
  (Super-admin uniquement)
  Retourne agrégation de tous les établissements

GET /api/v1/segments/distribution?period=YYYY-MM&establishment_id={uuid}
  Retourne (pour Pie Chart):
    - segments: [{ segment_id, label, nuitees, pct_volume }]

GET /api/v1/segments/revenue?period=YYYY-MM&establishment_id={uuid}
  Retourne (pour Histogramme):
    - segments: [{ segment_id, label, ca_brut }]

GET /api/v1/segments/trend?segment={code}&granularity=month&establishment_id={uuid}
  Retourne (pour courbe):
    - data: [{ period, to, adr, revpar }]

GET /api/v1/ytd/compare?channel={code}&month=MM&establishment_id={uuid}
  Retourne:
    - current_year: { to, adr, revpar, ca }
    - previous_year: { to, adr, revpar, ca }
    - deltas: { to_pct, adr_pct, revpar_pct, ca_pct }

GET /api/v1/channel/performance?period=YYYY-MM&establishment_id={uuid}
  Retourne (pour analyse OTA):
    - channels: [{ channel, bookings_count, revenue, commission, net_revenue }]
```

**Alimentation des données** :

- `analytics-service` consomme les événements RabbitMQ (`booking.*`, `folio.*`, `audit.closed`, `channel.*`) et met à jour ses tables agrégées de manière incrémentale.
- Table `daily_kpi_snapshot` : alimentée une fois par jour après `audit.closed`.
- Table `monthly_kpi_aggregation` : recalculée à la fin de chaque mois (job Celery).
- Table `channel_performance` : alimentée par événements `channel.booking_received`.

---

### 4.11 WORKFLOW K — Configuration d'Établissement (Admin)

**Acteurs** : Admin  
**Préconditions** : Nouveau Riad à intégrer ou modification structure existante  

**Étapes** :

1. **Création établissement** : `POST /api/v1/establishments`
   - Nom, adresse, contact, nombre de chambres.
   - Génération automatique du `establishment_id`.
2. **Configuration des chambres** : `POST /api/v1/establishments/{id}/rooms` (bulk import possible via CSV) :
   - `numero`, `categorie`, `floor`, `capacity_adults`, `capacity_children`.
   - Catégories configurables : `"Chambre Standard"`, `"Chambre Deluxe"`, `"Suite Junior"`, `"Suite Royale"`, `"Riad Entier"`.
3. **Configuration des services additionnels** : `POST /api/v1/establishments/{id}/services` :
   - Services spécifiques Riads : Hammam, Transfert Aéroport, Excursions, Dîners Traditionnels, Cours de cuisine, etc.
   - Prix HT/TTC, TVA, disponibilité.
4. **Configuration des saisons** : `POST /api/v1/pricing/seasons` (par établissement) :
   - Saisons personnalisables : Haute saison, Basse saison, Ramadan, Fin d'année, Événements spéciaux.
5. **Configuration Channel Manager** : `POST /api/v1/channel/connections` :
   - Credentials OTA (Booking.com, Expedia, Airbnb).
   - Mapping `room_type` OTA ↔ `room_category` interne.
   - Activation 2-way sync.
6. **Configuration utilisateurs** : `POST /api/v1/auth/users` :
   - Affectation au(x) établissement(s).
   - Attribution des rôles.
   - Enregistrement biométrique (WebAuthn / Passkeys).

---

## 5. MODÈLE DE DONNÉES — TABLES CLÉS PAR SERVICE

### 5.1 `establishment-service` (PostgreSQL — Schema `establishment`)

```sql
-- Établissements (Riads)
CREATE TABLE establishments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100) DEFAULT 'Marrakech',
    country VARCHAR(100) DEFAULT 'Maroc',
    phone VARCHAR(20),
    email VARCHAR(255),
    total_rooms INT NOT NULL CHECK (total_rooms > 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chambres (configurables par établissement)
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    numero VARCHAR(10) NOT NULL,
    categorie VARCHAR(50) NOT NULL,
    floor INT NOT NULL,
    capacity_adults INT NOT NULL DEFAULT 2,
    capacity_children INT DEFAULT 0,
    description TEXT,
    amenities JSONB DEFAULT '[]',
    photos JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(establishment_id, numero)
);

CREATE INDEX idx_rooms_establishment ON rooms(establishment_id) WHERE is_active = TRUE;
CREATE INDEX idx_rooms_categorie ON rooms(establishment_id, categorie);

-- Services additionnels spécifiques aux Riads
CREATE TABLE establishment_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    code VARCHAR(20) NOT NULL,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    prix_ht DECIMAL(12,2) NOT NULL,
    tva_rate DECIMAL(5,2) NOT NULL DEFAULT 20.00,
    prix_ttc DECIMAL(12,2) NOT NULL,
    category VARCHAR(30) NOT NULL CHECK (category IN (
        'Hammam', 'Transfert', 'Excursion', 'Diner', 'Cours_Cuisine', 'Autre'
    )),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_services_establishment ON establishment_services(establishment_id) WHERE is_active = TRUE;

-- Mapping OTA ↔ Établissement
CREATE TABLE ota_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    ota_name VARCHAR(50) NOT NULL CHECK (ota_name IN ('booking_com', 'expedia', 'airbnb', 'direct_website')),
    ota_property_id VARCHAR(100) NOT NULL,
    ota_room_type_id VARCHAR(100),
    internal_room_category VARCHAR(50),
    credentials_encrypted TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(establishment_id, ota_name, ota_room_type_id)
);
```

### 5.2 `reservation-service` (PostgreSQL — Schema `reserv`)

```sql
-- Table principale des réservations
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    room_id UUID NOT NULL,
    market_segment_id UUID NOT NULL REFERENCES market_segments(id),
    status VARCHAR(20) NOT NULL CHECK (status IN (
        'status_option', 'status_confirmed', 'status_voucher',
        'status_checked_in', 'status_checked_out', 'status_no_show', 'status_cancelled'
    )),
    option_expiry_date TIMESTAMPTZ,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    regime VARCHAR(5) NOT NULL CHECK (regime IN ('BB', 'DP', 'PC')),
    partner_id UUID,
    taxes_payment_mode VARCHAR(20) NOT NULL CHECK (taxes_payment_mode IN ('at_booking', 'on_site')),
    total_amount DECIMAL(12,2),
    deposit_amount DECIMAL(12,2) DEFAULT 0,
    adults INT NOT NULL CHECK (adults > 0),
    children INT DEFAULT 0 CHECK (children >= 0),
    notes TEXT,
    source VARCHAR(30) NOT NULL DEFAULT 'walk_in' CHECK (source IN (
        'walk_in', 'phone', 'email', 'website', 'ota_booking', 'ota_expedia', 'ota_airbnb', 'b2b_agency'
    )),
    ota_reference VARCHAR(100),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT chk_dates CHECK (check_out_date > check_in_date),
    CONSTRAINT chk_option_date CHECK (
        status != 'status_option' OR option_expiry_date IS NOT NULL
    )
);

CREATE INDEX idx_bookings_establishment ON bookings(establishment_id);
CREATE INDEX idx_bookings_dates ON bookings(check_in_date, check_out_date);
CREATE INDEX idx_bookings_room ON bookings(room_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_bookings_status ON bookings(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_bookings_customer ON bookings(customer_id);
CREATE INDEX idx_bookings_segment ON bookings(market_segment_id);
CREATE INDEX idx_bookings_created_at ON bookings(created_at);
CREATE INDEX idx_bookings_ota ON bookings(ota_reference) WHERE ota_reference IS NOT NULL;

-- Segments de marché
CREATE TABLE market_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    code VARCHAR(30) NOT NULL,
    label VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL CHECK (category IN ('DIRECT', 'OTA', 'PARTENAIRES')),
    color VARCHAR(7) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(establishment_id, code)
);

-- Fiches clients (CRM)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    id_number VARCHAR(50),
    nationality VARCHAR(3),
    date_of_birth DATE,
    historical_notes JSONB DEFAULT '{}',
    is_vip BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}',
    consent_marketing BOOLEAN DEFAULT FALSE,
    anonymized_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customers_establishment ON customers(establishment_id);
CREATE INDEX idx_customers_name ON customers(last_name, first_name);
CREATE INDEX idx_customers_email ON customers(email) WHERE anonymized_at IS NULL;
CREATE INDEX idx_customers_search ON customers USING gin(
    to_tsvector('french', coalesce(first_name,'') || ' ' || coalesce(last_name,'') || ' ' || coalesce(email,''))
);

-- Historique des statuts
CREATE TABLE booking_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id),
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by UUID NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    reason TEXT,
    ip_address INET,
    correlation_id UUID
);

CREATE INDEX idx_status_history_booking ON booking_status_history(booking_id, changed_at DESC);

-- Journal d'audit général
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    performed_by UUID NOT NULL,
    performed_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    correlation_id UUID
);

CREATE INDEX idx_audit_log_establishment ON audit_log(establishment_id);
CREATE INDEX idx_audit_log_table ON audit_log(table_name, record_id, performed_at DESC);
CREATE INDEX idx_audit_log_correlation ON audit_log(correlation_id);
```

### 5.3 `front-office-service` (PostgreSQL — Schema `frontoffice`)

```sql
CREATE TABLE folios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    booking_id UUID NOT NULL,
    type VARCHAR(1) NOT NULL CHECK (type IN ('A', 'B')),
    status VARCHAR(10) NOT NULL CHECK (status IN ('open', 'closed')) DEFAULT 'open',
    third_party_ref UUID,
    total_charges DECIMAL(12,2) DEFAULT 0,
    total_payments DECIMAL(12,2) DEFAULT 0,
    balance DECIMAL(12,2) GENERATED ALWAYS AS (total_charges - total_payments) STORED,
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    closed_by UUID,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    business_date DATE NOT NULL
);

CREATE INDEX idx_folios_establishment ON folios(establishment_id);
CREATE INDEX idx_folios_booking ON folios(booking_id);
CREATE INDEX idx_folios_status ON folios(status) WHERE status = 'open';
CREATE INDEX idx_folios_business_date ON folios(business_date);

CREATE TABLE folio_charges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    folio_id UUID NOT NULL REFERENCES folios(id),
    poste_comptable VARCHAR(10) NOT NULL CHECK (poste_comptable IN (
        'HEB', 'PDJ', 'RES', 'BAR', 'SPA', 'ACT', 'TS', 'TPT', 'REM',
        'HAM', 'TRF', 'DIN', 'EXC'
    )),
    libelle VARCHAR(255) NOT NULL,
    quantity INT DEFAULT 1 CHECK (quantity > 0),
    unit_price_ht DECIMAL(12,2) NOT NULL,
    montant_ht DECIMAL(12,2) NOT NULL,
    tva_rate DECIMAL(5,2) NOT NULL CHECK (tva_rate IN (0, 10, 20)),
    tva_amount DECIMAL(12,2) NOT NULL,
    montant_ttc DECIMAL(12,2) NOT NULL,
    visible_on_print BOOLEAN DEFAULT TRUE,
    source_service VARCHAR(50),
    catalog_item_id UUID,
    correction_of UUID REFERENCES folio_charges(id),
    corrects_date DATE,
    correction_reason TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    business_date DATE NOT NULL
);

CREATE INDEX idx_charges_folio ON folio_charges(folio_id);
CREATE INDEX idx_charges_poste ON folio_charges(poste_comptable, business_date);
CREATE INDEX idx_charges_business_date ON folio_charges(business_date);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    folio_id UUID NOT NULL REFERENCES folios(id),
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('CB', 'ESP', 'CHQ', 'Virement', 'Débiteur')),
    montant DECIMAL(12,2) NOT NULL CHECK (montant > 0),
    reference VARCHAR(100),
    encaisse_par UUID NOT NULL,
    encaisse_at TIMESTAMPTZ DEFAULT NOW(),
    business_date DATE NOT NULL
);

CREATE INDEX idx_payments_folio ON payments(folio_id);
CREATE INDEX idx_payments_mode ON payments(mode, business_date);
CREATE INDEX idx_payments_business_date ON payments(business_date);

CREATE TABLE business_date_locks (
    establishment_id UUID NOT NULL,
    business_date DATE NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE,
    locked_at TIMESTAMPTZ,
    locked_by UUID,
    audit_run_id UUID,
    PRIMARY KEY (establishment_id, business_date)
);
```

### 5.4 `housekeeping-service` (PostgreSQL — Schema `housekeeping`)

```sql
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    numero VARCHAR(10) NOT NULL,
    categorie VARCHAR(50) NOT NULL,
    floor INT NOT NULL,
    statut VARCHAR(20) NOT NULL CHECK (statut IN (
        'Sale', 'Nettoyage', 'Propre', 'Contrôlée', 'Bloquée'
    )) DEFAULT 'Propre',
    motif_blocage VARCHAR(20) CHECK (motif_blocage IN (
        'Day Use', 'Panne', 'Départ tardif', 'Travaux'
    )),
    blocked_reason TEXT,
    blocked_by UUID,
    blocked_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(establishment_id, numero)
);

CREATE INDEX idx_rooms_establishment ON rooms(establishment_id);
CREATE INDEX idx_rooms_statut ON rooms(statut) WHERE is_active = TRUE;
CREATE INDEX idx_rooms_categorie ON rooms(establishment_id, categorie);

CREATE TABLE room_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id),
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by UUID NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    reason TEXT
);

CREATE INDEX idx_room_status_history ON room_status_history(room_id, changed_at DESC);

CREATE TABLE room_planning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    room_id UUID NOT NULL REFERENCES rooms(id),
    booking_id UUID NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    UNIQUE(establishment_id, room_id, date)
);

CREATE INDEX idx_planning_establishment ON room_planning(establishment_id);
CREATE INDEX idx_planning_date ON room_planning(date);
CREATE INDEX idx_planning_room ON room_planning(room_id);

-- Incidents housekeeping
CREATE TABLE room_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    room_id UUID NOT NULL REFERENCES rooms(id),
    incident_type VARCHAR(30) NOT NULL CHECK (incident_type IN (
        'Panne technique', 'Manque de linge', 'Problème sanitaire', 'Autre'
    )),
    description TEXT,
    photo_url VARCHAR(500),
    reported_by UUID NOT NULL,
    reported_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID
);

CREATE INDEX idx_incidents_establishment ON room_incidents(establishment_id);
CREATE INDEX idx_incidents_room ON room_incidents(room_id);
```

### 5.5 `pricing-service` (PostgreSQL — Schema `pricing`)

```sql
CREATE TABLE seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    label VARCHAR(100) NOT NULL,
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT chk_season_dates CHECK (date_fin > date_debut)
);

CREATE INDEX idx_seasons_establishment ON seasons(establishment_id);

CREATE TABLE rate_grid (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    room_category VARCHAR(50) NOT NULL,
    season_id UUID NOT NULL REFERENCES seasons(id),
    regime VARCHAR(5) NOT NULL CHECK (regime IN ('BB', 'DP', 'PC')),
    prix_ttc DECIMAL(12,2) NOT NULL CHECK (prix_ttc > 0),
    prix_ht DECIMAL(12,2) NOT NULL,
    tva_rate DECIMAL(5,2) NOT NULL DEFAULT 10.00,
    UNIQUE(establishment_id, room_category, season_id, regime)
);

CREATE INDEX idx_rate_grid_lookup ON rate_grid(establishment_id, room_category, season_id, regime);

CREATE TABLE taxes_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN (
        'TVA_HEBERGEMENT', 'TVA_AUTRE', 'TS', 'TPT'
    )),
    taux_ou_montant DECIMAL(12,4) NOT NULL,
    mode_calcul VARCHAR(20) NOT NULL CHECK (mode_calcul IN ('PERCENTAGE', 'FIXED_PER_PAX')),
    applicable_from DATE NOT NULL DEFAULT '2024-01-01',
    applicable_to DATE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE extras_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    categorie VARCHAR(20) NOT NULL CHECK (categorie IN (
        'Restaurant', 'Bar', 'SPA', 'Activités', 'Autre'
    )),
    libelle VARCHAR(255) NOT NULL,
    description TEXT,
    prix_ht DECIMAL(12,2) NOT NULL,
    tva_rate DECIMAL(5,2) NOT NULL DEFAULT 20.00,
    prix_ttc DECIMAL(12,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_extras_establishment ON extras_catalog(establishment_id);

CREATE TABLE partner_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    partner_id UUID NOT NULL,
    season_id UUID NOT NULL REFERENCES seasons(id),
    room_category VARCHAR(50) NOT NULL,
    regime VARCHAR(5) NOT NULL,
    tarif_negocie DECIMAL(12,2) NOT NULL,
    commission_pct DECIMAL(5,2) DEFAULT 0,
    UNIQUE(establishment_id, partner_id, season_id, room_category, regime)
);

CREATE TABLE packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    prix_global_ttc DECIMAL(12,2) NOT NULL,
    ventilation JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_to DATE
);
```

### 5.6 `night-audit-service` (PostgreSQL — Schema `audit`)

```sql
CREATE TABLE audit_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    business_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'balancing', 'balanced', 'error', 'closed')),
    total_debits DECIMAL(14,2),
    total_credits DECIMAL(14,2),
    discrepancy DECIMAL(14,2),
    closed_by UUID,
    closed_at TIMESTAMPTZ,
    report_urls JSONB,
    report_hash VARCHAR(64),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    UNIQUE(establishment_id, business_date)
);

CREATE INDEX idx_audit_runs_establishment ON audit_runs(establishment_id, business_date DESC);

CREATE TABLE system_state (
    establishment_id UUID PRIMARY KEY REFERENCES establishments(id),
    business_date DATE NOT NULL,
    last_audit_run_id UUID REFERENCES audit_runs(id),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL,
    business_date DATE NOT NULL,
    service_name VARCHAR(50) NOT NULL,
    snapshot_data JSONB NOT NULL,
    snapshot_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(establishment_id, business_date, service_name)
);
```

### 5.7 `analytics-service` (PostgreSQL — Schema `analytics`)

```sql
CREATE TABLE daily_kpi_snapshot (
    business_date DATE NOT NULL,
    establishment_id UUID NOT NULL,
    segment_id UUID,
    nuitees INT DEFAULT 0,
    ca_brut DECIMAL(14,2) DEFAULT 0,
    ca_ht DECIMAL(14,2) DEFAULT 0,
    tva_total DECIMAL(14,2) DEFAULT 0,
    to_pct DECIMAL(5,2) DEFAULT 0,
    adr DECIMAL(12,2) DEFAULT 0,
    revpar DECIMAL(12,2) DEFAULT 0,
    dms DECIMAL(5,2) DEFAULT 0,
    pax_total INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (business_date, establishment_id, segment_id)
);

CREATE INDEX idx_kpi_establishment ON daily_kpi_snapshot(establishment_id, business_date DESC);

CREATE TABLE monthly_kpi_aggregation (
    year INT NOT NULL,
    month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
    establishment_id UUID NOT NULL,
    segment_id UUID,
    nuitees INT DEFAULT 0,
    ca_brut DECIMAL(14,2) DEFAULT 0,
    to_pct DECIMAL(5,2) DEFAULT 0,
    adr DECIMAL(12,2) DEFAULT 0,
    revpar DECIMAL(12,2) DEFAULT 0,
    dms DECIMAL(5,2) DEFAULT 0,
    PRIMARY KEY (year, month, establishment_id, segment_id)
);

CREATE TABLE channel_performance (
    business_date DATE NOT NULL,
    establishment_id UUID NOT NULL,
    channel VARCHAR(50) NOT NULL,
    bookings_count INT DEFAULT 0,
    revenue DECIMAL(14,2) DEFAULT 0,
    commission DECIMAL(14,2) DEFAULT 0,
    net_revenue DECIMAL(14,2) DEFAULT 0,
    PRIMARY KEY (business_date, establishment_id, channel)
);

CREATE VIEW kpi_ytd_comparison AS
SELECT 
    current.year,
    current.establishment_id,
    current.segment_id,
    current.ca_brut AS current_ca,
    previous.ca_brut AS previous_ca,
    ROUND(((current.ca_brut - previous.ca_brut) / NULLIF(previous.ca_brut, 0)) * 100, 2) AS ca_delta_pct
FROM monthly_kpi_aggregation current
LEFT JOIN monthly_kpi_aggregation previous 
    ON previous.year = current.year - 1 
    AND previous.month = current.month 
    AND previous.establishment_id = current.establishment_id
    AND previous.segment_id = current.segment_id;
```

### 5.8 `partner-service` (PostgreSQL — Schema `partner`)

```sql
CREATE TABLE partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('AGENCE', 'TO', 'CORPORATE', 'OTA')),
    nom VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    ice VARCHAR(15),
    rc VARCHAR(50),
    address TEXT,
    payment_terms INT DEFAULT 30,
    ota_credentials_encrypted TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_partners_establishment ON partners(establishment_id);
CREATE INDEX idx_partners_type ON partners(type);
CREATE INDEX idx_partners_active ON partners(nom) WHERE is_active = TRUE;
```


---

## 6. EXIGENCES NON-FONCTIONNELLES (Détaillées)

### 6.1 Cohérence Transactionnelle Inter-Services

- **Pattern** : Saga chorégraphiée (événements RabbitMQ) pour tout ce qui touche au Night Audit et au Check-in/out.
- **Pas de 2PC** : Pas de transaction distribuée classique (trop lente, trop complexe).
- **Compensation** : Chaque service implémente des endpoints de compensation (`/compensate/{action}`) appelés en cas d'échec d'une étape saga.
- **Idempotence** : Tous les endpoints d'écriture critiques acceptent un header `X-Idempotency-Key: {uuid}`. Clé stockée en Redis 24h (`idempotency:{key}` → `response_body`).

### 6.2 Verrouillage Concurrentiel

- **Redis SETNX** : Verrou distribué pour les réservations de chambres.
- **TTL** : 30 secondes (renouvelable si la transaction est longue).
- **Deadlock prevention** : Si le verrou expire pendant une transaction, la transaction est annulée (`ROLLBACK`) et le client reçoit `409 LOCK_EXPIRED`.
- **Optimistic Locking** : Sur les folios (`version` column) pour éviter les modifications concurrentes.

### 6.3 Immutabilité Comptable

- Après Night Audit (date J close), toute correction sur une date J close passe par une **écriture de régularisation datée du jour courant**.
- **Jamais** de modification rétroactive.
- Table `folio_charges` : champ `correction_of` pour lier l'écriture de régularisation à l'original.

### 6.4 Temps Réel

- **WebSocket** : Canal `/ws/rooms` pour les statuts de chambres, `/ws/planning` pour le planning réservations.
- **Redis pub/sub** : `room.status_changed`, `booking.created`, `booking.updated` publiés sur Redis, consommés par le serveur WebSocket et relayés aux clients.
- **Pas de polling** : Le frontend ne fait jamais de polling pour les données temps réel.

### 6.5 Résilience

| Service défaillant | Mode dégradé |
|---|---|
| `pricing-service` down | `reservation-service` crée réservation en `status_option` sans tarif calculé. Tarif à compléter plus tard. |
| `housekeeping-service` down | `front-office-service` permet le check-in avec warning ("Statut chambre non vérifié"). Manager doit valider. |
| `notification-service` down | Les événements sont stockés dans une file d'attente RabbitMQ DLQ. Retry automatique toutes les 5 min × 10. |
| `analytics-service` down | Les événements sont bufferisés dans Redis. Replay automatique au redémarrage. |
| `partner-service` down | Réservation B2B bloquée (partner_id obligatoire). Fallback : création réservation directe avec note manuelle. |
| `channel-manager-service` down | Réservations OTA bufferisées. Retry automatique. Saisie manuelle possible en fallback. |

### 6.6 Performance

| Métrique | Objectif | Stratégie |
|---|---|---|
| Temps de réponse API (p95) | < 200ms | Cache Redis, index optimisés, connexion pooling |
| Temps de chargement planning | < 1s (50 chambres × 30 jours) | Vue matérialisée `room_planning`, pagination |
| Night Audit 50 chambres | < 2 minutes | Requêtes parallèles, pas de transactions longues |
| WebSocket propagation | < 500ms | Redis pub/sub, pas de persistance intermédiaire |
| Export PDF rapport audit | < 30s | Génération asynchrone (Celery), notification par email |
| Sync OTA (webhook → réservation) | < 30s | Queue asynchrone, traitement parallèle |

### 6.7 Observabilité

```yaml
Traces (OpenTelemetry):
  - Nom de la trace: {correlation_id}
  - Spans par service: {service_name}/{endpoint}
  - Attributs obligatoires: user_id, establishment_id, business_date, hotel_id

Métriques (Prometheus):
  - pms_api_requests_total{service, endpoint, status}
  - pms_api_duration_seconds{service, endpoint, quantile}
  - pms_bookings_created_total{segment}
  - pms_night_audit_duration_seconds
  - pms_redis_lock_wait_seconds
  - pms_channel_sync_latency_seconds

Logs (ELK):
  - Format: JSON structuré
  - Champs obligatoires: timestamp, level, service, correlation_id, user_id, establishment_id, message, context
  - Niveaux: DEBUG (dev), INFO (prod), WARN, ERROR, FATAL
  - Rétention: 30 jours (hot), 1 an (warm), 3 ans (cold)

Alertes (Grafana):
  - ERROR rate > 1% pendant 5 min → PagerDuty
  - Night Audit échec 3 jours consécutifs → Email direction
  - Redis indisponible > 30s → Slack #ops
  - PostgreSQL connections > 80% → Auto-scale (si cloud)
  - Channel Manager sync échec > 5 min → Alert admin
```

---

## 7. STRATÉGIE DE TEST

### 7.1 Tests Unitaires

- **Couverture minimale** : 80% du code métier (`app/domain/`).
- **Framework** : `pytest` (Python), `Jest` (Next.js).
- **Mocking** : `unittest.mock` pour les dépendances externes, `fakeredis` pour les tests Redis.

### 7.2 Tests d'Intégration (Obligatoires)

| Workflow | Scénarios testés | Services impliqués |
|---|---|---|
| **A** — Réservation Walk-in | Double réservation concurrente, expiration option, client existant/inconnu | reservation, pricing, Redis, RabbitMQ |
| **C** — Check-in | Chambre sale refusée, création Folio A+B, verrou pro-forma | front-office, housekeeping, reservation |
| **F** — Check-out | Solde nul, solde positif (multi-paiements), Folio B débiteur, tentative réouverture | front-office, reservation, housekeeping |
| **H** — Night Audit | Équilibre OK, écart détecté, clôture J, bascule J+1, tentative modification J | night-audit, front-office, reservation, analytics |
| **E** — Room Shifting | Même catégorie, upsell manager, conflit chambre | reservation, pricing, housekeeping |
| **C (OTA)** — Réservation OTA | Webhook reçu, mapping OK/KO, sync inverse, conflit inventaire | channel-manager, reservation, pricing, housekeeping |

### 7.3 Tests E2E (Playwright)

- Scénario 1 : Réceptionniste crée réservation → check-in → ajoute extra → check-out.
- Scénario 2 : Manager lance Night Audit → vérifie rapports → bascule J+1.
- Scénario 3 : Gouvernante met à jour statuts chambres → vérification temps réel planning.
- Scénario 4 : Room shifting drag & drop → vérification changement chambre + tarif.
- Scénario 5 : Réservation OTA auto-importée → vérification planning + inventaire.

### 7.4 Tests de Charge

- **Outil** : `k6` ou `Locust`.
- **Scénarios** :
  - 15 réceptionnistes créant 30 réservations/minute simultanément.
  - Night Audit sur 50 chambres avec 200 folios actifs.
  - Planning WebSocket : 30 clients connectés, mises à jour toutes les 2 secondes.
  - Webhooks OTA : 50 webhooks/minute simultanés.

### 7.5 Tests de Sécurité

- **OWASP ZAP** : Scan automatique des APIs.
- **Tests JWT** : Token expiré, token falsifié, scope insuffisant.
- **Tests RBAC** : Réceptionniste tentant action admin → `403`.
- **Tests idempotence** : Retry de check-in avec même clé → même réponse, pas de double folio.
- **Tests biométrie** : WebAuthn bypass, fallback password, session mobile.
- **Tests multi-tenant** : Accès croisé établissements → `403`.

---

## 8. LIVRABLES ATTENDUS

### 8.1 Infrastructure

1. **`docker-compose.yml`** orchestrant :
   - Keycloak (avec realm pré-configuré `amh-hospitality`)
   - PostgreSQL (instance unique, multi-databases : `auth_db`, `establishment_db`, `reserv_db`, `fo_db`, `hk_db`, `pricing_db`, `audit_db`, `analytics_db`, `notif_db`, `partner_db`, `channel_db`)
   - RabbitMQ (avec exchanges et queues pré-déclarées)
   - Redis (cache + pub/sub + Celery broker)
   - Kong (configuration declarative via `kong.yml`)
   - MinIO (stockage S3-compatible pour les rapports)
   - Les 11 microservices FastAPI
   - Le frontend Next.js
   - L'application mobile Housekeeping (PWA/React Native)
   - ELK stack (Elasticsearch, Logstash, Kibana)
   - Prometheus + Grafana

2. **`docker-compose.prod.yml`** avec :
   - Réplicas des services critiques (reservation, front-office, channel-manager)
   - Health checks et restart policies
   - Réseaux isolés (frontend, backend, database, monitoring)

### 8.2 Par Microservice

Structure standard obligatoire :

```
services/{service-name}/
├── app/
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration (Pydantic Settings)
│   ├── dependencies.py      # Dépendances injectables (DB, Redis, JWT)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints.py # Routes FastAPI
│   │   │   └── schemas.py   # Pydantic models (request/response)
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py        # Modèles SQLAlchemy
│   │   ├── services.py      # Logique métier pure
│   │   └── exceptions.py    # Exceptions métier custom
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py      # Connexion PostgreSQL + session
│   │   ├── redis_client.py  # Connexion Redis
│   │   ├── rabbitmq.py      # Publisher/Consumer events
│   │   └── keycloak.py      # Client Keycloak
│   ├── events/
│   │   ├── __init__.py
│   │   ├── publisher.py     # Publie sur RabbitMQ
│   │   ├── consumer.py      # Consomme depuis RabbitMQ
│   │   └── handlers.py      # Handlers d'événements
│   └── tests/
│       ├── __init__.py
│       ├── test_unit.py
│       ├── test_integration.py
│       └── conftest.py
├── alembic/                 # Migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

### 8.3 Documentation

1. **OpenAPI agrégé** : Kong expose une documentation unifiée (`/docs`) agrégeant les schémas OpenAPI de chaque service.
2. **Diagrammes de séquence** : Un diagramme Mermaid pour chaque workflow (A–K).
3. **Runbook ops** : Procédures de dépannage pour chaque alerte Grafana.
4. **Guide de déploiement** : `DEPLOYMENT.md` avec commandes step-by-step.
5. **Guide Channel Manager** : `CHANNEL_MANAGER.md` avec procédures de mapping OTA et troubleshooting.
6. **Guide Mobile** : `MOBILE.md` avec procédures de build et déploiement PWA/React Native.

---

## 9. PRIORISATION DU DÉVELOPPEMENT

| Sprint | Services | Objectif |
|---|---|---|
| Sprint 1 | `auth-gateway-service`, `establishment-service`, `housekeeping-service` | Fondation sécurité + multi-tenant + gestion chambres |
| Sprint 2 | `pricing-service`, `partner-service`, `channel-manager-service` | Tarification + partenaires + intégration OTA |
| Sprint 3 | `reservation-service` | Cœur métier réservations (manuel + OTA) |
| Sprint 4 | `front-office-service`, `analytics-service` (parallèle) | Check-in/out + dashboards |
| Sprint 5 | `night-audit-service`, `notification-service` | Clôture comptable + alertes |
| Sprint 6 | Frontend Next.js (intégration) + Mobile Housekeeping | UI complète avec mocks remplacés |
| Sprint 7 | Tests E2E, charge, sécurité | Validation bout-en-bout |
| Sprint 8 | Optimisation, documentation, handover | Production-ready |

---

## 10. APPENDICES

### Appendix A — Glossaire

| Terme | Définition |
|---|---|
| **PMS** | Property Management System — logiciel de gestion hôtelière |
| **T.O.** | Taux d'Occupation — % de chambres occupées |
| **ADR** | Average Daily Rate — prix moyen par chambre louée |
| **RevPAR** | Revenue Per Available Room — revenu par chambre disponible |
| **DMS** | Durée Moyenne de Séjour — moyenne de nuitées par réservation |
| **Folio** | Compte client (A = client direct, B = tiers/agence) |
| **Night Audit** | Clôture comptable journalière irréversible |
| **Saga** | Pattern de gestion de transactions distribuées |
| **DLQ** | Dead Letter Queue — file de messages en échec |
| **OTA** | Online Travel Agency — agence de voyage en ligne (Booking.com, Expedia, etc.) |
| **2-way sync** | Synchronisation bidirectionnelle des inventaires et tarifs |
| **WebAuthn** | Standard web pour authentification sans mot de passe (FIDO2) |
| **Passkeys** | Implémentation moderne de WebAuthn par les grands éditeurs |
| **RLS** | Row-Level Security — sécurité au niveau des lignes PostgreSQL |
| **Upsell** | Vente d'une catégorie de chambre supérieure |
| **Room Shifting** | Changement de chambre d'une réservation existante |

### Appendix B — Codes HTTP Spécifiques au Métier

| Code | Usage |
|---|---|
| `409 ROOM_UNAVAILABLE` | Chambre déjà réservée ou verrou active |
| `409 PRECONDITION_FAILED` | Chambre non prête pour check-in |
| `409 REQUIRES_VALIDATION` | Upsell nécessite validation manager |
| `409 ROOM_CONFLICT` | Chambre cible occupée |
| `409 ROOM_BLOCKED` | Chambre cible bloquée |
| `409 INVALID_TRANSITION` | Transition state machine interdite |
| `409 OTA_CONFLICT` | Conflit d'inventaire détecté lors sync OTA |
| `410 GONE` | Facture pro-forma plus disponible après check-in |
| `423 LOCKED` | Date métier verrouillée par Night Audit |
| `423 ROOM_SHIFT_IN_PROGRESS` | Room shifting en cours sur cette chambre |
| `429 TOO_MANY_REQUESTS` | Rate limiting Kong |

### Appendix C — Event Catalog (RabbitMQ)

| Event | Publisher | Consumers | Payload |
|---|---|---|---|
| `booking.created` | reservation-service | analytics, housekeeping, notification, channel-manager | {booking_id, room_id, dates, segment, establishment_id} |
| `booking.checked_in` | front-office-service | housekeeping, analytics, notification | {booking_id, room_id, folio_ids, establishment_id} |
| `booking.checked_out` | front-office-service | housekeeping, analytics, notification, channel-manager | {booking_id, room_id, final_balance, establishment_id} |
| `booking.cancelled` | reservation-service | housekeeping, analytics, notification, channel-manager | {booking_id, reason, establishment_id} |
| `booking.room_changed` | reservation-service | housekeeping, analytics, channel-manager | {booking_id, old_room, new_room, establishment_id} |
| `folio.charge_added` | front-office-service | analytics | {folio_id, amount, poste, establishment_id} |
| `room.status_changed` | housekeeping-service | frontend (WebSocket), reservation-service | {room_id, old_status, new_status, establishment_id} |
| `room.incident_reported` | housekeeping-service | notification, frontend | {room_id, incident_type, establishment_id} |
| `audit.closed` | night-audit-service | ALL services | {business_date, report_hash, establishment_id} |
| `channel.booking_received` | channel-manager-service | reservation-service, analytics | {ota_reference, booking_id, establishment_id} |
| `channel.sync_failed` | channel-manager-service | notification, analytics | {ota_name, error, establishment_id} |

### Appendix D — Schéma de Communication Inter-Services

```
+-------------+     REST      +-------------+
|   Next.js   |◄─────────────▶│    Kong     │
|  Frontend   │   WebSocket   │   Gateway   │
+-------------+◄─────────────▶+------+------+
                                     │
              +----------------------+----------------------+
              │                      │                      │
              v REST sync            v REST sync            v Events async
        +----------+          +----------+          +--------------+
        |reservation|         | front-   │          │   RabbitMQ   │
        │-service   │◄───────▶│ office   │          │   Exchange   │
        +-----+-----+          +----+-----+          +------+-------+
              │                     │                       │
              │                     │                       │
              v REST                v REST                  v pub/sub
        +----------+          +----------+           +----------+
        │ pricing  │          │housekeep.│           │analytics │
        │-service  │          │-service  │           │-service  │
        +----------+          +----------+           +----------+
        +----------+
        │ channel  │
        │-manager  │
        +----------+
```

### Appendix E — Rôles & Interfaces Matricielles

| Rôle | Interface | Appareil | Auth | Permissions clés |
|---|---|---|---|---|
| Femme de chambre | Vue carte chambres | Mobile/Tablette | Biométrie native | MAJ statut, incidents, réassort |
| Gouvernante | Dashboard chambres + planning ménage | Mobile/Tablette | Biométrie native | Tous statuts, supervision, rapports |
| Réceptionniste | Planning + Dashboard + Facturation | Desktop Web | WebAuthn/Passkeys | CRUD réservations, check-in/out, encaissement |
| Manager | Accès complet (sauf users) | Desktop Web | WebAuthn/Passkeys (AAL2) | Validation upsell, Night Audit, dashboards, Channel Manager |
| Admin | Accès total | Desktop Web | WebAuthn/Passkeys (AAL2) | Config établissement, tarifs, utilisateurs |
| Comptable | Vue comptable | Desktop Web | Password + OTP | Journaux, encaissements, exports |

### Appendix F — Services Spécifiques Riads

| Service | Catégorie | TVA | Poste Comptable | Description |
|---|---|---|---|---|
| Hammam | Bien-être | 20% | `HAM` | Accès hammam traditionnel |
| Transfert Aéroport | Transport | 20% | `TRF` | Navette aéroport-Riad |
| Excursion | Activité | 20% | `EXC` | Visites guidées Marrakech |
| Dîner Traditionnel | Restauration | 10% | `DIN` | Dîner marocain sur place |
| Cours de Cuisine | Activité | 20% | `EXC` | Atelier cuisine marocaine |
| Petit-déjeuner | Restauration | 10% | `PDJ` | Petit-déjeuner inclus/forfait |

---

*Document généré le 22 Juillet 2026 — Version 3.0-Enhanced*  
*PMS AMH Hospitality — Spécifications techniques complètes avec intégration Channel Manager, authentification biométrique, multi-tenant Riads, et room shifting drag & drop*
