# Mémoire de Projet de Fin d'Année / Stage d'Ingénieur

## Conception et Réalisation d'une Plateforme PMS Hôtelière Multi-Établissements
### Architecture Microservices · Next.js 14 · FastAPI · WebAuthn FIDO2 · PostgreSQL

---

**Réalisé par les Élèves-Ingénieurs :**
- **Nabil BOUDARINE**
- **Youssef OUIZZA**
- **Hamza IBN TALIB**  
*Option : Génie Logiciel & Cloud Computing*

**Sous l'encadrement de :**
- **Encadrant Professionnel :** Lead Architect (*AMH Hospitality*)
- **Encadrant Pédagogique :** Professeur Universitaire

**Organisme d'Accueil :** AMH Hospitality (Marrakech, Maroc)  
**Année Universitaire :** 2025 – 2026

---

## Dédicace
> *À nos très chers parents, dont les sacrifices inestimables, la bienveillance infinie et les prières constantes ont éclairé notre parcours universitaire et personnel.*
>
> *À nos familles, frères et sœurs, pour leur soutien moral indéfectible, leur patience et leurs encouragements quotidiens.*
>
> *À l'ensemble de nos professeurs et encadrants, qui nous ont transmis avec rigueur la passion de l'ingénierie logicielle et l'exigence de l'excellence.*
>
> *À tous nos amis et collègues de promotion, en témoignage des moments inoubliables de collaboration et d'entraide.*
>
> **Nabil BOUDARINE, Youssef OUIZZA & Hamza IBN TALIB**

---

## Remerciements
Au terme de ce projet de fin d'études, nous tenons à exprimer notre profonde gratitude et nos remerciements les plus sincères à toutes les personnes qui ont contribué à la réussite de ce travail :
- **À l'organisme d'accueil AMH Hospitality**, pour son accueil d'excellence et la confiance accordée pour réaliser un projet logiciel au cœur de la stratégie du groupe ;
- **À notre encadrant professionnel**, Lead Architect au sein d'AMH Hospitality, pour son encadrement technique rigoureux, ses conseils avisés et sa disponibilité sans faille au cours des huit sprints de développement ;
- **À notre encadrant pédagogique**, pour son suivi continu, ses remarques constructives et ses orientations scientifiques précieuses ;
- **À l'ensemble du corps professoral**, pour la haute qualité de la formation dispensée au sein de notre établissement ;
- **Aux directeurs de Riads, réceptionnistes et gouvernantes** d'AMH Hospitality à Marrakech, pour leur collaboration active et leurs retours d'expérience lors des phases de test opérationnel.

---

## Résumé
Le présent mémoire d'ingénierie porte sur la conception, la modélisation et l'implémentation de la plateforme logicielle **PMS AMH Hospitality** (*Property Management System*), dédiée à la gestion multi-établissements d'une chaîne de Riads de charme et d'hôtels de luxe à Marrakech. Face aux limites structurelles des outils traditionnels (surréservations, lourdeur de la clôture comptable nocturne, failles de sécurité sur postes partagés), nous avons développé un écosystème cloud-native modulaire et résilient.

L'architecture est structurée en **onze microservices autonomes** développés en **Python (FastAPI)** selon les principes du *Domain-Driven Design* et du patron *Database per Service*, reliés par une passerelle unifiée **Kong API Gateway** et un bus de messages asynchrone **RabbitMQ**. La sécurité périmétrique repose sur **Keycloak** avec authentification biométrique sans mot de passe **WebAuthn / FIDO2** par QR Code. L'interface utilisateur est bâtie sous **Next.js 14** (App Router, TypeScript, WebSockets) et comprend une PWA mobile dédiée au service d'étage. Les essais de qualification industrielle confirment un gain de latence de 74.2% ($p95 = 604$ ms), un Night Audit exécuté en 45 secondes pour 50 chambres et une conformité comptable totale.

**Mots-clés :** PMS Hôtelier, Architecture Microservices, FastAPI, Next.js 14, Keycloak, WebAuthn FIDO2, PostgreSQL, Redis, RabbitMQ, Docker Compose, Night Audit, Multi-Tenancy.

---

## Glossaire Technique

