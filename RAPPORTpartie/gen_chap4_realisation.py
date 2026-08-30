#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Chapitre 4 (Intégration des 10 Interfaces Clés du Projet - KeepTogether Total)
Réalisation et Présentation des Interfaces
Chaque interface, son titre, son texte introductif et sa capture sont scellés dans un KeepTogether unique.
"""

import os
from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable, KeepTogether
from reportlab.lib.units import cm

def build_chap4(styles, usable_width, c_primary, c_secondary, c_accent, get_fig, get_two_figs, make_table, make_callout):
    story = []
    
    story.append(Paragraph("CHAPITRE 4 : RÉALISATION ET PRÉSENTATION DES INTERFACES", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    # ── 4.1 INTRODUCTION ───────────────────────────────────────────────────
    story.append(Paragraph("4.1 Introduction", styles['Sec1Title']))
    story.append(Paragraph(
        "Ce quatrième chapitre constitue le cœur démonstratif de notre mémoire d'ingénierie. Il expose la concrétisation pratique "
        "de la plateforme <b>PMS Alidentec Hospitality</b> à travers la mise en place de l'infrastructure de développement, l'implémentation "
        "des algorithmes métiers fondamentaux au niveau du backend, et la présentation approfondie des <b>dix interfaces utilisateurs majeures</b> "
        "développées sous <b>Next.js 14</b> et testées en situation réelle d'exploitation hôtelière.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Nous débuterons par la description de l'environnement de développement conteneurisé sous Docker. Nous détaillerons ensuite les algorithmes "
        "clés du système : le moteur de calcul fiscal marocain certifié (TVA 10%, TS 25 MAD, TPT 12 MAD), l'architecture asynchrone haute vitesse du Night Audit "
        "et le mécanisme de verrouillage distribué sous Redis. Nous présenterons ensuite en détail chacune des <b>dix interfaces opérationnelles fondamentales</b> "
        "du progiciel, avant de dresser le bilan des contributions d'ingénierie de notre équipe et la synthèse des défis techniques surmontés.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # ── 4.2 MISE EN PLACE DE L'ENVIRONNEMENT DE DÉVELOPPEMENT ────────────────
    story.append(Paragraph("4.2 Mise en Place de l'Environnement de Développement", styles['Sec1Title']))
    story.append(Paragraph(
        "L'infrastructure d'ingénierie au sein des laboratoires d'Alidentec a été conçue pour reproduire fidèlement les conditions de production cloud. "
        "L'environnement est entièrement orchestré par Docker Compose, articulé en 18 services conteneurisés interconnectés sur un réseau bridge privé :",
        styles['Body']
    ))
    story.append(Paragraph(
        "&bull; <b>Orchestration des 11 microservices FastAPI :</b> Chaque microservice dispose de son propre <code>Dockerfile</code> multi-stage basé sur <code>python:3.11-slim</code>, montant les volumes de code source pour permettre le Hot-Reloading instantané lors du développement.<br/>"
        "&bull; <b>Migrations de schémas relationnels sous Alembic :</b> À chaque démarrage, la commande <code>alembic upgrade head</code> est exécutée automatiquement pour synchroniser les tables, index et contraintes de clés étrangères avec les modèles SQLAlchemy 2.0.<br/>"
        "&bull; <b>Initialisation de la sécurité Keycloak :</b> Le script Python <code>keycloak_setup.py</code> provisionne le Realm <code>pms-alidentec</code>, enregistre les clients OIDC pour l'application web et configure les politiques RBAC.<br/>"
        "&bull; <b>Peuplement des données d'essai (Fixtures) :</b> Les scripts d'initialisation (<code>seed_sprint1.sh</code> à <code>seed_sprint5.sh</code>) injectent l'inventaire complet du Riad pilote (Riad Yasmine) : typologies de suites, équipements traditionnels, grilles tarifaires et comptes de démonstration.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 6))
    
    # ── 4.3 DÉVELOPPEMENT BACKEND ET ALGORITHMES CLÉS ────────────────────────
    story.append(Paragraph("4.3 Développement Backend et Implémentation des Algorithmes Clés", styles['Sec1Title']))
    
    story.append(Paragraph("4.3.1 Algorithme de calcul fiscal hôtelier marocain (TVA, TS, TPT)", styles['Sec2Title']))
    story.append(Paragraph(
        "L'intégration des règles fiscales marocaines applicables à l'hébergement touristique constitue un composant critique du moteur de facturation. "
        "Afin d'éliminer toute approximation sur les centimes propre aux nombres flottants natifs (type <code>float</code>), l'ensemble des montants financiers "
        "est manipulé à l'aide du type <code>Decimal</code> avec application de la politique d'arrondi bancaire symétrique <code>ROUND_HALF_EVEN</code>.",
        styles['Body']
    ))
    
    story += make_callout(
        "<b>Formules fiscales marocaines certifiées dans le PMS Alidentec :</b><br/>"
        "&bull; <b>Montant HT Nuitée :</b> <code>Montant_TTC_Nuitée / (1 + Taux_TVA)</code> où Taux_TVA = 0.10 (10% sur hébergement).<br/>"
        "&bull; <b>Taxe de Séjour Communale (TS) :</b> <code>TS = 25.00 MAD &times; Nombre_Adultes &times; Nombre_Nuitées</code> (taux Marrakech catégorie 5* / Riad de luxe).<br/>"
        "&bull; <b>Taxe de Promotion Touristique (TPT) :</b> <code>TPT = 12.00 MAD &times; Nombre_Adultes &times; Nombre_Nuitées</code>.<br/>"
        "&bull; <b>Total Facturé au Folio :</b> <code>Total = Montant_TTC_Nuitée + TS + TPT + Extras_TTC</code>.",
        "RÈGLES FISCALES HÔTELIÈRES DU ROYAUME DU MAROC", styles=styles
    )
    
    story.append(Paragraph("4.3.2 Moteur de clôture Night Audit asynchrone haute performance", styles['Sec2Title']))
    story.append(Paragraph(
        "Dans les PMS traditionnels, le Night Audit exécute une boucle séquentielle bloquante sur chaque chambre, entraînant des durées d'attente "
        "dépassant souvent une heure. L'équipe d'Alidentec a conçu un moteur entièrement asynchrone sous FastAPI exploitant les coroutines <code>asyncio.gather()</code> "
        "et les insertions en masse SQL (<i>Batch SQL Inserts</i>). Pour un établissement de 50 suites, l'ensemble des 50 folios actifs est traité, "
        "vérifié et imputé en <b>45 secondes chrono</b>, avec garantie d'un <code>ROLLBACK</code> intégral en cas de défaillance matérielle.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("4.3.3 Verrouillage distribué Redis anti-collision de réservation", styles['Sec2Title']))
    story.append(Paragraph(
        "Pour éliminer tout risque d'overbooking lorsqu'un réceptionniste et une plateforme OTA tentent de réserver la même chambre simultanément, "
        "le microservice <code>reservation-service</code> acquiert un verrou distribué atomique sous Redis avant toute écriture en base :",
        styles['Body']
    ))
    story.append(Paragraph(
        "<code>SET lock:room:{room_id}:{date_arrivee}_{date_depart} {uuid_session} NX PX 10000</code><br/>"
        "&bull; <code>NX</code> : Pose le verrou uniquement si la clé n'existe pas déjà (atomicité absolue).<br/>"
        "&bull; <code>PX 10000</code> : Assigne un bail temporel (TTL) de 10 secondes libérant automatiquement le verrou en cas de crash client.<br/>"
        "Si l'acquisition échoue (clé déjà existante), le système rejette immédiatement la requête avec un code <b>HTTP 409 Conflict</b>.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 8))
    
    # ── 4.4 DÉVELOPPEMENT FRONTEND ET COMPOSANTS RICHES ─────────────────────
    story.append(Paragraph("4.4 Développement Frontend et Composants Riches", styles['Sec1Title']))
    
    story.append(Paragraph("4.4.1 Planning interactif Tape Chart avec glisser-déposer", styles['Sec2Title']))
    story.append(Paragraph(
        "Le planning matriciel <i>Tape Chart</i> a été développé comme un composant React riche exploitant l'API <code>HTML5 Drag and Drop</code> "
        "et la bibliothèque <code>@dnd-kit</code>. Il permet aux réceptionnistes de visualiser d'un coup d'œil l'occupation du Riad, de modifier "
        "les dates d'un séjour par étirement horizontal du bloc, ou de changer la chambre assignée par simple glisser-déposer vertical (<i>Room Shift</i>), "
        "avec recalcul automatique instantané des montants financiers associés.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("4.4.2 Synchronisation temps réel par flux WebSockets", styles['Sec2Title']))
    story.append(Paragraph(
        "Pour maintenir une cohérence parfaite entre les postes de réception et les smartphones des gouvernantes, le frontend établit une connexion "
        "WebSocket permanente avec le microservice <code>notification-service</code>. Dès qu'une femme de chambre valide le nettoyage d'une suite sur sa PWA mobile, "
        "l'événement est acheminé via RabbitMQ et le Tape Chart de réception change instantanément de couleur (du rouge <code>DIRTY</code> au vert <code>CLEAN</code>) "
        "en moins de 500 millisecondes sans aucun rechargement de page.",
        styles['Body']
    ))
    story.append(Spacer(1, 8))
    
    # ── 4.5 PRÉSENTATION DÉTAILLÉE DES 10 INTERFACES UTILISATEURS DU PROJET ─
    story.append(Paragraph("4.5 Présentation Détaillée des 10 Interfaces Utilisateurs du Projet", styles['Sec1Title']))
    story.append(Paragraph(
        "Nous détaillons ci-après les <b>dix interfaces fondamentales</b> du système PMS Alidentec, illustrées par leurs captures réelles "
        "configurées à des dimensions uniformes et scellées avec leurs descriptions techniques respectives :",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # Helper for unified image inclusion with COMPLETE KeepTogether block
    def add_ui_section(num, title, img_file, caption, desc_points):
        p_title = Paragraph(f"4.5.{num} Interface {num} : {title}", styles['Sec2Title'])
        p_intro = Paragraph(
            f"La {caption.split(':')[0].strip()} illustre l'interface opérationnelle du module <i>{title}</i> de la plateforme PMS.",
            styles['Body']
        )
        fig_elements = get_fig(img_file, max_width=usable_width*0.92, max_height=7.2*cm, caption=caption, styles=styles)
        desc_text = "<b>Description ergonomique et technique de l'Interface :</b><br/>" + "<br/>".join([f"&bull; {p}" for p in desc_points])
        p_desc = Paragraph(desc_text, styles['Body'])
        
        # Scellement intégral Titre + Intro + Figure + Description
        block = [
            p_title,
            p_intro
        ] + fig_elements + [
            p_desc,
            Spacer(1, 8)
        ]
        return [KeepTogether(block)]

    # 1. TABLEAU DE BORD D'ACCUEIL
    story += add_ui_section(
        1, "Tableau de Bord Principal d'Accueil et d'Exploitation",
        "homepage.png",
        "Figure 4-1 : Interface 1 : Tableau de bord principal d'accueil et d'exploitation du PMS",
        [
            "<i>Indicateurs clés (KPI) :</i> Affichage dynamique du taux d'occupation journalier, du nombre d'arrivées prévues, des départs attendus et du chiffre d'affaires consolidé en temps réel.",
            "<i>Navigation modulaire :</i> Barre latérale ergonomique donnant accès direct aux 11 modules de la plateforme (Planning, Réservations, Check-in, Facturation, Housekeeping, Clôture).",
            "<i>Alertes opérationnelles :</i> Panneau d'alertes instantanées signalant les chambres en attente d'inspection et les soldes folios débiteurs."
        ]
    )
    
    # 2. CRÉATION DE RÉSERVATION
    story += add_ui_section(
        2, "Formulaire de Création et Tarification de Réservation",
        "reservation.png",
        "Figure 4-2 : Interface 2 : Formulaire complet de création et tarification dynamique de réservation",
        [
            "<i>Saisie guidée rapide :</i> Sélection des dates de séjour via un calendrier dynamique, choix de la typologie de suite et nombre d'occupants (adultes/enfants).",
            "<i>Calcul fiscal instantané :</i> Dès la sélection des dates, le moteur calcule la ventilation certifiée : Montant HT, TVA 10%, Taxe de Séjour communale (25 MAD) et TPT (12 MAD).",
            "<i>Verrouillage préventif Redis :</i> Acquisition automatique d'un verrou atomique (TTL 10s) interdisant toute réservation concurrente simultanée sur la même suite."
        ]
    )
    
    # 3. CHECK-IN VOYAGEUR
    story += add_ui_section(
        3, "Enregistrement de Check-in et Fiche de Police Réglementaire",
        "businescheckin.png",
        "Figure 4-3 : Interface 3 : Enregistrement de Check-in voyageur et conformité réglementaire",
        [
            "<i>Contrôle d'hygiène automatique :</i> Blocage préventif de l'attribution des clés si la suite n'est pas au statut <code>CLEAN</code> ou <code>INSPECTED</code> dans le service Housekeeping.",
            "<i>Fiche de police DGSN :</i> Saisie et vérification des pièces d'identité officielles (Passeport / CIN) avec génération instantanée du document conforme aux autorités marocaines.",
            "<i>Activation du séjour :</i> Basculement du statut à <code>IN_HOUSE</code> et ouverture du compte Folio financier rattaché."
        ]
    )
    
    # 4. FACTURATION & FOLIOS
    story += add_ui_section(
        4, "Compte Financier Folio Client et Grand Livre du Séjour",
        "folio_1.png",
        "Figure 4-4 : Interface 4 : Facturation et gestion des Folios clients avec calcul fiscal",
        [
            "<i>Ventilation des débits :</i> Imputation automatique des nuitées d'hébergement, des taxes de séjour et des consommations annexes enregistrées au cours du séjour.",
            "<i>Enregistrement des règlements :</i> Encaissement multi-moyens (carte bancaire CMI, espèces en Dirhams/Devises, virement) avec émission immédiate de reçu.",
            "<i>Contrôle de solde strict :</i> Affichage en grand de la balance nette (<code>Total Débits - Total Crédits</code>), le Check-out exigeant un solde strictement nul."
        ]
    )
    
    # 5. IMPUTATION CHARGE EXTRA
    story += add_ui_section(
        5, "Imputation d'une Consommation Extra sur le Folio",
        "ajouter_charge.png",
        "Figure 4-5 : Interface 5 : Fenêtre modale d'imputation d'une consommation extra (Restaurant / Spa)",
        [
            "<i>Catalogue de prestations :</i> Sélection rapide parmi les extras disponibles (Table d'hôtes marocaine, Hammam traditionnel, Navette aéroport, Blanchisserie).",
            "<i>Ventilation fiscale automatique :</i> Calcul séparé du montant HT et de la TVA correspondante avec mise à jour temps réel de la balance du folio.",
            "<i>Traçabilité totale :</i> Horodatage précis de l'imputation et enregistrement de l'identifiant du collaborateur émetteur dans l'audit log."
        ]
    )
    
    # 6. NIGHT AUDIT
    story += add_ui_section(
        6, "Module de Clôture Journalière Nocturne (Night Audit)",
        "06_module_cloture_journaliere_night_audit.png",
        "Figure 4-6 : Interface 6 : Module de clôture journalière automatisée (Night Audit)",
        [
            "<i>Vérifications préliminaires :</i> Contrôle automatique des flux du jour (arrivées enregistrées, départs réglés, traitement des no-shows).",
            "<i>Balance financière & fiscalité marocaine :</i> Vérification de l'équilibre Débits = Crédits (TVA 10%, Taxe de Séjour TS 25 MAD, TPT 12 MAD).",
            "<i>Traitement batch transactionnel & archivage S3 :</i> Exécution en 45 secondes avec génération de rapport immuable signé et incrémentation irréversible de la Business Date (+1 jour)."
        ]
    )
    
    # 7. PWA MOBILE HOUSEKEEPING
    story += add_ui_section(
        7, "Progressive Web App (PWA) Mobile pour le Housekeeping",
        "femme.jpeg",
        "Figure 4-7 : Interface 7 : Progressive Web App mobile pour la gouvernance et l'entretien des chambres",
        [
            "<i>Mobilité sur smartphone :</i> Application réactive installable sans store, optimisée pour un usage fluide par les femmes de chambre dans les étages des Riads.",
            "<i>Statuts visuels d'hygiène :</i> Mise à jour instantanée en un clic du statut d'une suite (<code>DIRTY</code> &rarr; <code>IN_PROGRESS</code> &rarr; <code>CLEAN</code>).",
            "<i>Synchronisation temps réel :</i> Propagation immédiate du changement d'état vers le Tape Chart de réception via WebSockets et RabbitMQ en moins de 500 ms."
        ]
    )
    
    # 8. GESTION MULTI-ÉTABLISSEMENTS
    story += add_ui_section(
        8, "Console de Gestion et Configuration Multi-Établissements",
        "etabli.png",
        "Figure 4-8 : Interface 8 : Console de configuration multi-établissements (Riads du groupe)",
        [
            "<i>Administration centralisée :</i> Configuration des différents Riads partenaires (Riad Yasmine, Riad Al Ksar) avec coordonnées, devises et fuseaux horaires.",
            "<i>Gestion de l'inventaire physique :</i> Paramétrage des suites, typologies (Royale, Junior, Deluxe), équipements traditionnels et capacités d'accueil.",
            "<i>Isolation multi-tenant :</i> Garantie d'étanchéité stricte des bases de données entre établissements via l'identifiant <code>establishment_id</code>."
        ]
    )
    
    # 9. CRM & PROFILS CLIENTS
    story += add_ui_section(
        9, "Répertoire CRM Unifié des Profils Clients et Voyageurs",
        "names.png",
        "Figure 4-9 : Interface 9 : Répertoire CRM unifié des profils voyageurs et segmentation VIP",
        [
            "<i>Fichier centralisé des clients :</i> Consultation de l'historique exhaustif des séjours passés, nationalités, coordonnées et pièces d'identité enregistrées.",
            "<i>Personnalisation de l'accueil :</i> Enregistrement des préférences spécifiques (régime alimentaire, chambre préférée, allergies, demandes particulières).",
            "<i>Segmentation VIP :</i> Attribution de statuts de fidélité permettant des surclassements automatiques et un accueil sur-mesure."
        ]
    )
    
    # 10. AUTHENTIFICATION PASSKEY QR
    story += add_ui_section(
        10, "Terminal d'Appairage Biométrique Sans Mot de Passe WebAuthn",
        "pms_link_qr.png",
        "Figure 4-10 : Interface 10 : Terminal d'appairage biométrique sans mot de passe WebAuthn par QR Code",
        [
            "<i>Sécurité Zero-Trust FIDO2 :</i> Affichage d'un QR Code dynamique unique chiffré permettant l'authentification sans mot de passe sur poste partagé.",
            "<i>Signature biométrique mobile :</i> Le réceptionniste scanne le QR Code avec son smartphone et valide la session par TouchID/FaceID en moins de 2 secondes.",
            "<i>Émission de token JWT RS256 :</i> Délivrance du jeton d'accès sécurisé sans qu'aucun secret ou mot de passe ne transite sur le réseau public."
        ]
    )
    
    # ── 4.6 INTÉGRATION GLOBALE DES COMPOSANTS ──────────────────────────────
    story.append(Paragraph("4.6 Intégration Globale des Composants", styles['Sec1Title']))
    story.append(Paragraph(
        "L'intégration complète de la plateforme a validé la chaîne de bout en bout : l'interface Next.js 14 dialogue de manière fluide avec la passerelle "
        "Kong Gateway, qui authentifie les jetons JWT Keycloak, route les appels vers les microservices FastAPI appropriés, persiste les données sous PostgreSQL "
        "et Redis, et propage les événements temps réel via le courtier RabbitMQ vers la PWA Housekeeping et les tableaux de bord de réception.",
        styles['Body']
    ))
    story.append(Spacer(1, 8))
    
    # ── 4.7 BILAN DES CONTRIBUTIONS INDIVIDUELLES ────────────────────────────
    story.append(Paragraph("4.7 Bilan des Contributions Individuelles de l'Équipe", styles['Sec1Title']))
    story.append(Paragraph(
        "Le Tableau 4-1 détaille la répartition équilibrée des responsabilités techniques et des réalisations logicielles majeures "
        "au sein de notre trinôme d'élèves-ingénieurs tout au long des 16 semaines de stage chez Alidentec.", styles['Body']
    ))
    
    contrib_data = [
        ["Élève-Ingénieur", "Domaines de Responsabilité", "Réalisations Logicielles Majeures"],
        ["Nabil BOUDARINE", "Architecture Système, Sécurité & Clôture", "Conception de l'architecture microservices globale, intégration de la passerelle Kong Gateway, sécurité Keycloak WebAuthn/FIDO2 avec flux QR Code, développement du moteur Night Audit asynchrone et archivage MinIO S3, conteneurisation Docker Compose."],
        ["Youssef OUIZZA", "Développement Frontend & Temps Réel", "Conception et développement de l'interface Next.js 14 (App Router, Server Components, TypeScript), réalisation du planning interactif Tape Chart avec glisser-déposer (Drag & Drop) et Room Shift, intégration des flux WebSockets temps réel."],
        ["Mohamed Hamza IBNTALIB", "Facturation, PWA Mobile & Tests", "Développement des microservices Billing/Folios et Guest Profiles, implémentation des algorithmes fiscaux marocains (TVA 10%, TS 25 MAD, TPT 12 MAD), développement de la PWA mobile Housekeeping, configuration RabbitMQ et rédaction des suites de tests Pytest."]
    ]
    story += make_table(contrib_data, [usable_width * 0.22, usable_width * 0.28, usable_width * 0.50],
                        "Tableau 4-1 : Répartition détaillée des contributions d'ingénierie au sein du trinôme", styles)
    story.append(Spacer(1, 8))
    
    # ── 4.8 DIFFICULTÉS TECHNIQUES RENCONTRÉES ET SOLUTIONS ──────────────────
    story.append(Paragraph("4.8 Difficultés Techniques Rencontrées et Solutions d'Ingénierie", styles['Sec1Title']))
    story.append(Paragraph(
        "Le Tableau 4-2 synthétise les principaux obstacles techniques rencontrés lors du développement et les solutions d'ingénierie apportées.",
        styles['Body']
    ))
    
    defis_data = [
        ["Défi Technique Rencontré", "Cause Racine Identifiée", "Solution d'Ingénierie Implémentée"],
        ["Collisions de réservations simultanées lors des tests de charge", "Deux opérateurs sélectionnant la même chambre avant validation de la transaction SQL.", "Implémentation du pattern de verrouillage distribué Redis (SET NX PX 10000) avec bail de 10s et clé d'idempotence."],
        ["Lenteur excessive du Night Audit initial (> 6 minutes)", "Boucle séquentielle bloquante sur chaque folio avec requêtes SQL unitaires.", "Parallélisation des calculs par coroutines asynchrones (asyncio.gather) et requêtes par lots (Batch SQL), ramenant la durée à 45s."],
        ["Pertes de messages AMQP lors du redémarrage d'un conteneur", "Files d'attente RabbitMQ configurées en mode volatile avec accusé automatique.", "Configuration des files et échanges en mode durable (durable=True) avec acquittement manuel (manual ack) après traitement."],
        ["Erreurs d'arrondis sur les montants de taxes marocaines", "Utilisation du type flottant natif provoquant des dérives sur les centimes.", "Migration intégrale des attributs financiers vers le type Decimal avec arrondi bancaire symétrique (ROUND_HALF_EVEN)."],
        ["Désynchronisation du Tape Chart lors de navigations multi-onglet", "Connexion WebSocket fermée lors du passage en arrière-plan du navigateur.", "Implémentation de la BroadcastChannel API permettant le partage de l'état d'occupation en temps réel entre tous les onglets actifs."]
    ]
    story += make_table(defis_data, [usable_width * 0.32, usable_width * 0.34, usable_width * 0.34],
                        "Tableau 4-2 : Synthèse des défis techniques rencontrés et solutions d'ingénierie apportées", styles)
    story.append(Spacer(1, 8))
    
    # ── 4.9 CONCLUSION DU CHAPITRE ──────────────────────────────────────────
    story.append(Paragraph("4.9 Conclusion du Chapitre", styles['Sec1Title']))
    story.append(Paragraph(
        "Ce quatrième chapitre a présenté la réalisation intégrale et concrète de la plateforme <b>PMS Alidentec Hospitality</b>. "
        "À travers l'architecture technique Docker, l'implémentation rigoureuse des algorithmes fiscaux et de concurrence, et la démonstration "
        "des <b>dix interfaces utilisateurs fondamentales</b>, nous avons prouvé la robustesse et la parfaite adéquation du progiciel avec les exigences "
        "du terrain hôtelier marocain. Le chapitre suivant sera consacré à la <b>Stratégie de Test, de Validation et d'Assurance Qualité Logicielle</b>.",
        styles['Body']
    ))
    story.append(PageBreak())
    
    return story
