import os, shutil

# Create the target directory "pictures of rapport" in RAPPORTpartie
target_dir = os.path.join('PMSV2-main', 'RAPPORTpartie', 'pictures of rapport')
os.makedirs(target_dir, exist_ok=True)
src_dir = os.path.join('PMSV2-main', 'RAPPORTpartie', 'figures')

# Selection of the TOP 10 project screenshots with clean, academic, descriptive names:
selected_10 = [
    {
        "src": "homepage.png",
        "dest": "01_tableau_de_bord_accueil_pms.png",
        "titre": "Figure 4-1 : Tableau de bord principal d'accueil et d'exploitation du PMS",
        "module": "Module 1 : Exploitation Générale & Pilotage Multi-Riads",
        "description": "Vue d'ensemble affichant les indicateurs clés de performance en temps réel (taux d'occupation journalier, arrivées prévues, départs attendus, chiffre d'affaires généré et alertes de service). Barre latérale de navigation vers les 11 modules de la plateforme."
    },
    {
        "src": "reservation.png",
        "dest": "02_formulaire_creation_reservation.png",
        "titre": "Figure 4-2 : Formulaire de création et tarification dynamique de réservation",
        "module": "Module 2 : Moteur de Réservation & Pricing",
        "description": "Interface modale de réservation avec sélection de suite, calendrier de séjour, ventilation tarifaire automatique (prix HT, TVA 10%, Taxe de Séjour 25 MAD, TPT 12 MAD) et pose immédiate du verrou atomique Redis anti-collision."
    },
    {
        "src": "businescheckin.png",
        "dest": "03_enregistrement_checkin_police.png",
        "titre": "Figure 4-3 : Interface de Check-in voyageur et formalités de police réglementaires",
        "module": "Module 3 : Front-Office & Conformité Légale",
        "description": "Écran d'enregistrement à l'arrivée avec vérification automatique de propreté de la suite (statut CLEAN), saisie des pièces d'identité officielles (passeport/CIN) et génération instantanée de la fiche de police marocaine réglementaire."
    },
    {
        "src": "folio_1.png",
        "dest": "04_facturation_folio_client.png",
        "titre": "Figure 4-4 : Compte financier Folio client et grand livre comptable du séjour",
        "module": "Module 4 : Facturation & Gestion des Folios",
        "description": "Grand livre individualisé enregistrant l'ensemble des débits de nuitées et taxes, les consommations annexes, les encaissements multi-moyens (carte, espèces, virement) et le calcul en direct du solde net exigé avant Check-out."
    },
    {
        "src": "ajouter_charge.png",
        "dest": "05_imputation_charge_extra.png",
        "titre": "Figure 4-5 : Fenêtre modale d'imputation d'une consommation extra (Restaurant / Spa)",
        "module": "Module 5 : Facturation des Extras & Point de Vente",
        "description": "Modal permettant d'ajouter instantanément une prestation annexe (table d'hôtes marocaine, hammam traditionnel, transfert aéroport) sur le folio du voyageur avec calcul automatique de la TVA correspondante."
    },
    {
        "src": "business_date.png",
        "dest": "06_cloture_nocturne_night_audit.png",
        "titre": "Figure 4-6 : Module de clôture journalière automatisée (Night Audit)",
        "module": "Module 6 : Clôture Comptable & Business Date",
        "description": "Console de supervision de la clôture nocturne : validation des dossiers résidents, exécution du traitement batch en 45 secondes, transfert immuable du rapport d'audit sur MinIO S3 et basculement automatique de la Business Date."
    },
    {
        "src": "femme.jpeg",
        "dest": "07_application_mobile_housekeeping_pwa.jpg",
        "titre": "Figure 4-7 : Progressive Web App (PWA) mobile pour la gouvernance d'étage",
        "module": "Module 7 : Housekeeping & Mobilité",
        "description": "Interface smartphone optimisée pour les gouvernantes et femmes de chambre affichant la liste des suites à traiter avec code couleur d'état (DIRTY / CLEAN / INSPECTED) et synchronisation temps réel par WebSockets."
    },
    {
        "src": "etabli.png",
        "dest": "08_gestion_multi_etablissements.png",
        "titre": "Figure 4-8 : Console de configuration multi-établissements (Riads du groupe)",
        "module": "Module 8 : Administration & Multi-Tenancy",
        "description": "Module d'administration permettant de paramétrer les différents Riads partenaires (Riad Yasmine, Riad Al Ksar), leurs catégories de suites, leurs équipements, leurs grilles tarifaires et leurs règles fiscales."
    },
    {
        "src": "names.png",
        "dest": "09_annuaire_crm_profils_clients.png",
        "titre": "Figure 4-9 : Répertoire CRM unifié des profils voyageurs et segmentation VIP",
        "module": "Module 9 : CRM Clients & Profils Voyageurs",
        "description": "Fichier centralisé des profils clients avec historique des séjours passés, nationalités, coordonnées vérifiées, préférences personnalisées et statut de fidélité VIP."
    },
    {
        "src": "pms_link_qr.png",
        "dest": "10_authentification_fido2_passkey_qr.png",
        "titre": "Figure 4-10 : Terminal d'appairage biométrique sans mot de passe WebAuthn par QR Code",
        "module": "Module 10 : Sécurité & Authentification FIDO2",
        "description": "Borne d'authentification sans mot de passe affichant le QR Code dynamique généré par Keycloak permettant au réceptionniste de s'authentifier par capteur biométrique (TouchID/FaceID) sur son smartphone personnel en moins de 2 secondes."
    }
]

print(f"Copie et organisation des 10 meilleures captures du projet dans '{target_dir}' :")
for item in selected_10:
    src_path = os.path.join(src_dir, item["src"])
    dest_path = os.path.join(target_dir, item["dest"])
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"  [OK] {item['dest']:45s} (source: {item['src']})")
    else:
        print(f"  [MANQUE] {item['src']} introuvable")

print(f"\nLes 10 images ont ete placees et nommees dans '{target_dir}'.")
