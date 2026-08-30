#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Chapitre 1 — Présentation de l'Entreprise et Cadre du Projet
Contenu académique dense, sans captures superflues (strictement réservées au Chapitre 4).
Intègre le planning de Gantt officiel du projet.
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor

def build_chap1(styles, usable_width, c_primary, c_secondary, c_accent,
                get_fig_flowable, get_two_figs_flowable, make_table_flowable, make_callout_flowable):
    story = []
    
    # ── 1.1 INTRODUCTION ───────────────────────────────────────────────────
    story.append(Paragraph("1.1 Introduction", styles['Sec1Title']))
    story.append(Paragraph(
        "Ce premier chapitre pose le cadre contextuel, organisationnel et méthodologique dans lequel s'est inscrit "
        "notre projet de fin d'année d'ingénieur. Nous débuterons par une présentation approfondie de notre organisme "
        "d'accueil, l'entreprise <b>Alidentec</b>, de sa vision stratégique, de ses pôles d'expertise et de sa gouvernance "
        "technique. Nous détaillerons ensuite le cadre institutionnel de l'École Marocaine des Sciences de l'Ingénieur "
        "(EMSI Marrakech) et les objectifs pédagogiques fixés pour ce stage de fin d'études.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Dans un second temps, nous exposerons l'immersion terrain menée au sein des établissements hôteliers partenaires, "
        "permettant de circonscrire précisément les enjeux opérationnels du projet. Enfin, nous expliciterons la démarche de "
        "conduite de projet adoptée, basée sur le framework Agile Scrum, ainsi que la planification prévisionnelle de nos huit sprints "
        "de développement matérialisée par le diagramme de Gantt officiel.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))
    
    # ── 1.2 PRÉSENTATION DE L'ORGANISME D'ACCUEIL (ALIDENTEC) ──────────────
    story.append(Paragraph("1.2 Présentation de l'Organisme d'Accueil : Alidentec", styles['Sec1Title']))
    story.append(Paragraph("<b>1.2.1 Historique, Positionnement et Vision d'Entreprise</b>", styles['Sec2Title']))
    story.append(Paragraph(
        "Fondée par des ingénieurs passionnés par l'innovation logicielle et la transformation numérique, <b>Alidentec</b> est une société "
        "d'ingénierie et de conseil en technologies informatiques. L'entreprise s'est forgé une solide réputation en concevant des architectures "
        "logicielles sur mesure, hautement résilientes et adaptées aux exigences critiques d'entreprises opérant dans des secteurs variés : "
        "hospitality, commerce omnicanal, fintech et industrie 4.0.",
        styles['Body']
    ))
    story.append(Paragraph(
        "La vision d'Alidentec repose sur l'adoption précoce des standards ouverts du Cloud-Native Computing (CNCF), la promotion des architectures "
        "microservices décentralisées, l'application rigoureuse des principes du <i>Domain-Driven Design</i> (DDD) et l'intégration systématique "
        "de pipelines d'intégration et de déploiement continus (CI/CD) garantissant un très haut niveau de qualité logicielle.",
        styles['Body']
    ))
    
    # Tableau 1-1 : Fiche Signalétique
    t1_data = [
        ["Critère d'Identification", "Informations Légales et Opérationnelles"],
        ["Raison Sociale", "ALIDENTEC S.A.R.L."],
        ["Activité Principale", "Ingénierie logicielle, édition de progiciels métiers et conseil Cloud-Native"],
        ["Domaines d'Expertise", "Architectures Microservices, Systèmes Distribués, Applications Web & Mobiles, DevOps"],
        ["Secteurs Cibles", "Hôtellerie de luxe (Hospitality), Tourisme, Retail et Systèmes Financiers"],
        ["Technologies Clés Maîtrisées", "Python (FastAPI), React / Next.js, Go, PostgreSQL, Redis, RabbitMQ, Docker, Kubernetes"],
        ["Normes et Qualité", "Clean Architecture, TDD / BDD, OWASP ASVS, SonarQube Quality Gates"],
        ["Implantation", "Marrakech & Casablanca, Maroc"],
        ["Partenaires & Écosystème", "Établissements Hôteliers, Riads de Prestige, EMSI Marrakech"]
    ]
    story += make_table_flowable(t1_data, [usable_width*0.35, usable_width*0.65],
                                "Tableau 1-1 : Fiche signalétique et d'identité de l'entreprise Alidentec", styles)
    
    story.append(Paragraph("<b>1.2.2 Pôles d'Expertise et Organisation Interne</b>", styles['Sec2Title']))
    story.append(Paragraph(
        "L'organisation d'Alidentec est structurée en plusieurs cellules d'ingénierie agiles favorisant l'émulation technique et le transfert de compétences :<br/>"
        "&bull; <b>Pôle Architecture & Backend :</b> Responsable de la conception des socles applicatifs distribués, de l'élaboration des schémas de données, de la scalabilité horizontale et des intergiciels de communication asynchrone (RabbitMQ, Kafka).<br/>"
        "&bull; <b>Pôle Frontend & Expérience Utilisateur (UI/UX) :</b> Développe des interfaces riches, ergonomiques et réactives sous React et Next.js, en veillant à l'accessibilité, à la fluidité des interactions et à la portabilité sur terminaux mobiles (PWA).<br/>"
        "&bull; <b>Pôle DevOps, Cloud & Sécurité :</b> Administre les infrastructures d'intégration continue, le provisionnement conteneurisé (Docker / Kubernetes), l'observabilité (Prometheus, Grafana) et la conformité aux exigences de cybersécurité périmétrique.<br/>"
        "&bull; <b>Pôle Assurance Qualité (QA) & Audit :</b> Supervise la rédaction des suites de tests automatisés (unitaires, intégration, bout-en-bout) et pilote l'analyse statique du code sous SonarQube.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 4))
    
    # ── 1.3 PRÉSENTATION DU CADRE INSTITUTIONNEL (EMSI) ────────────────────
    story.append(Paragraph("1.3 Présentation du Cadre Institutionnel (EMSI) et du Stage", styles['Sec1Title']))
    story.append(Paragraph(
        "Créée en 1986, l'<b>École Marocaine des Sciences de l'Ingénieur (EMSI)</b>, membre du réseau <i>Honoris United Universities</i>, est la première "
        "école d'ingénierie privée du Royaume du Maroc. Reconnue par l'État pour son excellence pédagogique et la rigueur de sa formation scientifique, "
        "l'EMSI forme des ingénieurs polyvalents, directement opérationnels et dotés d'un sens aigu de l'innovation et du leadership technique.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Au sein de la filière <b>Ingénierie Informatique et Réseaux (IIR)</b>, l'option <i>Génie Logiciel</i> dispense une formation avancée en modélisation "
        "orientée objet, génie logiciel formel, architectures microservices, sécurité des systèmes d'information et management de projets agiles. "
        "Le Projet de Fin d'Année (PFA) constitue l'aboutissement de ce cycle de formation, exigeant des étudiants la réalisation intégrale d'un projet "
        "industriel complexe, depuis la formalisation des besoins jusqu'au déploiement et à la validation opérationnelle sur site.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))
    
    # ── 1.4 IMMERSION MÉTIER & PROJET HÔTELIER ─────────────────────────────
    story.append(Paragraph("1.4 Immersion Métier & Présentation du Projet Hôtelier", styles['Sec1Title']))
    story.append(Paragraph(
        "Afin d'ancrer notre démarche d'ingénierie dans la réalité opérationnelle du secteur touristique marocain, notre trinôme a réalisé une phase "
        "d'immersion intensive de deux semaines au sein de trois <b>Riads pilotes de la Médina de Marrakech</b> partenaires d'Alidentec. Cette immersion "
        "en immersion totale a consisté à observer et documenter minutieusement le quotidien des équipes de front-office, de réservation, de gouvernance "
        "et de direction générale.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Cette phase d'audit sur le terrain a révélé des spécificités métier cruciales qui ont directement dicté les choix de conception du PMS Alidentec :<br/>"
        "1. <b>Hétérogénéité des canaux d'acquisition :</b> Les réservations affluent simultanément par les OTAs (Booking.com, Airbnb, Expedia), par le site web direct de l'hôtel et par des agences de voyage réceptives locales.<br/>"
        "2. <b>Exigences réglementaires et policières strictes :</b> En vertu de la législation marocaine régissant les établissements touristiques, tout hébergeur est tenu de renseigner pour chaque voyageur étranger une <i>Fiche Individuelle de Police</i> normée et de transmettre un état journalier des arrivées aux services de la DGSN.<br/>"
        "3. <b>Complexité de la fiscalité touristique locale :</b> Contrairement à une facturation commerciale standard, une facture d'hôtel au Maroc doit ventiler rigoureusement la prestation d'hébergement (soumise à une <b>TVA de 10%</b>), la <b>Taxe de Séjour communale (TS)</b> fixée à 25 MAD par adulte et par nuitée, ainsi que la <b>Taxe de Promotion Touristique (TPT)</b> de 12 MAD par adulte et par nuitée.<br/>"
        "4. <b>Mobilité et réactivité des équipes d'étage :</b> Dans la configuration architecturale sur plusieurs niveaux d'un Riad traditionnel, le personnel de ménage ne peut être tributaire de terminaux fixes de bureau. Une solution mobile légère et synchronisée en temps réel s'avérait indispensable.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 4))
    
    # ── 1.5 MÉTHODOLOGIE AGILE SCRUM ───────────────────────────────────────
    story.append(Paragraph("1.5 Méthodologie de Conduite de Projet (Agile Scrum)", styles['Sec1Title']))
    story.append(Paragraph(
        "Compte tenu de la complexité du domaine métier hôtelier, de la multiplicité des microservices à développer et de la nécessité de livrer "
        "des incréments fonctionnels testables à intervalles réguliers, nous avons adopté la méthodologie <b>Agile Scrum</b>. Ce cadre méthodologique "
        "a favorisé une communication fluide au sein de notre trinôme et une réactivité optimale face aux retours des hôteliers partenaires.",
        styles['Body']
    ))
    story.append(Paragraph(
        "L'organisation des rituels Scrum a été rythmée selon les règles suivantes :<br/>"
        "&bull; <b>Durée des Sprints :</b> Fixée à 2 semaines par sprint, soit un total de 8 sprints répartis sur les 16 semaines du projet.<br/>"
        "&bull; <b>Sprint Planning :</b> Sélection des User Stories prioritaires dans le Product Backlog, estimation de la complexité en Story Points (suite de Fibonacci) et engagement sur le Sprint Goal.<br/>"
        "&bull; <b>Daily Standup Meeting :</b> Point de synchronisation quotidien de 15 minutes structuré autour de trois questions clés (Qu'ai-je accompli hier ? Que vais-je faire aujourd'hui ? Quels obstacles bloquent ma progression ?).<br/>"
        "&bull; <b>Sprint Review & Démonstration :</b> Présentation de l'incrément logiciel opérationnel aux tuteurs d'Alidentec et aux gérants de Riads pilotes pour validation continue.<br/>"
        "&bull; <b>Sprint Retrospective :</b> Analyse réflexive du fonctionnement de l'équipe pour identifier les pistes d'amélioration technique et organisationnelle.",
        styles['ReportBullet']
    ))
    
    # Tableau 1-2 : Calendrier des Sprints
    t2_data = [
        ["Sprint", "Objectif Majeur du Sprint (Sprint Goal)", "Livrables Validés", "Période"],
        ["Sprint 1", "Cadrage, études de terrain Riads & spécification du Product Backlog", "Cahier des charges, Backlog Jira", "Semaines 1-2"],
        ["Sprint 2", "Architecture microservices, schémas PostgreSQL & socle Docker", "Docker Compose, FastAPI skeleton", "Semaines 3-4"],
        ["Sprint 3", "Service IAM, intégration Keycloak & flux WebAuthn FIDO2 QR", "Auth Service opérationnel", "Semaines 5-6"],
        ["Sprint 4", "Module Réservation, verrouillage Redis & moteur fiscal marocain", "Reservation Service & tests", "Semaines 7-8"],
        ["Sprint 5", "Module Facturation Folio, imputation des extras & paiements", "Folio Service & facturation", "Semaines 9-10"],
        ["Sprint 6", "Moteur de clôture Night Audit & archivage immuable MinIO S3", "Night Audit Service & rapports", "Semaines 11-12"],
        ["Sprint 7", "PWA mobile Housekeeping, WebSockets & console Multi-Riads", "PWA mobile & WebSockets RabbitMQ", "Semaines 13-14"],
        ["Sprint 8", "Tests de charge, qualification SonarQube & recette finale", "Rapport de tests, Quality Gate Passed", "Semaines 15-16"]
    ]
    story += make_table_flowable(t2_data, [usable_width*0.12, usable_width*0.48, usable_width*0.26, usable_width*0.14],
                                "Tableau 1-2 : Calendrier prévisionnel et jalons majeurs des 8 sprints Scrum", styles)
    
    # ── 1.6 PLANIFICATION ET DIAGRAMME DE GANTT ────────────────────────────
    story.append(Paragraph("1.6 Planification Temporelle et Diagramme de Gantt", styles['Sec1Title']))
    story.append(Paragraph(
        "Afin de garantir le respect scrupuleux des échéances et la synchronisation des développements inter-services, nous avons modélisé "
        "le chemin critique du projet à travers un diagramme de Gantt détaillé. Ce dernier illustre l'ordonnancement séquentiel et parallèle "
        "des tâches d'ingénierie.",
        styles['Body']
    ))
    
    # Diagramme de Gantt
    story += get_fig_flowable("gantt_pms.png", max_width=usable_width, max_height=8.0*cm,
                             caption="Figure 1-1 : Planning de Gantt des 8 Sprints de développement du projet PMS Alidentec", styles=styles)
    
    # ── 1.7 CONCLUSION DU CHAPITRE ─────────────────────────────────────────
    story.append(Paragraph("1.7 Conclusion du Chapitre", styles['Sec1Title']))
    story.append(Paragraph(
        "Ce premier chapitre a permis d'établir avec précision le cadre institutionnel et industriel de notre mémoire. "
        "L'immersion terrain au cœur des Riads de Marrakech a mis en lumière les attentes fondamentales du secteur, tandis que "
        "le cadrage Agile Scrum et le planning de Gantt ont défini la trajectoire opérationnelle de nos travaux. "
        "Fort de ce socle, le chapitre suivant sera consacré à l'analyse détaillée des besoins et à la modélisation formelle du système sous UML.",
        styles['Body']
    ))
    story.append(PageBreak())
    
    return story