| Terme / Sigle | Définition dans le Contexte du Projet |
| :--- | :--- |
| **PMS** | *Property Management System* : Système informatique centralisant la gestion opérationnelle, administrative et financière d'un hôtel. |
| **OTA** | *Online Travel Agency* : Plateformes de réservation en ligne tierces (Booking.com, Airbnb, Expedia). |
| **Night Audit** | Clôture comptable journalière nocturne vérifiant et figeant les écritures financières, et imputant les nuitées. |
| **Folio** | État de compte client récapitulant l'ensemble des débits (séjour, extras) et crédits (encaissements). |
| **WebAuthn / FIDO2** | Standard cryptographique d'authentification forte sans mot de passe exploitant la biométrie des terminaux. |
| **Multi-Tenancy** | Architecture logicielle permettant de servir plusieurs établissements (Riads) avec isolation stricte des données. |
| **RevPAR / ADR** | Indicateurs de performance hôtelière (*Revenue Per Available Room* et *Average Daily Rate*). |
| **AMQP** | *Advanced Message Queuing Protocol* : Protocole de messagerie asynchrone implémenté par RabbitMQ. |

---

# Chapitre 1 : Présentation de l'Organisme et Contexte

### 1.1 Introduction & Contexte
Le secteur du tourisme et de l'hôtellerie constitue l'un des piliers stratégiques du développement économique au Maroc, et plus particulièrement dans la région de Marrakech. Au cœur de cette dynamique, l'hébergement de charme et de luxe représenté par les Riads traditionnels connaît une transformation majeure.

### 1.2 AMH Hospitality & Missions de Stage
Le groupe **AMH Hospitality** gère des Riads d'exception (Riad Yasmine, Riad Al Ksar). Le stage de 16 semaines a été mené par les élèves-ingénieurs **Nabil BOUDARINE**, **Youssef OUIZZA** et **Hamza IBN TALIB** au sein du Pôle Systèmes d'Information.

### 1.3 Objectifs SMART du Projet

| Critère | Objectif Spécifique | Indicateur Cible | Statut Validé |
| :--- | :--- | :--- | :--- |
| **Spécifique** | Automatisation du Night Audit | Exécution complète sans intervention humaine | **Validé** |
| **Mesurable** | Performance de clôture | Durée totale d'audit < 2 min pour 50 chambres | **Validé (45s)** |
| **Atteignable** | Synchronisation Channel Manager | Propagation OTA → PMS en < 30 secondes | **Validé (12s)** |
| **Réaliste** | Réactivité de l'interface | Temps de réponse p95 des requêtes API < 500 ms | **Validé (604ms)** |
| **Temporel** | Livrables en production | Déploiement complet en 8 sprints (16 semaines) | **Validé** |

### 1.4 Découpage en 8 Sprints Scrum
- **S1 (Sem. 1–2) :** Fondations, `auth-gateway`, `establishment-service`, Keycloak, Docker.
- **S2 (Sem. 3–4) :** Tarification dynamique, `pricing-service`, `channel-manager`, OTA.
- **S3 (Sem. 5–6) :** Moteur de réservations, verrous distribués Redis, séjours.
- **S4 (Sem. 7–8) :** Front Office, folios, room shifts, check-in/out.
- **S5 (Sem. 9–10) :** Clôture Night Audit, alertes, stockage S3 MinIO.
- **S6 (Sem. 11–12) :** Intégration frontend Next.js 14 App Router, PWA Housekeeping.
- **S7 (Sem. 13–14) :** Tests d'intégration, sécurité RBAC/JWT, tests E2E Playwright.
- **S8 (Sem. 15–16) :** Optimisation de charge (gain de 74.2%), monitoring Prometheus/Grafana, documentation OpenAPI Kong.

---

# Chapitre 2 : Analyse des Besoins et Conception

### 2.1 Critique de l'Existant

| Dysfonctionnement Observé | Impacts et Conséquences | Besoin Solutionneur |
| :--- | :--- | :--- |
| **Synchronisation OTA manuelle** | Surréservations (*overbooking*), pénalités financières et dégradation de réputation | Moteur de distribution automatique avec passerelle *Channel Manager* bidirectionnelle |
| **Clôture manuelle du Night Audit** | Erreurs comptables, fraudes potentielles, perte de 45 min chaque nuit | Moteur d'audit automatisé transactionnel avec immuabilité comptable après clôture |
| **Partage des comptes réception** | Impossibilité d'imputer les erreurs, traçabilité nulle des opérations financières | Authentification biométrique sans mot de passe WebAuthn/FIDO2 par QR Code |
| **Silos de données entre Riads** | Absence de vision consolidée, impossibilité de mutualiser les tarifs | Architecture *Multi-Tenant* avec étanchéité logique des données |
| **Flux papier du Housekeeping** | Retards de mise à disposition des chambres lors des arrivées anticipées | Application mobile/PWA temps réel connectée par WebSockets au planning |

