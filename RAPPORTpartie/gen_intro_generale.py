#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Introduction Générale
Contexte économique et touristique marocain, problématique des PMS traditionnels,
objectifs stratégiques de la solution Alidentec et annonce détaillée du plan du mémoire.
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable, Table, TableStyle
from reportlab.lib.colors import HexColor

C_VERT_PRAIRIE = HexColor('#2E7D32')       # Vert prairie
C_VERT_PRAIRIE_BG = HexColor('#E8F5E9')

def build_intro_generale(styles, usable_width, c_primary, c_secondary, c_accent):
    story = []
    
    # ── TITRE INTRODUCTION GÉNÉRALE ─────────────────────────────────────────
    story.append(Paragraph("INTRODUCTION GÉNÉRALE", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_VERT_PRAIRIE, spaceBefore=4, spaceAfter=14))
    
    # ── 1. CONTEXTE GLOBAL ET ÉCONOMIQUE ─────────────────────────────────────
    story.append(Paragraph("<b>1. Contexte Économique et Mutation du Secteur Touristique Marocain</b>", styles['Sec2Title']))
    story.append(Paragraph(
        "Pilier stratégique de l'économie du Royaume du Maroc, l'industrie touristique connaît une dynamique de croissance "
        "exceptionnelle portée par la feuille de route nationale 2023-2026 et les préparatifs d'envergure mondiale liés à l'organisation "
        "conjointe de la Coupe du Monde de la FIFA 2030. Au cœur de cette dynamique, la ville de Marrakech s'impose comme la première destination "
        "touristique du pays, caractérisée par un écosystème d'hébergement haut de gamme singulier dominé par les <b>Riads traditionnels de la Médina</b> "
        "et les boutiques-hôtels de charme.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Ces établissements d'exception, alliant architecture patrimoniale et hospitalité personnalisée, font face à des exigences de gestion "
        "de plus en plus complexes. La fidélisation d'une clientèle internationale exigeante requiert une fluidité opérationnelle irréprochable, "
        "de la réservation en ligne jusqu'au départ du voyageur, ainsi qu'une conformité stricte avec les dispositions légales, réglementaires et fiscales marocaines.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 2. PROBLÉMATIQUE ET VERROUS TECHNOLOGIQUES ───────────────────────────
    story.append(Paragraph("<b>2. Problématique Métier et Limites des Systèmes Existants</b>", styles['Sec2Title']))
    story.append(Paragraph(
        "Malgré cette sophistication de l'offre d'hébergement, la gestion quotidienne d'un grand nombre de Riads et d'hôtels indépendants repose encore "
        "sur des outils informatiques obsolètes, hétérogènes ou monolithiques. L'audit approfondi mené sur le terrain a mis en exergue quatre verrous majeurs :",
        styles['Body']
    ))
    story.append(Paragraph(
        "&bull; <b>Surréservations récurrentes (Overbooking) :</b> Lors des pics de fréquentation, la synchronisation lente et asynchrone entre les réceptions et les agences de voyage en ligne (OTAs telles que Booking.com ou Airbnb) provoque des conflits de réservation sur les mêmes suites.<br/>"
        "&bull; <b>Lenteur et erreurs de la clôture journalière (Night Audit) :</b> L'exécution manuelle ou séquentielle du Night Audit engendre des temps de traitement excessifs (souvent plus d'une heure) et des dérives sur le calcul des taxes réglementaires marocaines (TVA 10%, Taxe de Séjour communale TS et Taxe de Promotion Touristique TPT).<br/>"
        "&bull; <b>Vulnérabilités de sécurité sur les postes partagés :</b> Le partage d'identifiants et de mots de passe génériques entre réceptionnistes travaillant par roulement crée des risques critiques de fuite de données et d'usurpation d'identité.<br/>"
        "&bull; <b>Rupture de communication avec les équipes d'étage :</b> L'absence de synchronisation temps réel entre le front-office et les smartphones des gouvernantes retarde l'attribution des chambres nettoyées aux nouveaux arrivants.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 6))
    
    # ── 3. OBJECTIFS STRATÉGIQUES DU PROJET PMS ALIDENTEC ────────────────────
    story.append(Paragraph("<b>3. Objectifs et Apports de la Solution Développée chez Alidentec</b>", styles['Sec2Title']))
    story.append(Paragraph(
        "Dans ce contexte, notre projet de fin d'année réalisé au sein de l'entreprise <b>Alidentec</b> a consisté à concevoir, développer et qualifier "
        "industriellement la plateforme <b>PMS Alidentec Hospitality</b>. L'objectif fondamental est de doter les gestionnaires hôteliers d'un progiciel "
        "cloud-native de nouvelle génération, fondé sur une architecture microservices distribuée et hautement résiliente.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Les innovations clés apportées par notre solution comprennent :<br/>"
        "1. Une architecture en <b>11 microservices FastAPI</b> selon le patron <i>Database per Service</i> avec passerelle <b>Kong API Gateway</b>.<br/>"
        "2. Une authentification biométrique sans mot de passe <b>WebAuthn / FIDO2</b> par flux QR Code dynamique via <b>Keycloak</b>.<br/>"
        "3. Un mécanisme de verrouillage distribué atomique sous <b>Redis 7</b> garantissant zéro surréservation.<br/>"
        "4. Un moteur de clôture Night Audit transactionnel asynchrone réduisant la durée de traitement à <b>45 secondes pour 50 suites</b>.<br/>"
        "5. Une interface riche sous <b>Next.js 14</b> avec planning interactif Tape Chart et Progressive Web App (PWA) pour le Housekeeping.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 4. STRUCTURE ET ANNONCE DU PLAN DU MÉMOIRE ───────────────────────────
    story.append(Paragraph("<b>4. Structure et Organisation du Mémoire</b>", styles['Sec2Title']))
    story.append(Paragraph(
        "Afin de rendre compte de manière rigoureuse de notre démarche d'ingénierie, ce mémoire s'articule en <b>six chapitres complémentaires</b> :",
        styles['Body']
    ))
    
    plan_data = [
        [Paragraph("<b>Chapitre 1 : Présentation de l'Entreprise et Cadre du Projet</b>", styles['TblCellBold']),
         Paragraph("Présente l'organisme d'accueil Alidentec, le cadre institutionnel de l'EMSI, l'immersion sur le terrain hôtelier, la méthodologie Agile Scrum et le planning de Gantt.", styles['TblCell'])],
        [Paragraph("<b>Chapitre 2 : Analyse des Besoins et Modélisation du Système</b>", styles['TblCellBold']),
         Paragraph("Détaille l'étude critique de l'existant, la matrice RACI, les spécifications fonctionnelles/non-fonctionnelles, les diagrammes UML (3 UC, 3 Séquences, Classes) et le Domain-Driven Design.", styles['TblCell'])],
        [Paragraph("<b>Chapitre 3 : Conception Technique et Technologies</b>", styles['TblCellBold']),
         Paragraph("Expose l'architecture 4 tiers, la cartographie des 11 microservices, les choix technologiques (Next.js 14, FastAPI, PostgreSQL, Redis, RabbitMQ, MinIO) et la sécurité Keycloak.", styles['TblCell'])],
        [Paragraph("<b>Chapitre 4 : Réalisation et Présentation des Interfaces</b>", styles['TblCellBold']),
         Paragraph("Décrit l'environnement conteneurisé Docker, les algorithmes métiers (fiscalité, clôture, verrous), la présentation des 10 interfaces clés du projet et les contributions individuelles.", styles['TblCell'])],
        [Paragraph("<b>Chapitre 5 : Tests, Validation et Qualité Logicielle</b>", styles['TblCellBold']),
         Paragraph("Présente la pyramide des tests, les 10 suites Pytest validées (100%), les tests E2E Playwright, les tests de charge (gain de latence de -74%) et l'audit SonarQube Quality Gate Passed.", styles['TblCell'])],
        [Paragraph("<b>Chapitre 6 : Bilan du Stage et Apports d'Ingénierie</b>", styles['TblCellBold']),
         Paragraph("Dresse le bilan réflexif des compétences acquises, les leçons de gestion de projet en trinôme et la roadmap des perspectives d'évolution future.", styles['TblCell'])]
    ]
    t_plan = Table(plan_data, colWidths=[usable_width * 0.35, usable_width * 0.65])
    t_plan.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.4, HexColor('#D0D7DE')),
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#FAFAFA'))
    ]))
    story.append(t_plan)
    
    story.append(PageBreak())
    return story
