#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Chapitre 3 (Version Approfondie ~12 pages)
Conception Technique et Technologies
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable, KeepTogether
from reportlab.lib.units import cm

def build_chap3(styles, usable_width, c_primary, c_secondary, c_accent, get_fig, get_two_figs, make_table, make_callout):
    story = []
    
    story.append(Paragraph("CHAPITRE 3 : CONCEPTION TECHNIQUE ET TECHNOLOGIES", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    # ── 3.1 INTRODUCTION ───────────────────────────────────────────────────
    story.append(Paragraph("3.1 Introduction", styles['Sec1Title']))
    story.append(Paragraph(
        "La concrétisation logicielle d'une plateforme d'envergure telle que le <b>PMS Alidentec Hospitality</b> exige une sélection technologique "
        "rigoureuse, guidée par des impératifs d'industrialisation, de haute disponibilité, de latence ultra-faible et de sécurité de niveau bancaire. "
        "Plutôt que de se limiter à un empilement d'outils hétérogènes, chaque composant de la pile technique a été évalué, benchmarqué et choisi "
        "en fonction de sa valeur ajoutée directe pour résoudre les verrous métiers identifiés lors de la phase d'analyse.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Ce chapitre expose l'architecture technique globale et les fondations technologiques de la solution. Nous débuterons par la présentation du schéma "
        "d'architecture 4 tiers, puis nous détaillerons l'organisation des 11 microservices backend et le patron <i>Database per Service</i>. "
        "Nous analyserons ensuite les frameworks et bibliothèques côté frontend (Next.js 14, React 18, TypeScript, Tailwind CSS, PWA) et côté backend "
        "(Python 3.11, FastAPI, SQLAlchemy, Pydantic), la couche de persistance et de messagerie asynchrone (PostgreSQL 15, Redis 7, RabbitMQ 3.12, MinIO S3), "
        "l'infrastructure de sécurité Zero-Trust avec Keycloak et le standard WebAuthn/FIDO2, les outils DevOps (Docker Compose, Git, SonarQube), pour conclure sur "
        "la spécification normalisée des contrats d'API RESTful.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 3.2 ARCHITECTURE TECHNIQUE GLOBALE 4 TIERS ───────────────────────────
    story.append(Paragraph("3.2 Architecture Technique Globale 4 Tiers", styles['Sec1Title']))
    story.append(Paragraph(
        "La Figure 3-1 présente la cartographie complète de l'architecture technique 4 tiers déployée pour la plateforme PMS Alidentec. "
        "Cette architecture sépare strictement les responsabilités pour garantir l'évolutivité, la sécurité et la tolérance aux pannes.",
        styles['Body']
    ))
    
    story += get_fig("arch_technique.png", max_width=usable_width*0.95, max_height=8.5*cm,
                     caption="Figure 3-1 : Architecture Technique Globale 4 Tiers des Microservices PMS Alidentec", styles=styles)
    
    story.append(Paragraph(
        "Comme l'illustre la Figure 3-1, l'architecture s'articule autour de quatre couches interdépendantes et étanches :", styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Couche Clients et Présentation (Tier 1) :</b><br/>"
        "&bull; <i>Application Web Desktop (Next.js 14 / React 18 / TypeScript) :</i> Déployée sur les postes fixes de réception et d'administration, offrant un planning interactif Tape Chart ultra-fluide avec glisser-déposer et synchronisation WebSocket.<br/>"
        "&bull; <i>Progressive Web App (PWA) Mobile :</i> Application réactive optimisée pour les smartphones des gouvernantes et femmes de chambre d'étage.<br/>"
        "&bull; <i>Terminal Biométrique Mobile :</i> Smartphone personnel du collaborateur utilisé comme authentificateur externe (Cross-Device FIDO2).",
        styles['ReportBullet']
    ))
    story.append(Paragraph(
        "2. <b>Couche Passerelle d'API et Sécurité Périmétrique (Tier 2) :</b><br/>"
        "&bull; <i>Kong API Gateway :</i> Point d'entrée unique inversé assurant le routage dynamique, la terminaison SSL/TLS 1.3, le filtrage CORS, la limitation de débit (Rate Limiting) et l'agrégation des spécifications OpenAPI.<br/>"
        "&bull; <i>Keycloak Identity Provider :</i> Serveur centralisé de gestion des identités délivrant des jetons JWT asymétriques signés en RS256.",
        styles['ReportBullet']
    ))
    story.append(Paragraph(
        "3. <b>Couche Cœur Métier — Microservices FastAPI (Tier 3) :</b> Onze microservices spécialisés fonctionnant dans des conteneurs isolés, communiquant de manière synchrone par API REST/JSON et asynchrone par événements AMQP.",
        styles['ReportBullet']
    ))
    story.append(Paragraph(
        "4. <b>Couche Persistance, Cache et Middleware (Tier 4) :</b> Instances PostgreSQL 15 dédiées par service, cluster de cache Redis 7 pour les verrous distribués, courtier RabbitMQ 3.12 et stockage objet MinIO S3 pour l'archivage immuable.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 3.3 ARCHITECTURE LOGICIELLE MICROSERVICES ────────────────────────────
    story.append(Paragraph("3.3 Architecture Logicielle Microservices & Pattern Database per Service", styles['Sec1Title']))
    story.append(Paragraph(
        "L'application du patron <b>Database per Service</b> garantit qu'aucun microservice ne peut accéder directement aux tables de la base de données d'un autre service. "
        "Tout échange de données s'effectue exclusivement à travers des contrats d'API formellement définis ou par publication/souscription d'événements métiers.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))
    
    ms_table_data = [
        ["Microservice Backend", "Port", "Base & Schéma Dédié", "Rôle Métier & Responsabilités Techniques"],
        ["auth-gateway-service", "8001", "PostgreSQL (auth_db)", "Gestion des sessions, flux d'appairage QR FIDO2 et vérification des jetons JWT."],
        ["establishment-service", "8002", "PostgreSQL (estab_db)", "Référentiel des Riads, chambres, équipements, tarifs de base et Business Date."],
        ["guest-profile-service", "8003", "PostgreSQL (guest_db)", "Répertoire centralisé des voyageurs, historique des séjours et segmentation VIP."],
        ["pricing-service", "8004", "PostgreSQL (pricing_db)", "Moteur de calcul tarifaire dynamique, grilles saisonnières et promotions."],
        ["partner-service", "8005", "PostgreSQL (partner_db)", "Gestion des contrats d'agences partenaires et commissions d'intermédiation."],
        ["channel-manager-service", "8006", "PostgreSQL (channel_db)", "Passerelle de synchronisation bidirectionnelle avec Booking.com, Airbnb, Expedia."],
        ["reservation-service", "8007", "PostgreSQL (resv_db) + Redis", "Moteur de réservation, contrôle de disponibilité et verrous atomiques anti-overbooking."],
        ["front-office-service", "8008", "PostgreSQL (front_db)", "Gestion opérationnelle du Check-in/out, fiches de police et réattribution de chambres."],
        ["analytics-service", "8009", "PostgreSQL (analytics_db)", "Calcul des indicateurs consolidés de performance hôtelière (RevPAR, ADR, Taux d'occupation)."],
        ["night-audit-service", "8010", "PostgreSQL (audit_db) + MinIO", "Moteur de clôture journalière transactionnelle, facturation en masse et rapports S3."],
        ["notification-service", "8011", "RabbitMQ + WebSockets", "Routage événementiel des alertes temps réel (chambre propre, alerte solde, clôture)."]
    ]
    story += make_table(ms_table_data, [usable_width * 0.28, usable_width * 0.08, usable_width * 0.26, usable_width * 0.38],
                        "Tableau 3-1 : Cartographie détaillée des 11 microservices backend et bases associées", styles)
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("3.3.2 Communication synchrone (REST/JSON) vs asynchrone (AMQP / RabbitMQ)", styles['Sec2Title']))
    story.append(Paragraph(
        "L'architecture sépare clairement deux types de communication selon la criticité temporelle des opérations :<br/>"
        "&bull; <b>Flux synchrones (REST / JSON via HTTP/2) :</b> Utilisés pour les requêtes de lecture et de validation en temps réel où l'utilisateur attend une réponse immédiate (consultation du Tape Chart, vérification de disponibilité, calcul de devis tarifaire).<br/>"
        "&bull; <b>Flux asynchrones (AMQP via RabbitMQ) :</b> Utilisés pour les opérations découplées et la propagation d'événements métiers (diffusion d'un changement de statut de nettoyage, émission d'alertes financières, archivage de rapports PDF). Les microservices émetteurs publient l'événement et reprennent instantanément leur exécution sans bloquer le client.",
        styles['Body']
    ))
    story.append(Spacer(1, 8))
    
    # ── 3.4 ÉCOSYSTÈME TECHNOLOGIQUE FRONTEND ────────────────────────────────
    story.append(Paragraph("3.4 Écosystème Technologique Frontend", styles['Sec1Title']))
    
    story.append(Paragraph("3.4.1 Next.js 14, React 18 et TypeScript", styles['Sec2Title']))
    story.append(Paragraph(
        "Pour bâtir l'interface utilisateur du PMS, nous avons retenu le framework <b>Next.js 14</b> (développé par Vercel), combiné à <b>React 18</b> "
        "et au langage fortement typé <b>TypeScript</b>. Ce choix s'appuie sur l'exploitation de l'architecture <i>App Router</i> et des <i>React Server Components</i> (RSC), "
        "permettant de déporter le rendu des composants lourds côté serveur tout en réduisant drastiquement le bundle JavaScript transmis au client navigateur.",
        styles['Body']
    ))
    story.append(Paragraph(
        "L'intégration de TypeScript apporte une sécurité de typage de bout en bout : chaque interface de données correspond fidèlement aux schémas "
        "Pydantic exposés par le backend FastAPI, éliminant les erreurs de manipulation de propriétés à l'exécution.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("3.4.2 Tailwind CSS et composants d'interface réactifs", styles['Sec2Title']))
    story.append(Paragraph(
        "La couche de stylisation repose sur le framework utilitaire <b>Tailwind CSS</b>. Associé à la bibliothèque de composants headless <b>Radix UI</b> "
        "et aux icônes vectorielles <b>Lucide React</b>, il garantit un design system épuré, responsive, accessible et parfaitement conforme aux standards "
        "visuels modernes de l'hôtellerie de luxe. Les animations de transition fluide sont orchestrées via <b>Framer Motion</b>.", styles['Body']
    ))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("3.4.3 Architecture PWA Mobile pour la gouvernance d'étage", styles['Sec2Title']))
    story.append(Paragraph(
        "Plutôt que de développer une application mobile native distincte nécessitant un déploiement contraignant sur les stores applicatifs, "
        "l'application mobile Housekeeping a été intégrée directement sous la forme d'une <b>Progressive Web App (PWA)</b> au sein du même projet Next.js. "
        "Grâce aux <i>Service Workers</i> et au fichier <code>manifest.json</code>, la PWA s'installe en un clic sur l'écran d'accueil des smartphones des gouvernantes, "
        "assurant un fonctionnement fluide et la mise en cache des données même lors des pertes ponctuelles de couverture Wi-Fi dans les étages épais des Riads.",
        styles['Body']
    ))
    story.append(Spacer(1, 8))
    
    # ── 3.5 ÉCOSYSTÈME TECHNOLOGIQUE BACKEND ────────────────────────────────
    story.append(Paragraph("3.5 Écosystème Technologique Backend", styles['Sec1Title']))
    
    story.append(Paragraph("3.5.1 Python 3.11 et Framework FastAPI asynchrone", styles['Sec2Title']))
    story.append(Paragraph(
        "L'ensemble des 11 microservices backend est développé avec le langage <b>Python 3.11</b> et le framework web moderne <b>FastAPI</b>. "
        "Repousant sur le standard ASGI (<i>Asynchronous Server Gateway Interface</i>) et le serveur haute performance <b>Uvicorn</b>, FastAPI offre des performances "
        "en débit et latence comparables à Node.js et Go, tout en offrant la concision et la richesse de l'écosystème Python.",
        styles['Body']
    ))
    story.append(Paragraph(
        "FastAPI intègre nativement l'injection de dépendances (<i>Dependency Injection</i>), permettant d'extraire automatiquement l'utilisateur authentifié "
        "à partir du token JWT, d'isoler les sessions de base de données par requête et d'appliquer des filtres de sécurité stricts au niveau de chaque route.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("3.5.2 ORM SQLAlchemy 2.0 et validation Pydantic v2", styles['Sec2Title']))
    story.append(Paragraph(
        "&bull; <b>SQLAlchemy 2.0 (Mode Asynchrone) :</b> ORM de référence en Python, utilisé avec le pilote asynchrone <code>asyncpg</code> pour exécuter des requêtes non bloquantes vers PostgreSQL, gérant nativement les transactions ACID et les pools de connexions.<br/>"
        "&bull; <b>Pydantic v2 :</b> Moteur de validation de données ultra-rapide codé en Rust, assurant la sérialisation, la désérialisation et le typage strict de chaque payload JSON entrant et sortant, tout en générant automatiquement la documentation interactive Swagger / OpenAPI.<br/>"
        "&bull; <b>Alembic :</b> Outil de gestion des migrations de schémas relationnels garantissant la reproductibilité et la traçabilité des évolutions de base de données.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 3.6 PERSISTANCE, CACHE ET MESSAGERIE ────────────────────────────────
    story.append(Paragraph("3.6 Persistance, Cache Distribué et Messagerie", styles['Sec1Title']))
    story.append(Paragraph(
        "&bull; <b>PostgreSQL 15 :</b> Système de gestion de base de données relationnelle open-source réputé pour sa robustesse transactionnelle (ACID), son support natif des types JSONB pour les données semi-structurées et sa conformité SQL stricte.<br/>"
        "&bull; <b>Redis 7 :</b> Magasin de structure de données en mémoire haute vitesse (latence $< 1$ ms) utilisé pour l'acquisition de verrous distribués atomiques anti-overbooking via la commande <code>SET NX PX 10000</code>, la mise en cache des disponibilités et la gestion de la liste noire de tokens JWT révoqués.<br/>"
        "&bull; <b>RabbitMQ 3.12 :</b> Courtier de messages asynchrone implémentant le protocole AMQP 0-9-1. Toutes les files critiques sont configurées en mode <code>durable=True</code> avec accusé de réception manuel (<i>manual ack</i>), garantissant la persistance des messages même en cas de panne conteneur.<br/>"
        "&bull; <b>MinIO S3 :</b> Serveur de stockage objet open-source compatible avec l'API Amazon S3, déployé localement sous Docker pour archiver de manière immuable les rapports financiers certifiés du Night Audit et les factures PDF.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 3.7 SÉCURITÉ ET IAM ─────────────────────────────────────────────────
    story.append(Paragraph("3.7 Sécurité Périmétrique et Gestion des Identités", styles['Sec1Title']))
    story.append(Paragraph(
        "La sécurité de la plateforme PMS Alidentec repose sur une approche de sécurité en profondeur (<i>Defense in Depth</i>) et le principe du Zero-Trust :",
        styles['Body']
    ))
    story.append(Paragraph(
        "&bull; <b>Passerelle d'API Kong :</b> Intercepte l'ensemble du trafic externe, applique le filtrage CORS, bloque les requêtes abusives via le plugin de Rate Limiting (100 req/min par IP) et valide la présence du jeton JWT avant routage vers les microservices internes non exposés sur Internet.<br/>"
        "&bull; <b>Serveur d'Identité Keycloak :</b> Centralise la gestion des comptes utilisateurs, l'attribution des rôles RBAC (<code>ADMIN</code>, <code>RECEPTIONIST</code>, <code>HOUSEKEEPING</code>, <code>NIGHT_AUDITOR</code>) et l'émission des jetons signés cryptographiquement en RS256 avec clé asymétrique RSA 2048 bits.<br/>"
        "&bull; <b>Standard WebAuthn / FIDO2 :</b> Élimine totalement le stockage et la transmission de mots de passe sur le réseau. Le serveur ne conserve que la clé publique de l'utilisateur (courbe elliptique ECDSA P-256), tandis que la clé privée reste enfermée dans l'enclave sécurisée (Secure Enclave / TPM) du smartphone personnel du collaborateur.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 3.8 OUTILS DE DÉVELOPPEMENT ET DEVOPS ────────────────────────────────
    story.append(Paragraph("3.8 Outils de Développement et Industrialisation DevOps", styles['Sec1Title']))
    story.append(Paragraph(
        "Le Tableau 3-2 résume la matrice de justification technologique de chaque outil retenu dans la chaîne d'ingénierie d'Alidentec "
        "(Technologie &rarr; Rôle dans le projet &rarr; Raison du choix &rarr; Intégration dans l'architecture).", styles['Body']
    ))
    
    tools_data = [
        ["Technologie / Outil", "Rôle dans le Projet PMS", "Raison du Choix & Justification", "Intégration dans l'Architecture"],
        ["Visual Studio Code", "IDE de développement principal", "Écosystème d'extensions riche (Python, TypeScript, Docker, GitLens), légèreté.", "Utilisé par les 3 élèves-ingénieurs avec configuration partagée (.vscode)."],
        ["Docker & Compose", "Conteneurisation et orchestration", "Isolation stricte des dépendances, reproductibilité parfaite entre environnements.", "Orchestre les 18 conteneurs interconnectés sur le réseau bridge privé."],
        ["Git & GitHub", "Gestion de versions & collaboration", "Traçabilité cryptographique, Feature Branch Workflow et Pull Requests obligatoires.", "Dépôt GitHub Enterprise avec protection de la branche main et CI/CD."],
        ["Postman & Newman", "Tests et qualification des API", "Création de collections de requêtes automatisées, validation des schémas JSON.", "Tests automatisés des 45 endpoints exposés à travers la passerelle Kong."],
        ["SonarQube 10.4", "Audit continu de qualité de code", "Détection automatique des vulnérabilités OWASP, mesure de dette technique et couverture.", "Pipeline CI/CD bloquant toute fusion en cas de non-respect du Quality Gate."],
        ["Pytest & Asyncio", "Framework de tests unitaires", "Support natif des coroutines asynchrones, fixtures puissantes et exécution ultra-rapide.", "Validation des 10 suites de tests unitaires avec temps d'exécution < 5 ms."]
    ]
    story += make_table(tools_data, [usable_width * 0.22, usable_width * 0.24, usable_width * 0.28, usable_width * 0.26],
                        "Tableau 3-2 : Matrice de justification technologique et sélection des outils d'ingénierie", styles)
    story.append(Spacer(1, 8))
    
    # ── 3.9 SPÉCIFICATION DES CONTRATS D'API REST ────────────────────────────
    story.append(Paragraph("3.9 Spécification des Contrats d'API RESTful et Codes HTTP", styles['Sec1Title']))
    story.append(Paragraph(
        "L'ensemble des interactions synchrones entre le frontend Next.js et les microservices FastAPI s'effectue via des API RESTful standardisées "
        "respectant le modèle de maturité de Richardson (Niveau 2). Le Tableau 3-3 formalise les endpoints critiques et leurs codes de statut HTTP associés.",
        styles['Body']
    ))
    
    api_data = [
        ["Méthode HTTP", "Endpoint Exposé (via Kong)", "Microservice Cible", "Description Métier", "Codes HTTP Retournés"],
        ["POST", "/api/v1/auth/login/begin", "auth-gateway", "Génération du challenge FIDO2 et émission du QR Code", "200 OK, 400 Bad Request"],
        ["POST", "/api/v1/auth/login/finish", "auth-gateway", "Vérification signature biométrique et délivrance du JWT", "200 OK, 401 Unauthorized"],
        ["GET", "/api/v1/establishments/{id}/rooms", "establishment", "Consultation de l'inventaire et des statuts des suites", "200 OK, 404 Not Found"],
        ["POST", "/api/v1/reservations", "reservation", "Création de séjour avec verrouillage atomique Redis", "201 Created, 409 Conflict"],
        ["POST", "/api/v1/front-office/check-in", "front-office", "Enregistrement de l'arrivée et édition fiche de police", "200 OK, 422 Unprocessable"],
        ["POST", "/api/v1/billing/folios/{id}/charges", "billing-folio", "Imputation d'une consommation extra avec calcul TVA", "201 Created, 400 Bad Request"],
        ["POST", "/api/v1/night-audit/execute", "night-audit", "Déclenchement clôture journalière et avance Business Date", "200 OK, 500 Internal Error"],
        ["PATCH", "/api/v1/housekeeping/rooms/{id}", "housekeeping", "Mise à jour du statut d'hygiène de la chambre (DIRTY/CLEAN)", "200 OK, 403 Forbidden"]
    ]
    story += make_table(api_data, [usable_width * 0.12, usable_width * 0.32, usable_width * 0.18, usable_width * 0.24, usable_width * 0.14],
                        "Tableau 3-3 : Spécification des endpoints d'API REST critiques et codes de statut HTTP", styles)
    story.append(Spacer(1, 8))
    
    # ── 3.10 CONCLUSION DU CHAPITRE ─────────────────────────────────────────
    story.append(Paragraph("3.10 Conclusion du Chapitre", styles['Sec1Title']))
    story.append(Paragraph(
        "Ce troisième chapitre a détaillé l'ensemble de l'architecture technique 4 tiers et la sélection technologique rigoureuse "
        "ayant guidé la construction du <b>PMS Alidentec Hospitality</b>. En combinant la réactivité de <b>Next.js 14</b>, la performance asynchrone "
        "de <b>FastAPI</b>, l'intégrité de <b>PostgreSQL</b>, la rapidité en mémoire de <b>Redis</b>, la fiabilité de <b>RabbitMQ</b> et la sécurité "
        "sans mot de passe de <b>WebAuthn / Keycloak</b>, le système dispose d'une infrastructure robuste et hautement industrielle. "
        "Le chapitre suivant sera consacré à la <b>Réalisation Pratique et à la Présentation des Interfaces Utilisateurs</b> développées.",
        styles['Body']
    ))
    story.append(PageBreak())
    
    return story