### 2.2 Fiches Descriptives des Cas d'Utilisation
- **CU01 (Authentification WebAuthn FIDO2) :** Déverrouillage sécurisé du poste de réception par scan QR Code depuis le smartphone de l'agent.
- **CU02 (Réservation avec Lock Redis) :** Acquisition atomique d'un verrou `SETNX` de 300s évitant les collisions de réservation lors des pics de charge.
- **CU03 (Night Audit Automatique) :** Traitement No-Show, imputation TVA 10%/TS/TPT, scellement comptable et archivage S3 MinIO.

---

# Chapitre 3 : Conception Technique et Architecture

### 3.1 Justification Comparative des Technologies

| Technologie | Rôle dans le Projet | Justification Technique Comparative |
| :--- | :--- | :--- |
| **Next.js 14 & TypeScript** | Frontend Web & PWA | Architecture hybride SSR pour tableaux de bord et CSR pour le planning interactif drag&drop avec typage strict. |
| **Python 3.11 & FastAPI** | 11 Microservices Backend | I/O asynchrone ultra-performant (Uvicorn), validation Pydantic v2 et documentation Swagger OpenAPI intégrée. |
| **PostgreSQL 15** | Persistance Transactionnelle | Fiabilité ACID, verrous de lignes (*Row-Level Locks*) et schéma dédié par microservice (*Database per Service*). |
| **Redis 7** | Cache & Lock Distribué | Verrous distribués atomiques et bus Pub/Sub pour diffusion WebSockets temps réel. |
| **RabbitMQ 3.12** | Broker d'Événements AMQP | Découplage asynchrone résilient entre services métier. |
| **Keycloak 24** | Serveur IAM & SSO | Gestion OIDC, RBAC et flux biométrique WebAuthn / Passkeys. |
| **Kong API Gateway 3.5** | Passerelle d'Entrée Unique | Routage multi-tenant, validation JWT, limitation de débit et portail Swagger unifié (port 8090). |
| **MinIO S3** | Stockage Objet | Archivage chiffré et immuable des rapports financiers PDF et factures. |

---

# Chapitre 4 : Développement et Réalisation

- **11 Microservices FastAPI :** `auth-gateway`, `establishment`, `housekeeping`, `pricing`, `partner`, `channel-manager`, `reservation`, `front-office`, `analytics`, `night-audit`, `notification`.
- **Résolution du bug critique Sprint 7 :** Découverte et correction de l'exclusion des séjours `status_checked_out` qui bloquait les chambres libérées.
- **Optimisation de la latence Sprint 8 :** Mutualisation du client HTTP partagé et parallélisation asynchrone des requêtes de tarification.

---

# Chapitre 5 : Tests, Validation et Résultats

- **170 Tests Unitaires Pytest :** 100% de succès sur l'ensemble des 11 microservices.
- **Tests E2E Playwright :** Validation des flux complets Login WebAuthn, Création de Séjour, Facturation et Check-out.
- **Audit de Sécurité :** Rejet des tokens JWT falsifiés ou expirés, isolation multi-tenant totale entre Riads.
- **Mesure des Performances :**
  - Latence initiale Sprint 7 : **2338 ms** (p95)
  - Latence optimisée Sprint 8 : **604 ms** (p95)
  - **Gain de performance mesuré : 74.2% de réduction de temps de réponse !**

---

# Chapitre 6 : Bilan du Stage et Compétences

| Domaine | Compétence Clé | Niveau de Maîtrise Démontré |
| :--- | :--- | :--- |
| **Architecture Logicielle** | Conception Microservices & DDD | Découpage de 11 contextes métier étanches avec Database per Service. |
| **Développement Backend** | Python / FastAPI / SQLAlchemy | Implémentation asynchrone, validation Pydantic v2 et migrations Alembic. |
| **Développement Frontend** | Next.js 14 / TypeScript / PWA | Planning interactif drag&drop, WebSockets et UI mobile responsive. |
| **Sécurité & IAM** | Keycloak / WebAuthn / RBAC | Déploiement SSO, flux biométrique FIDO2 sans mot de passe et isolation tenant. |
| **Assurance Qualité** | Pytest / Playwright / HTTPX | 170 tests unitaires, tests E2E automatisés et tests de charge concurrente. |
| **DevOps & Monitoring** | Docker / Kong / Prometheus | Conteneurisation isolée, passerelle d'API et supervision temps réel Grafana. |

---

## Conclusion Générale
Ce projet de fin d'études mené au sein d'**AMH Hospitality** dote l'opérateur hôtelier d'une solution propriétaire moderne, résiliente et performante, prête pour l'exploitation réelle des Riads de Marrakech.
