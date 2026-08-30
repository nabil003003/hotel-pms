#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Pages Préliminaires
Conforme aux normes de l'EMSI et du Guide PFA (F. ENNAAMA)
- Dédicace (Page II)
- Remerciements (Page III)
- Résumé en Français (Page IV - Page dédiée)
- Abstract in English (Page V - Page dédiée)
- Glossaire Technique et Métier (Page VI)
- Table des Matières (Page VII)
- Liste des Figures (Page IX)
- Liste des Tableaux (Page X)
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.units import cm
from reportlab.lib.colors import white, HexColor

def to_roman_upper(n):
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num

def build_preliminaries(styles, usable_width, c_primary, c_light_bg):
    story = []
    
    # ── II. DÉDICACE ─────────────────────────────────────────────────────────
    story.append(Paragraph("DÉDICACE", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    dedicaces = [
        "<i>À nos très chers parents, pour leurs sacrifices constants, leur soutien inconditionnel et leurs prières tout au long de notre cursus d'ingénieur. Que ce travail soit le témoignage de notre profonde gratitude et de notre affection éternelle.</i>",
        "<i>À nos frères et sœurs, pour leurs encouragements chaleureux et leur présence réconfortante à chaque étape de notre formation.</i>",
        "<i>À l'ensemble du corps professoral et administratif de l'École Marocaine des Sciences de l'Ingénieur (EMSI Marrakech), pour la qualité de l'enseignement dispensé et leur quête constante d'excellence.</i>",
        "<i>À l'équipe d'Alidentec, pour la confiance accordée et l'environnement d'ingénierie stimulant ayant permis l'aboutissement de ce projet d'envergure.</i>",
        "<i>À tous nos amis et collègues de promotion, avec qui nous avons partagé ces années d'apprentissage, d'efforts et de passions technologiques partagées.</i>"
    ]
    for d in dedicaces:
        story.append(Paragraph(d, styles['Body']))
        story.append(Spacer(1, 6))
    story.append(PageBreak())
    
    # ── III. REMERCIEMENTS ───────────────────────────────────────────────────
    story.append(Paragraph("REMERCIEMENTS", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    story.append(Paragraph(
        "Au terme de ce projet de fin d'année, nous tenons à exprimer notre profonde gratitude et nos remerciements les plus sincères "
        "à toutes les personnes qui ont contribué de près ou de loin à la réussite de ce mémoire d'ingénierie.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Nous adressons tout particulièrement nos vifs remerciements à la direction et aux équipes techniques de l'entreprise <b>Alidentec</b> "
        "pour leur accueil chaleureux, leur accompagnement professionnel bienveillant et les moyens matériels et d'infrastructure mis à notre entière disposition.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Nous exprimons notre reconnaissance la plus chaleureuse à notre encadrant professionnel chez Alidentec, pour sa disponibilité constante, "
        "ses conseils techniques éclairés en architecture logicielle distribuée et son exigence d'industrialisation.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Nous tenons également à remercier chaleureusement notre encadrant pédagogique à l'<b>EMSI Marrakech</b>, pour ses orientations méthodologiques rigoureuses, "
        "ses relectures attentives et son soutien tout au long de la rédaction de ce mémoire.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Enfin, nous remercions respectueusement les membres du jury pour l'honneur qu'ils nous font en acceptant d'évaluer ce travail de projet de fin d'année.",
        styles['Body']
    ))
    story.append(PageBreak())
    
    # ── IV. RÉSUMÉ (PAGE UNIQUE DÉDIÉE) ─────────────────────────────────────
    story.append(Paragraph("RÉSUMÉ", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    story.append(Paragraph(
        "Dans un secteur touristique marocain en forte expansion et engagé dans une transition numérique stratégique, la gestion informatisée "
        "des établissements hôteliers traditionnels et des Riads haut de gamme fait face à des défis opérationnels critiques : surréservations récurrentes "
        "lors des pics saisonniers, clôture nocturne (<i>Night Audit</i>) manuelle fastidieuse et source d'erreurs, application complexe de la réglementation "
        "fiscale marocaine (TVA à 10%, Taxe de Séjour communale TS à 25 MAD et Taxe de Promotion Touristique TPT à 12 MAD), et vulnérabilités de sécurité "
        "liées au partage des identifiants sur les postes de réception.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Ce mémoire d'ingénierie présente la conception, la modélisation formelle et la réalisation complète de la plateforme <b>PMS Alidentec Hospitality</b>, "
        "un progiciel hôtelier multi-établissements moderne fondé sur une architecture microservices distribuée cloud-native. Développée avec <b>Next.js 14</b> "
        "(App Router, Server Components, TypeScript) côté client et <b>Python 3.11 / FastAPI</b> côté backend, la solution orchestre <b>onze microservices autonomes</b> "
        "isolés selon le patron architectural <i>Database per Service</i>.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Parmi les innovations techniques majeures figurent : l'intégration de l'authentification biométrique sans mot de passe <b>WebAuthn / FIDO2</b> "
        "avec flux d'appairage dynamique par QR Code, un orchestrateur de verrous distribués sous <b>Redis</b> éliminant mathématiquement tout risque d'overbooking, "
        "un bus de messagerie asynchrone <b>RabbitMQ</b> assurant la réactivité temps réel des statuts de chambres pour le personnel d'étage (PWA Housekeeping), "
        "et un stockage objet immuable <b>MinIO S3</b> pour l'archivage sécurisé des rapports financiers d'audit. Les audits de qualité logicielle sous <b>SonarQube</b> "
        "(Quality Gate Passed) et les campagnes de tests unitaires sous <b>Pytest</b> (100% de succès) attestent du niveau d'industrialisation et de la haute fiabilité de la plateforme.",
        styles['Body']
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Mots-clés :</b> PMS Hôtelier, Architecture Microservices, FastAPI, Next.js 14, WebAuthn FIDO2, Redis Redlock, RabbitMQ, PostgreSQL, Fiscalité Marocaine, Night Audit, SonarQube, Qualité Logicielle.", styles['BodyBold']))
    story.append(PageBreak())
    
    # ── V. ABSTRACT (PAGE UNIQUE DÉDIÉE) ────────────────────────────────────
    story.append(Paragraph("ABSTRACT", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    story.append(Paragraph(
        "In the rapidly expanding Moroccan hospitality sector, traditional boutique hotels and luxury Riads face major technological and operational hurdles: "
        "frequent overbooking collisions during peak tourist seasons, tedious and error-prone manual Night Audit closing procedures, strict compliance mandates "
        "with Moroccan fiscal regulations (10% hospitality VAT, municipal tourist tax TS at 25 MAD, and tourism promotion tax TPT at 12 MAD), and widespread "
        "credential-sharing vulnerabilities across front-desk reception terminals.",
        styles['Body']
    ))
    story.append(Paragraph(
        "This master engineering thesis details the formal design, distributed architecture, and industrial implementation of the <b>PMS Alidentec Hospitality</b> "
        "platform, an enterprise-grade cloud-native multi-property property management system. Built using <b>Next.js 14</b> (React 18, TypeScript) for the rich frontend "
        "and <b>Python 3.11 / FastAPI</b> for the backend, the platform deploys <b>eleven autonomous microservices</b> strictly adhering to the <i>Database per Service</i> "
        "architectural pattern.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Key engineering achievements include: passwordless biometric authentication via the <b>WebAuthn / FIDO2</b> standard with dynamic QR code handoff, "
        "high-concurrency distributed lock orchestration with <b>Redis</b> completely eliminating double-booking hazards, an event-driven <b>RabbitMQ</b> messaging bus "
        "enabling instantaneous room housekeeping status synchronization across mobile Progressive Web Apps (PWA), and tamper-proof <b>MinIO S3</b> object storage "
        "for financial night audit immutable ledgers. Rigorous automated testing via <b>Pytest</b> (10/10 suites passed) and static code inspection under <b>SonarQube</b> "
        "(Quality Gate Passed, zero security vulnerabilities) certify the industrial robustness, security, and scalability of the delivered software solution.",
        styles['Body']
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Keywords :</b> Property Management System (PMS), Microservices Architecture, FastAPI, Next.js 14, WebAuthn FIDO2, Redis Distributed Locks, RabbitMQ, PostgreSQL, Moroccan Hospitality Taxes, Night Audit, SonarQube, Software Quality.", styles['BodyBold']))
    story.append(PageBreak())
    
    # ── VI. GLOSSAIRE TECHNIQUE ET MÉTIER ────────────────────────────────────
    story.append(Paragraph("GLOSSAIRE TECHNIQUE ET MÉTIER", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    glossary_data = [
        ["Sigle / Terme", "Signification Complète & Définition dans le Contexte PMS"],
        ["PMS", "Property Management System : Progiciel central de gestion hôtelière pilotant réservations, chambres, facturation et clôtures."],
        ["OTA", "Online Travel Agency : Agences de voyage en ligne tierces (ex. Booking.com, Airbnb, Expedia) connectées par API."],
        ["WebAuthn / FIDO2", "Standard W3C de cryptographie asymétrique permettant l'authentification biométrique sans mot de passe."],
        ["Night Audit", "Clôture journalière nocturne automatisée vérifiant les arrivées/départs, imputant les nuitées et avançant la Business Date."],
        ["Folio", "Compte financier individualisé d'une réservation enregistrant l'ensemble des débits (nuitées, extras) et règlements."],
        ["Tape Chart", "Planning matriciel interactif représentant l'occupation des chambres dans le temps avec manipulation Drag & Drop."],
        ["Room Shift", "Opération de réassignation d'un client vers une autre chambre en cours de séjour avec régularisation financière."],
        ["TS / TPT", "Taxe de Séjour communale (25 MAD/adulte/nuit) et Taxe de Promotion Touristique (12 MAD/adulte/nuit) au Maroc."],
        ["RevPAR", "Revenue Per Available Room : Indicateur de performance financière clé calculé par <code>RevPAR = Taux_Occupation &times; ADR</code>."],
        ["ADR", "Average Daily Rate : Prix moyen d'une chambre louée au cours d'une journée d'exploitation."],
        ["DDD", "Domain-Driven Design : Méthode de conception logicielle guidée par le domaine métier et le découpage en Bounded Contexts."],
        ["AMQP", "Advanced Message Queuing Protocol : Protocole standard de messagerie asynchrone utilisé par RabbitMQ."],
        ["JWT", "JSON Web Token : Jeton d'authentification compact signé cryptographiquement en RS256 contenant les rôles RBAC."],
        ["PWA", "Progressive Web App : Application web installable sur smartphone offrant des fonctionnalités proches du natif hors store."],
        ["RBAC", "Role-Based Access Control : Modèle de sécurité régissant les droits d'accès selon le rôle attribué à l'utilisateur."],
        ["S3", "Simple Storage Service : Standard d'API de stockage objet cloud implémenté localement par la solution MinIO."],
        ["TTL", "Time-To-Live : Durée de validité temporelle d'une clé ou d'un verrou dans le cache en mémoire Redis."],
        ["Quality Gate", "Seuil d'exigence de qualité de code SonarQube bloquant la mise en production en cas de vulnérabilité."]
    ]
    t_glo = Table([[Paragraph(f"<b>{r[0]}</b>", styles['TblCellBold']), Paragraph(r[1], styles['TblCell'])] for r in glossary_data],
                  colWidths=[usable_width * 0.25, usable_width * 0.75])
    t_glo.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#D0D7DE')),
        ('BACKGROUND', (0,0), (-1,0), c_light_bg)
    ]))
    story.append(t_glo)
    story.append(PageBreak())
    
    # ── VII. TABLE DES MATIÈRES ──────────────────────────────────────────────
    story.append(Paragraph("TABLE DES MATIÈRES", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    toc_entries = [
        ("Dédicace", "I", True),
        ("Remerciements", "II", True),
        ("Résumé", "III", True),
        ("Abstract", "IV", True),
        ("Glossaire Technique et Métier", "V", True),
        ("Table des Matières", "VI", True),
        ("Liste des Figures", "VIII", True),
        ("Liste des Tableaux", "IX", True),
        ("INTRODUCTION GÉNÉRALE", "1", True),
        ("CHAPITRE 1 : PRÉSENTATION DE L'ENTREPRISE ET CADRE DU PROJET", "2", True),
        ("  1.1 Introduction", "3", False),
        ("  1.2 Présentation de l'Organisme d'Accueil (Alidentec)", "3", False),
        ("  1.3 Présentation du Cadre Institutionnel (EMSI) et du Stage", "4", False),
        ("  1.4 Immersion Métier & Présentation du Projet Hôtelier", "5", False),
        ("  1.5 Méthodologie de Conduite de Projet (Agile Scrum)", "6", False),
        ("  1.6 Planification Temporelle et Diagramme de Gantt", "7", False),
        ("  1.7 Conclusion du Chapitre", "8", False),
        ("CHAPITRE 2 : ANALYSE DES BESOINS ET MODÉLISATION DU SYSTÈME", "9", True),
        ("  2.1 Introduction", "10", False),
        ("  2.2 Étude et Critique de l'Existant Hôtelier", "10", False),
        ("  2.3 Solution Proposée et Objectifs Stratégiques", "12", False),
        ("  2.4 Identification et Rôles des Acteurs (Matrice RACI)", "13", False),
        ("  2.5 Spécification Détaillée des Besoins Fonctionnels", "14", False),
        ("  2.6 Spécification des Besoins Non-Fonctionnels", "16", False),
        ("  2.7 Modélisation UML des Cas d'Utilisation (3 Diagrammes UC)", "17", False),
        ("  2.8 Modélisation UML Dynamique (3 Diagrammes de Séquence)", "20", False),
        ("  2.9 Modélisation UML Structurelle (Diagramme de Classes Métier)", "22", False),
        ("  2.10 Architecture Fonctionnelle et Découpage DDD", "23", False),
        ("  2.11 Conclusion du Chapitre", "23", False),
        ("CHAPITRE 3 : CONCEPTION TECHNIQUE ET TECHNOLOGIES", "24", True),
        ("  3.1 Introduction", "25", False),
        ("  3.2 Architecture Technique Globale 4 Tiers", "25", False),
        ("  3.3 Architecture Logicielle Microservices & Pattern Database per Service", "26", False),
        ("  3.4 Écosystème Technologique Frontend (Next.js 14, TypeScript, PWA)", "28", False),
        ("  3.5 Écosystème Technologique Backend (Python 3.11, FastAPI, SQLAlchemy)", "29", False),
        ("  3.6 Persistance, Cache Distribué et Messagerie (PostgreSQL, Redis, RabbitMQ, MinIO)", "30", False),
        ("  3.7 Sécurité Périmétrique et Gestion des Identités (Keycloak, WebAuthn, JWT)", "31", False),
        ("  3.8 Outils de Développement et Industrialisation DevOps", "32", False),
        ("  3.9 Spécification des Contrats d'API RESTful et Codes HTTP", "33", False),
        ("  3.10 Conclusion du Chapitre", "34", False),
        ("CHAPITRE 4 : RÉALISATION ET PRÉSENTATION DES INTERFACES", "32", True),
        ("  4.1 Introduction", "33", False),
        ("  4.2 Mise en Place de l'Environnement de Développement Conteneurisé", "33", False),
        ("  4.3 Développement Backend et Implémentation des Algorithmes Clés", "34", False),
        ("  4.4 Développement Frontend et Composants Riches", "35", False),
        ("  4.5 Présentation Détaillée des 10 Interfaces Utilisateurs du Projet", "36", False),
        ("  4.6 Intégration Globale des Composants", "45", False),
        ("  4.7 Bilan des Contributions Individuelles de l'Équipe", "46", False),
        ("  4.8 Difficultés Techniques Rencontrées et Solutions d'Ingénierie", "47", False),
        ("  4.9 Conclusion du Chapitre", "47", False),
        ("CHAPITRE 5 : TESTS, VALIDATION ET QUALITÉ LOGICIELLE", "48", True),
        ("  5.1 Introduction", "49", False),
        ("  5.2 Stratégie Globale d'Assurance Qualité (Pyramide des Tests)", "49", False),
        ("  5.3 Suites de Tests Unitaires sous Pytest (10/10 Validées)", "50", False),
        ("  5.4 Tests d'Intégration des Microservices et Intergiciels", "51", False),
        ("  5.5 Tests de Contrats d'API REST avec Postman", "52", False),
        ("  5.6 Tests Fonctionnels et Parcours End-to-End (Playwright)", "52", False),
        ("  5.7 Tests de Charge et Analyse de Performance Concurrente", "53", False),
        ("  5.8 Tests de Sécurité et Audit de Vulnérabilités (OWASP)", "54", False),
        ("  5.9 Audit de Qualité de Code sous SonarQube (Quality Gate Passed)", "54", False),
        ("  5.10 Conclusion du Chapitre", "55", False),
        ("CHAPITRE 6 : BILAN DU STAGE ET APPORTS D'INGÉNIERIE", "55", True),
        ("  6.1 Introduction", "56", False),
        ("  6.2 Apports Techniques et Maîtrise du Cloud-Native", "56", False),
        ("  6.3 Apports Professionnels et Immersion Métier chez Alidentec", "57", False),
        ("  6.4 Enseignements Organisationnels et Gestion Agile en Trinôme", "57", False),
        ("  6.5 Matrice des Compétences d'Ingénieur Développées", "58", False),
        ("  6.6 Contributions Personnelles de Chaque Élève-Ingénieur", "58", False),
        ("  6.7 Perspectives d'Évolution et Roadmap Future", "59", False),
        ("  6.8 Conclusion du Chapitre", "59", False),
        ("CONCLUSION GÉNÉRALE ET PERSPECTIVES", "59", True),
        ("BIBLIOGRAPHIE", "62", True),
        ("WEBOGRAPHIE", "62", True),
        ("ANNEXES TECHNIQUES", "63", True)
    ]
    
    t_toc_rows = []
    for title, page_str, is_major in toc_entries:
        st = styles['TocChap'] if is_major else styles['TocItem']
        t_toc_rows.append([Paragraph(title, st), Paragraph(page_str, styles['TblCellCenter'])])
        
    t_toc = Table(t_toc_rows, colWidths=[usable_width * 0.88, usable_width * 0.12])
    t_toc.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1.6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.6),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, HexColor('#EAEAEA'))
    ]))
    story.append(t_toc)
    story.append(PageBreak())
    
    # ── IX. LISTE DES FIGURES ─────────────────────────────────────────────
    story.append(Paragraph("LISTE DES FIGURES", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    lof_data = [
        ["Figure 1-1", "Planning de Gantt des 8 Sprints de développement du projet PMS", "7"],
        ["Figure 2-1", "Diagramme de Cas d'Utilisation Global du système PMS Alidentec", "17"],
        ["Figure 2-2", "Diagramme de Cas d'Utilisation : Module Réservation et Front-Office", "18"],
        ["Figure 2-3", "Diagramme de Cas d'Utilisation : Module Housekeeping et Administration", "19"],
        ["Figure 2-4", "Diagramme de Séquence UML : Authentification sans mot de passe WebAuthn", "20"],
        ["Figure 2-5", "Diagramme de Séquence UML : Création de Réservation avec verrou Redis", "21"],
        ["Figure 2-6", "Diagramme de Séquence UML : Clôture journalière nocturne (Night Audit)", "22"],
        ["Figure 2-7", "Diagramme de Classes UML du domaine métier hôtelier (4 Bounded Contexts)", "22"],
        ["Figure 3-1", "Architecture Technique Globale 4 Tiers des Microservices PMS Alidentec", "25"],
        ["Figure 4-1", "Interface 1 : Tableau de bord principal d'accueil et d'exploitation du PMS", "36"],
        ["Figure 4-2", "Interface 2 : Formulaire complet de création et tarification dynamique", "37"],
        ["Figure 4-3", "Interface 3 : Enregistrement de Check-in voyageur et conformité réglementaire", "38"],
        ["Figure 4-4", "Interface 4 : Facturation et gestion des Folios clients avec calcul fiscal", "39"],
        ["Figure 4-5", "Interface 5 : Modal d'imputation d'une consommation extra (Restaurant / Spa)", "40"],
        ["Figure 4-6", "Interface 6 : Module de clôture journalière automatisée (Night Audit)", "41"],
        ["Figure 4-7", "Interface 7 : Progressive Web App mobile pour le Housekeeping", "42"],
        ["Figure 4-8", "Interface 8 : Console de configuration multi-établissements (Riads du groupe)", "43"],
        ["Figure 4-9", "Interface 9 : Répertoire CRM unifié des profils voyageurs et segmentation VIP", "44"],
        ["Figure 4-10", "Interface 10 : Terminal d'appairage biométrique sans mot de passe WebAuthn", "45"],
        ["Figure 5-1", "Rapport officiel d'exécution des tests unitaires backend sous Pytest (10/10 validées)", "50"],
        ["Figure 5-2", "Dashboard interactif d'audit de qualité et de sécurité SonarQube (Quality Gate Passed)", "54"]
    ]
    t_lof = Table([[Paragraph(f"<b>{r[0]}</b>", styles['TblCellBold']), Paragraph(r[1], styles['TblCell']), Paragraph(r[2], styles['TblCellCenter'])] for r in lof_data],
                  colWidths=[usable_width * 0.16, usable_width * 0.74, usable_width * 0.10])
    t_lof.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.4, HexColor('#D0D7DE'))
    ]))
    story.append(t_lof)
    story.append(PageBreak())
    
    # ── X. LISTE DES TABLEAUX ──────────────────────────────────────────────
    story.append(Paragraph("LISTE DES TABLEAUX", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    lot_data = [
        ["Tableau 1-1", "Fiche signalétique et d'identité de l'entreprise Alidentec", "3"],
        ["Tableau 1-2", "Calendrier prévisionnel et jalons majeurs des 8 sprints Scrum", "6"],
        ["Tableau 2-1", "Matrice comparative critique de l'existant hôtelier et apports PMS Alidentec", "11"],
        ["Tableau 2-2", "Matrice RACI des responsabilités par acteur opérationnel", "13"],
        ["Tableau 2-3", "Exigences non-fonctionnelles et métriques de validation", "16"],
        ["Tableau 2-4", "Description textuelle normée du Cas d'Utilisation UC-01 : Créer une Réservation", "17"],
        ["Tableau 2-5", "Description textuelle normée du Cas d'Utilisation UC-02 : Enregistrer le Check-in", "18"],
        ["Tableau 2-6", "Description textuelle normée du Cas d'Utilisation UC-03 : Clôturer le Night Audit", "19"],
        ["Tableau 3-1", "Cartographie détaillée des 11 microservices backend et bases associées", "27"],
        ["Tableau 3-2", "Matrice de justification technologique et sélection des outils d'ingénierie", "32"],
        ["Tableau 3-3", "Spécification des endpoints d'API REST critiques et codes de statut HTTP", "33"],
        ["Tableau 4-1", "Répartition détaillée des contributions d'ingénierie au sein du trinôme", "46"],
        ["Tableau 4-2", "Synthèse des défis techniques rencontrés et solutions d'ingénierie apportées", "47"],
        ["Tableau 5-1", "Matrice de la pyramide des tests et couverture d'assurance qualité", "49"],
        ["Tableau 5-2", "Détail des suites de tests unitaires critiques validées sous Pytest", "51"],
        ["Tableau 5-3", "Bilan comparatif des temps de réponse et performances avant/après optimisation", "53"],
        ["Tableau 6-1", "Matrice d'évaluation des compétences d'ingénierie acquises lors du stage", "58"],
        ["Tableau A-1", "Inventaire des suites de test du Riad pilote (Fixtures de référence)", "63"]
    ]
    t_lot = Table([[Paragraph(f"<b>{r[0]}</b>", styles['TblCellBold']), Paragraph(r[1], styles['TblCell']), Paragraph(r[2], styles['TblCellCenter'])] for r in lot_data],
                  colWidths=[usable_width * 0.16, usable_width * 0.74, usable_width * 0.10])
    t_lot.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('GRID', (0,0), (-1,-1), 0.4, HexColor('#D0D7DE'))
    ]))
    story.append(t_lot)
    story.append(PageBreak())
    
    return story
