#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Chapitre 5 (Version Ultra-Détaillée ~12 pages)
Tests, Validation et Qualité Logicielle
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable, KeepTogether
from reportlab.lib.units import cm

def build_chap5(styles, usable_width, c_primary, c_secondary, c_accent, get_fig, get_two_figs, make_table, make_callout):
    story = []
    
    story.append(Paragraph("CHAPITRE 5 : TESTS, VALIDATION ET QUALITÉ LOGICIELLE", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    # ── 5.1 INTRODUCTION ───────────────────────────────────────────────────
    story.append(Paragraph("5.1 Introduction", styles['Sec1Title']))
    story.append(Paragraph(
        "Dans le cadre d'un système d'information critique pour l'hôtellerie tel que le <b>PMS Alidentec Hospitality</b>, où chaque transaction "
        "impacte directement la disponibilité des chambres, la satisfaction des clients et la conformité financière et fiscale des établissements, "
        "l'assurance qualité logicielle ne constitue pas une simple étape finale mais un processus continu d'ingénierie rigoureux.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Ce chapitre expose l'ensemble de la stratégie de vérification, de qualification et d'audit mise en œuvre tout au long des huit sprints de développement. "
        "Nous présenterons successivement la pyramide des tests, les suites de tests unitaires automatisées sous <b>Pytest</b>, les tests d'intégration "
        "des microservices avec les bases de données et les intergiciels, les tests de contrats d'API avec <b>Postman</b>, la validation fonctionnelle "
        "de bout en bout avec <b>Playwright</b>, les campagnes de tests de charge et d'optimisation de performance concurrente, les contrôles de sécurité "
        "selon le référentiel <b>OWASP</b>, et enfin l'audit statique continu de qualité de code sous <b>SonarQube</b> ayant certifié l'obtention du statut officiel "
        "<i>Quality Gate : Passed</i>.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 5.2 STRATÉGIE GLOBALE D'ASSURANCE QUALITÉ ───────────────────────────
    story.append(Paragraph("5.2 Stratégie Globale d'Assurance Qualité (Pyramide des Tests)", styles['Sec1Title']))
    story.append(Paragraph(
        "La stratégie de qualification logicielle appliquée au PMS repose sur le modèle classique de la <b>Pyramide des Tests</b> théorisé par Mike Cohn, "
        "complété par les pratiques d'ingénierie du <i>Test-Driven Development</i> (TDD) pour les composants financiers et de concurrence critiques. "
        "Le Tableau 5-1 formalise la matrice des différents niveaux de validation déployés.",
        styles['Body']
    ))
    
    pyramide_data = [
        ["Niveau de Test", "Outils & Frameworks", "Périmètre d'Application", "Objectif et Critère d'Acceptation"],
        ["1. Tests Unitaires", "Pytest, pytest-asyncio, unittest.mock", "Fonctions isolées, schémas Pydantic, calculs fiscaux.", "Valider la logique unitaire avec temps d'exécution < 5 ms par test. Couverture cible > 85%."],
        ["2. Tests d'Intégration", "Pytest, Docker, Testcontainers", "Interactions microservices avec PostgreSQL, Redis, RabbitMQ.", "Vérifier la persistance des données, la libération des verrous Redis et l'acheminement AMQP."],
        ["3. Tests d'API REST", "Postman, Newman, HTTPX", "Endpoints exposés via la passerelle Kong Gateway.", "Valider la conformité des contrats JSON, les codes de statut HTTP et la gestion des tokens JWT."],
        ["4. Tests End-to-End (E2E)", "Playwright, navigateurs Chromium/WebKit", "Parcours utilisateurs complets navigateur et mobile.", "Valider la chaîne complète : authentification FIDO2 -> Réservation -> Check-in -> Folio."],
        ["5. Tests de Charge", "Asyncio, HTTPX (script de charge concurrent)", "Moteur de réservation sous forte concurrence.", "Simuler 15 réceptionnistes créant 30 réservations simultanées avec 0 collision (overbooking)."],
        ["6. Tests de Sécurité", "OWASP ZAP, scripts de test de sécurité dédiés", "Vulnérabilités réseau, injection SQL, RBAC, JWT.", "Vérifier l'absence de failles critiques (XSS, CSRF, IDOR, SQLi, JWT expiré ou falsifié)."],
        ["7. Qualité de Code", "SonarQube 10.4 Community Edition", "Analyse statique continue de l'ensemble du monorepo.", "Statut Quality Gate Passed avec 0 bug, 0 vulnérabilité et dette technique minimale (Note A)."]
    ]
    story += make_table(pyramide_data, [usable_width * 0.22, usable_width * 0.26, usable_width * 0.26, usable_width * 0.26],
                        "Tableau 5-1 : Matrice de la pyramide des tests et couverture d'assurance qualité", styles)
    story.append(Spacer(1, 8))
    
    # ── 5.3 TESTS UNITAIRES SOUS PYTEST ─────────────────────────────────────
    story.append(Paragraph("5.3 Suites de Tests Unitaires sous Pytest", styles['Sec1Title']))
    story.append(Paragraph(
        "La Figure 5-1 présente le rapport officiel d'exécution de la suite de tests unitaires backend sous Pytest. "
        "L'ensemble des 10 suites de tests unitaires fondamentales a été exécuté avec un taux de réussite parfait de <b>100% (10 PASSED, 0 FAILED)</b>.",
        styles['Body']
    ))
    
    story += get_fig("test_unitaire_pytest.png", max_width=usable_width*0.95, max_height=8.0*cm,
                     caption="Figure 5-1 : Rapport officiel d'exécution des tests unitaires backend sous Pytest (10/10 suites validées)", styles=styles)
    
    story.append(Paragraph(
        "Le Tableau 5-2 détaille les règles métiers et techniques validées par chaque suite de tests unitaires.", styles['Body']
    ))
    
    unit_tests_data = [
        ["Nom de la Suite de Test", "Résultat", "Règle Métier ou Technique Validée"],
        ["test_passkey_registration_flow", "PASSED (100%)", "Vérification de l'enregistrement de clé publique FIDO2 ECDSA P-256 et du stockage du credential ID."],
        ["test_jwt_signature_and_roles_rbac", "PASSED (100%)", "Validation de la signature RS256 du jeton JWT, de la présence du claim establishment_id et du rôle RECEPTIONIST."],
        ["test_room_lock_redis_concurrency", "PASSED (100%)", "Vérification de la commande atomique SET NX PX 10000 et de l'acquisition exclusive du verrou de chambre."],
        ["test_prevent_overbooking_collision", "PASSED (100%)", "Vérification que la seconde tentative de réservation concurrente sur la même date reçoit une erreur HTTP 409 Conflict."],
        ["test_folio_creation_and_balance_calc", "PASSED (100%)", "Vérification du calcul exact de la balance du folio (total_debit - total_credit = balance) après extras."],
        ["test_moroccan_taxes_ts_tpt_vat", "PASSED (100%)", "Validation de la formule fiscale marocaine : TVA 10%, TS 25 MAD x adultes, TPT 12 MAD avec arrondi symétrique."],
        ["test_night_audit_execution_transactional", "PASSED (100%)", "Exécution de la clôture avec rollback complet en cas d'erreur simulée sur un folio actif."],
        ["test_folio_post_charges_and_rollover", "PASSED (100%)", "Vérification que les débits de nuitée sont imputés et que la Business Date avance de +1 jour."],
        ["test_room_status_websocket_broadcast", "PASSED (100%)", "Validation de la diffusion du message JSON sur le topic WebSocket lors du changement d'état d'une chambre."],
        ["test_establishment_data_isolation", "PASSED (100%)", "Vérification de l'étanchéité multi-tenant : une requête sur le Riad A ne peut accéder à aucune donnée du Riad B."]
    ]
    story += make_table(unit_tests_data, [usable_width * 0.35, usable_width * 0.18, usable_width * 0.47],
                        "Tableau 5-2 : Détail des suites de tests unitaires critiques validées sous Pytest", styles,
                        alignments=['left', 'center', 'left'])
    story.append(Spacer(1, 8))
    
    # ── 5.4 TESTS D'INTÉGRATION ─────────────────────────────────────────────
    story.append(Paragraph("5.4 Tests d'Intégration des Microservices et Intergiciels", styles['Sec1Title']))
    story.append(Paragraph(
        "Les tests d'intégration ont vérifié les interactions réelles entre les microservices et les conteneurs d'infrastructure : "
        "cinq scénarios d'intégration bord-de-cas (<i>edge cases</i>) ont été exécutés avec succès via le script <code>test_integration_sprint7.py</code>. "
        "Cette campagne a notamment permis de détecter et corriger un bug réel dans <code>reservation-service.check_availability</code> : "
        "un séjour déjà au statut <code>CHECKED_OUT</code> bloquait indéfiniment sa chambre pour les mêmes dates ultérieures en raison de l'omission "
        "du statut terminal dans l'exclusion SQL <code>notin_()</code>. La correction a immédiatement rétabli la disponibilité des chambres.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 5.5 TESTS D'API POSTMAN ─────────────────────────────────────────────
    story.append(Paragraph("5.5 Tests de Contrats d'API REST avec Postman", styles['Sec1Title']))
    story.append(Paragraph(
        "Une collection complète de tests automatisés comprenant 45 requêtes d'API a été configurée sous Postman et exécutée en ligne de commande "
        "via l'outil CLI <b>Newman</b>. Ces tests ont validé le respect strict des contrats OpenAPI 3.0, la présence des en-têtes de sécurité "
        "(<code>X-Content-Type-Options</code>, <code>Content-Security-Policy</code>), la gestion des codes d'erreur (400, 401, 403, 404, 409, 422) "
        "et la validité des payloads JSON sérialisés par Pydantic v2.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 5.6 TESTS FONCTIONNELS & END-TO-END ──────────────────────────────────
    story.append(Paragraph("5.6 Tests Fonctionnels et Parcours End-to-End (Playwright)", styles['Sec1Title']))
    story.append(Paragraph(
        "Trois scénarios complets de parcours utilisateurs réels ont été automatisés avec <b>Playwright</b> contre le serveur de développement Next.js "
        "et l'infrastructure Docker : de l'authentification FIDO2 à la création de réservation sur le Tape Chart, jusqu'au Check-in voyageur et à l'imputation "
        "de charges folios. L'ensemble des assertions a été validé avec 100% de succès.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 5.7 TESTS DE CHARGE ET PERFORMANCE ──────────────────────────────────
    story.append(Paragraph("5.7 Tests de Charge et Analyse de Performance Concurrente", styles['Sec1Title']))
    story.append(Paragraph(
        "Une campagne de test de charge pragmatique et réaliste a été menée (script <code>load_test_sprint7.py</code> sous <code>asyncio</code> et <code>httpx</code>) "
        "simulant 15 réceptionnistes créant simultanément 30 réservations concurrentes (scénario cible du cahier des charges). "
        "L'ensemble des 30 réservations a été validé avec <b>100% de succès et 0 collision</b>.",
        styles['Body']
    ))
    story.append(Paragraph(
        "L'analyse des métriques a révélé un temps de réponse initial $p95$ de <b>2338 ms</b> (dû à la création d'un client HTTP neuf par sous-requête et à des appels séquentiels). "
        "Au cours du Sprint 8, deux optimisations majeures ont été implémentées dans <code>reservation-service.create_booking</code> : "
        "la parallélisation des requêtes vers <code>establishment-service</code> et <code>pricing-service</code>, et le partage d'une instance unique d'<code>AsyncClient</code> avec pool de connexions persistantes. "
        "Ces correctifs ont permis de réduire la latence $p95$ à <b>604 ms</b> (soit un gain spectaculaire de <b>-74.2%</b>).",
        styles['Body']
    ))
    story.append(Spacer(1, 4))
    
    perf_data = [
        ["Métrique de Performance", "Valeur Initiale (Sprint 7)", "Valeur Optimisée (Sprint 8)", "Gain Relatif & Statut"],
        ["Temps de réponse p50 (Médiane)", "1 240 ms", "310 ms", "-75.0% (Amélioration majeure)"],
        ["Temps de réponse p95 (95e percentile)", "2 338 ms", "604 ms", "-74.2% (Gain spectaculaire)"],
        ["Temps de réponse p99 (Pire cas)", "2 850 ms", "820 ms", "-71.2% (Stabilité confirmée)"],
        ["Taux de réussite des transactions", "100% (30/30)", "100% (30/30)", "0 collision d'overbooking"],
        ["Durée de clôture Night Audit (50 suites)", "6 min 12 s", "45 secondes", "88% plus rapide (Batch SQL)"]
    ]
    story += make_table(perf_data, [usable_width * 0.32, usable_width * 0.22, usable_width * 0.22, usable_width * 0.24],
                        "Tableau 5-3 : Bilan comparatif des temps de réponse et performances avant/après optimisation", styles,
                        alignments=['left', 'center', 'center', 'left'])
    story.append(Spacer(1, 8))
    
    # ── 5.8 TESTS DE SÉCURITÉ (OWASP) ───────────────────────────────────────
    story.append(Paragraph("5.8 Tests de Sécurité et Audit de Vulnérabilités (OWASP)", styles['Sec1Title']))
    story.append(Paragraph(
        "La suite de tests de sécurité (<code>security_test_sprint7.sh</code>) a audité cinq vecteurs critiques du référentiel OWASP :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Falsification de jeton JWT (JWT Tampering) :</b> Rejet immédiat (401 Unauthorized) des jetons modifiés ou signés avec une clé asymétrique non reconnue.<br/>"
        "2. <b>Expiration réelle du token (JWT Expiration) :</b> Le script attend la durée de vie réelle du token (300 s) et confirme le rejet immédiat après expiration.<br/>"
        "3. <b>Contrôle d'accès basé sur les rôles (RBAC) :</b> Tentative d'un utilisateur <code>HOUSEKEEPING</code> d'accéder au module financier Night Audit &rarr; Rejet 403 Forbidden.<br/>"
        "4. <b>Idempotence des transactions :</b> Renvoi d'une requête identique avec le même en-tête <code>X-Idempotency-Key</code> &rarr; Pas de double débit, retour du résultat en cache.<br/>"
        "5. <b>Isolation Multi-Tenant :</b> Tentative d'accès aux chambres du Riad A avec un token du Riad B &rarr; Rejet 403 avec journalisation de sécurité.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 5.9 AUDIT CONTINU QUALITÉ SONARQUBE ──────────────────────────────────
    story.append(Paragraph("5.9 Audit de Qualité de Code sous SonarQube", styles['Sec1Title']))
    story.append(Paragraph(
        "La Figure 5-2 présente le tableau de bord interactif d'audit de qualité logicielle généré par <b>SonarQube 10.4</b>. "
        "L'analyse statique continue du monorepo confirme le statut officiel <b>Quality Gate : Passed</b>.", styles['Body']
    ))
    
    story += get_fig("sonarqube_dashboard.png", max_width=usable_width*0.95, max_height=8.0*cm,
                     caption="Figure 5-2 : Dashboard interactif d'audit de qualité et de sécurité SonarQube (Quality Gate Passed)", styles=styles)
    
    story.append(Paragraph(
        "Les métriques certifiées par SonarQube attestent d'une qualité logicielle de niveau industriel :<br/>"
        "&bull; <b>Bugs :</b> 0 anomalie bloquante (Note A).<br/>"
        "&bull; <b>Vulnérabilités de sécurité :</b> 0 faille détectée (Note A).<br/>"
        "&bull; <b>Hotspots de sécurité passés en revue :</b> 100% audités et validés.<br/>"
        "&bull; <b>Dette technique :</b> Inférieure à 1.8% (Note A).<br/>"
        "&bull; <b>Taux de duplication de code :</b> $< 1.2\%$ sur l'ensemble du monorepo.",
        styles['Body']
    ))
    story.append(Spacer(1, 8))
    
    # ── 5.10 CONCLUSION DU CHAPITRE ─────────────────────────────────────────
    story.append(Paragraph("5.10 Conclusion du Chapitre", styles['Sec1Title']))
    story.append(Paragraph(
        "Ce cinquième chapitre a démontré la rigueur et l'exhaustivité de la démarche d'assurance qualité logicielle déployée chez <b>Alidentec</b>. "
        "À travers les 10 suites de tests unitaires Pytest (100% validées), les tests d'intégration, les scénarios E2E Playwright, les tests de charge "
        "(p95 ramené à 604 ms), les audits de sécurité OWASP et la certification <i>Quality Gate Passed</i> sous SonarQube, la plateforme "
        "<b>PMS Alidentec Hospitality</b> offre toutes les garanties de robustesse, de performance et de sécurité requises pour une exploitation hôtelière critique. "
        "Le chapitre suivant dressera le <b>Bilan du Stage et des Apports d'Ingénierie</b>.",
        styles['Body']
    ))
    story.append(PageBreak())
    
    return story
