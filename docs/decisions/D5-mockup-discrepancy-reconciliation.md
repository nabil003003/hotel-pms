# D5 — Réconciliation des écarts identifiés dans les maquettes HTML

**Statut** : Adopté, appliqué progressivement (Sprint 1 pour les fixtures,
Sprint 6 pour le frontend réel).

## Contexte

L'analyse des 8 maquettes `Design/PMS 1-5` vs le spec vs les 5 PDF
d'origine a révélé plusieurs incohérences (voir conversation projet) :
branding "Hotel Management System" au lieu de "AMH Hospitality", devise
"DH" sans décimales au lieu de "MAD" à 2 décimales, jeux de données mock
différents par page (8 / 17 / 9 chambres), taxonomies de catégories de
chambres différentes (Standard/Suite/Lodge(+Premium) vs les 5 catégories du
Workflow K).

## Décisions

1. **Branding** : "AMH Hospitality" partout dans le frontend réel (Sprint 6).
2. **Devise** : util partagé `formatMAD()` (locale `fr-MA`, 2 décimales,
   suffixe "MAD") — à écrire dans `frontend/lib/currency.ts` au Sprint 6.
3. **Taxonomie des chambres** : les 5 catégories du Workflow K (`Chambre
   Standard`, `Chambre Deluxe`, `Suite Junior`, `Suite Royale`, `Riad
   Entier`) deviennent la référence canonique — voir
   `CANONICAL_ROOM_CATEGORIES` dans
   `services/establishment-service/app/domain/models.py`. Le champ reste un
   `VARCHAR` libre en base (fidélité au schéma §5.1), la validation stricte
   se fera côté frontend/formulaire (Sprint 6).
4. **Jeu de données de référence unique** : `fixtures/seed_riad_yasmine.json`
   (12 chambres, 4 catégories canoniques, 5 services Riad) — utilisé par
   `scripts/seed_sprint1.sh`, réutilisable tel quel par les fixtures pytest
   et les futurs tests Playwright (Sprint 7).

## Conséquences

Le Sprint 6 (intégration frontend) doit partir de ces décisions plutôt que
de recopier les valeurs des maquettes HTML existantes — celles-ci restent
une référence UX (layout, interactions), pas une source de vérité pour les
données ou le nommage produit.
