#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Chapitre 6 (Version Ultra-Détaillée ~10 pages)
Bilan du Stage et Apports d'Ingénierie
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable, KeepTogether
from reportlab.lib.units import cm

def build_chap6(styles, usable_width, c_primary, c_secondary, c_accent, get_fig, get_two_figs, make_table, make_callout):
    story = []
    
    story.append(Paragraph("CHAPITRE 6 : BILAN DU STAGE ET APPORTS D'INGÉNIERIE", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    # ── 6.1 INTRODUCTION ───────────────────────────────────────────────────
    story.append(Paragraph("6.1 Introduction", styles['Sec1Title']))
    story.append(Paragraph(
        "Ce sixième et dernier chapitre dresse le bilan réflexif, technique, méthodologique et humain de ce stage d'ingénierie "
        "effectué au sein de l'entreprise <b>Alidentec</b>. Au-delà des livrables logiciels opérationnels, ce projet a constitué une opportunité "
        "d'apprentissage exceptionnelle permettant de consolider nos acquis théoriques d'élèves-ingénieurs de l'<b>EMSI Marrakech</b>, "
        "de nous confronter aux exigences de production d'un progiciel hôtelier d'envergure, et de développer des compétences professionnelles "
        "transversales indispensables à l'exercice du métier d'ingénieur logiciel.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Nous analyserons successivement les apports techniques et la maîtrise des technologies cloud-native, les apports professionnels "
        "et la compréhension intime du métier hôtelier, les leçons organisationnelles tirées de la gestion de projet Agile Scrum en équipe de trois "
        "élèves-ingénieurs, la matrice détaillée des compétences acquises, les contributions personnelles de chacun, avant d'esquisser les perspectives "
        "d'évolution et la roadmap future du produit.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 6.2 APPORTS TECHNIQUES ET MAÎTRISE DU CLOUD-NATIVE ───────────────────
    story.append(Paragraph("6.2 Apports Techniques et Maîtrise des Technologies Cloud-Native", styles['Sec1Title']))
    story.append(Paragraph(
        "Sur le plan purement technologique, le projet a permis à notre équipe de franchir un cap significatif en matière d'ingénierie logicielle avancée :",
        styles['Body']
    ))
    story.append(Paragraph(
        "&bull; <b>Architectures distribuées et Domain-Driven Design (DDD) :</b> Maîtrise complète du découpage modulaire en microservices autonomes, "
        "application du patron Database per Service, gestion de la cohérence transactionnelle à travers des événements asynchrones et découplage via passerelle d'API.<br/>"
        "&bull; <b>Développement backend asynchrone haute performance :</b> Exploitation avancée des coroutines Python (<code>asyncio</code>), du framework FastAPI, "
        "de la sérialisation Pydantic v2 et des requêtes SQL par lots pour optimiser les traitements de masse (Night Audit en 45 secondes).<br/>"
        "&bull; <b>Frontend réactif moderne et mobilité :</b> Conception d'interfaces riches sous Next.js 14 (App Router, Server Components, TypeScript), "
        "gestion des flux bidirectionnels WebSockets pour le planning interactif Tape Chart et développement d'une Progressive Web App (PWA) fluide.<br/>"
        "&bull; <b>Sécurité cryptographique et authentification sans mot de passe :</b> Implémentation pratique des standards W3C WebAuthn / FIDO2 par flux QR Code, "
        "manipulation des clés asymétriques ECDSA P-256 et configuration fine des serveurs d'identité Keycloak OIDC avec tokens JWT RS256.<br/>"
        "&bull; <b>Gestion de la concurrence et verrous distribués :</b> Conception d'algorithmes d'exclusion mutuelle à bail temporel sous Redis 7 (Redlock) "
        "garantissant zéro surréservation lors des pics de trafic concurrent.<br/>"
        "&bull; <b>Industrialisation DevOps et Assurance Qualité :</b> Orchestration multi-conteneurs sous Docker Compose, automatisation des tests unitaires Pytest "
        "(100% de succès), scénarios E2E Playwright et maintien continu du Quality Gate SonarQube (Note A).",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 6.3 APPORTS PROFESSIONNELS ET IMMERSION MÉTIER ───────────────────────
    story.append(Paragraph("6.3 Apports Professionnels et Immersion Métier chez Alidentec", styles['Sec1Title']))
    story.append(Paragraph(
        "L'immersion dans l'environnement d'ingénierie d'Alidentec et les échanges continus avec les équipes opérationnelles hôtelières partenaires "
        "(AMH Hospitality) ont apporté des enseignements professionnels déterminants :", styles['Body']
    ))
    story.append(Paragraph(
        "&bull; <b>Sens aigu du besoin utilisateur :</b> Comprendre que la perfection technique d'un algorithme n'a de valeur que si elle se traduit par une interface "
        "simple, ergonomique et sans friction pour un réceptionniste sous pression ou une femme de chambre dans les étages.<br/>"
        "&bull; <b>Rigueur comptable et réglementaire :</b> Appréhender la complexité du droit fiscal marocain (TVA réduite à 10%, taxes communales TS et TPT) "
        "et l'obligation d'exactitude absolue sur les centimes dans les folios financiers.<br/>"
        "&bull; <b>Culture du livrable industriel :</b> Passer de la logique académique du prototype « qui marche sur ma machine » à la discipline d'un code source "
        "entièrement conteneurisé, documenté, testé et déployable de manière reproductible sur n'importe quel serveur.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 6.4 ENSEIGNEMENTS ORGANISATIONNELS ET GESTION AGILE ─────────────────
    story.append(Paragraph("6.4 Enseignements Organisationnels et Gestion Agile en Trinôme", styles['Sec1Title']))
    story.append(Paragraph(
        "La conduite du projet à trois élèves-ingénieurs sur une durée de 16 semaines a constitué une formidable école de travail d'équipe et de management de projet :",
        styles['Body']
    ))
    story.append(Paragraph(
        "&bull; <b>Discipline des rituels Scrum :</b> Le respect scrupuleux des réunions quotidiennes (Daily Stand-up de 15 minutes) a permis de lever immédiatement "
        "les blocages techniques et de maintenir un niveau d'énergie et de cohésion maximal au sein de l'équipe.<br/>"
        "&bull; <b>Gouvernance Git et revues de code systématiques :</b> L'adoption du Feature Branch Workflow avec obligation d'au moins une relecture par les pairs "
        "avant toute fusion sur la branche <code>main</code> a permis d'élever collectivement la qualité du code et d'éviter les régressions.<br/>"
        "&bull; <b>Gestion du compromis et pragmatisme technique :</b> Savoir identifier et documenter honnêtement la dette technique (comme lors du Sprint 7 où le p95 "
        "était de 2.3s avant d'être optimisé à 604 ms au Sprint 8) plutôt que de dissimuler les faiblesses.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 6.5 MATRICE DES COMPÉTENCES D'INGÉNIEUR DÉVELOPPÉES ──────────────────
    story.append(Paragraph("6.5 Matrice des Compétences d'Ingénieur Développées", styles['Sec1Title']))
    story.append(Paragraph(
        "Le Tableau 6-1 récapitule la cartographie des compétences d'ingénierie acquises et consolidées lors de la réalisation du projet PMS chez Alidentec.",
        styles['Body']
    ))
    
    skills_data = [
        ["Axe de Compétence", "Domaine Spécifique", "Niveau de Maîtrise Démontré"],
        ["Architecture Logicielle", "Microservices, DDD & Database per Service", "Conception complète d'un système distribué en 11 services autonomes avec isolation stricte des données et bus AMQP."],
        ["Développement Backend", "Python 3.11, FastAPI & SQLAlchemy", "Développement d'API REST asynchrones, validation Pydantic v2, calculs fiscaux bancaires et traitement par lots."],
        ["Développement Frontend", "Next.js 14, React 18 & TypeScript", "Interface riche interactive (Tape Chart Drag & Drop), Progressive Web App mobile et flux WebSockets temps réel."],
        ["Sécurité & Cryptographie", "WebAuthn / FIDO2 & Keycloak IAM", "Authentification biométrique sans mot de passe par QR Code, gestion des tokens JWT signés en RS256 et rôles RBAC."],
        ["Persistance & Middleware", "PostgreSQL, Redis 7 & RabbitMQ", "Transactions ACID complexes, verrous atomiques distribués anti-collision et files de messages durables persistantes."],
        ["DevOps & Qualité", "Docker Compose, Pytest & SonarQube", "Conteneurisation multi-services, automatisation intégrale des tests (100% succès) et certification Quality Gate Passed."],
        ["Gestion de Projet", "Agile Scrum & Collaboration Git", "Pilotage itératif en 8 sprints de 2 semaines, réunions quotidiennes, revues de code et livraison continue de valeur."]
    ]
    story += make_table(skills_data, [usable_width * 0.25, usable_width * 0.28, usable_width * 0.47],
                        "Tableau 6-1 : Matrice d'évaluation des compétences d'ingénierie acquises lors du stage", styles)
    story.append(Spacer(1, 8))
    
    # ── 6.6 CONTRIBUTIONS PERSONNELLES DÉTAILLÉES ────────────────────────────
    story.append(Paragraph("6.6 Contributions Personnelles de Chaque Élève-Ingénieur", styles['Sec1Title']))
    story.append(Paragraph(
        "&bull; <b>Nabil BOUDARINE :</b> Prise en charge de l'architecture générale du système, configuration de la passerelle Kong API Gateway, "
        "intégration du serveur Keycloak avec le standard WebAuthn/FIDO2, conception du moteur de clôture Night Audit asynchrone et archivage S3, "
        "orchestration multi-conteneurs Docker Compose et supervision des déploiements.<br/>"
        "&bull; <b>Youssef OUIZZA :</b> Conception ergonomique et développement de l'interface frontend Next.js 14, réalisation du planning interactif "
        "Tape Chart avec glisser-déposer (Drag & Drop) et Room Shift, intégration des flux bidirectionnels WebSockets pour la réactivité temps réel, "
        "développement des formulaires de réservation réactifs et dashboards de gestion.<br/>"
        "&bull; <b>Mohamed Hamza IBNTALIB :</b> Développement des microservices de facturation (Billing/Folios), implémentation stricte des algorithmes de calcul fiscal "
        "marocain (TVA 10%, TS 25 MAD, TPT 12 MAD), développement de la PWA mobile Housekeeping, configuration du courtier RabbitMQ et rédaction des suites "
        "de tests unitaires automatisés sous Pytest.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 6.7 PERSPECTIVES D'ÉVOLUTION ET ROADMAP ──────────────────────────────
    story.append(Paragraph("6.7 Perspectives d'Évolution et Roadmap Future", styles['Sec1Title']))
    story.append(Paragraph(
        "Pour prolonger l'industrialisation de la plateforme au sein d'Alidentec, la roadmap d'évolution identifie quatre axes d'amélioration :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Observabilité distribuée avec OpenTelemetry & Jaeger :</b> Implémenter le traçage distribué des requêtes traversant les 11 microservices pour mesurer avec précision la latence inter-services.<br/>"
        "2. <b>Moteur de tarification prédictive par Intelligence Artificielle :</b> Intégrer un modèle de Machine Learning (Time Series Forecasting) pour recommander dynamiquement les tarifs optimaux des suites en fonction de la demande historique et des événements locaux à Marrakech.<br/>"
        "3. <b>Connecteurs OTA directs et certification 2-Way :</b> Développer les passerelles directes avec les API partenaires de Booking.com et Airbnb sans passer par des agrégateurs tiers.<br/>"
        "4. <b>Déploiement sur cluster Kubernetes managé :</b> Migrer l'orchestration Docker Compose vers Kubernetes (EKS / GKE / K3s) avec politiques d'Auto-Scaling horizontal (HPA) pour supporter des chaînes de plus de 100 établissements.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 6.8 CONCLUSION DU CHAPITRE ──────────────────────────────────────────
    story.append(Paragraph("6.8 Conclusion du Chapitre", styles['Sec1Title']))
    story.append(Paragraph(
        "Ce sixième chapitre a dressé le bilan hautement positif de notre stage de fin d'année au sein d'<b>Alidentec</b>. "
        "Ce projet nous a permis de valider notre capacité à concevoir et livrer une plateforme logicielle complète, robuste, ergonomique et certifiée "
        "conforme aux plus hauts standards de l'industrie. La section suivante présentera la <b>Conclusion Générale et les Perspectives</b> du mémoire.",
        styles['Body']
    ))
    story.append(PageBreak())
    
    return story
