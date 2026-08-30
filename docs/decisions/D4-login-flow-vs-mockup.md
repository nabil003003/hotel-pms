# D4 — Flow de login réel vs maquette `login.html`

**Statut** : Adopté, Sprint 6 (frontend) — décidé en Sprint 1 pour cadrer le
thème Keycloak posé dès maintenant.

## Contexte

`Design/PMS 1/login.html` est un formulaire HTML/JS custom (champs
identifiant/mot de passe maison, boutons biométriques câblés sur des
`alert()`). Le spec impose Authorization Code + PKCE contre Keycloak
(§1, §3.1) avec WebAuthn/Passkeys natifs Keycloak (`webauthn-register`,
§3.2.1).

## Décision

PKCE signifie une redirection navigateur vers la page de login **hébergée
par Keycloak**, pas un rendu Next.js du formulaire de la maquette. On ne
reproduit donc pas le DOM de `login.html` : on re-thème Keycloak lui-même
(`infra/keycloak/themes/amh-hospitality/login/`, palette identique —
`#4a6cf7` primaire, Inter, cartes `border-radius:16px`). Le frontend
implémente uniquement les routes PKCE (`/api/auth/login`,
`/api/auth/callback`, `openid-client`), pas un formulaire de saisie.

Le WebAuthn/biométrie n'est donc jamais implémenté en JS custom côté
frontend — c'est un `requiredAction` Keycloak (`webauthn-register`), à
activer par utilisateur via l'Admin API/console quand ce flow sera vraiment
exercé (au-delà des comptes de test Sprint 1, qui utilisent password seul
pour rester scriptables par `scripts/smoke_test_sprint1.sh`).

**Mise à jour (vérification Sprint 1)** : le realm `amh-hospitality` n'est
plus provisionné via `--import-realm` + un `realm-export.json` écrit à la
main. Un test réel a montré qu'un realm importé ainsi manque des
scopes/flows implicites qu'un realm créé via `POST /admin/realms` obtient
automatiquement, ce qui cassait le Direct Grant avec l'erreur interne
`resolve_required_actions` — reproductible même pour un utilisateur neuf
sans aucune required action. Provisioning réel :
`scripts/keycloak_setup.py` (API Admin REST, idempotent), lancé une fois
Keycloak démarré. Le thème (`infra/keycloak/themes/amh-hospitality/`) reste
monté en volume, seule la création du realm/clients/rôles/utilisateurs est
passée en scripté-API.

## Conséquences

- Sprint 6 : ne pas chercher à porter `login.html` en composant React —
  seul son habillage visuel compte, pas sa structure de formulaire.
- Vérifier le nom du thème parent Keycloak (`keycloak` vs `keycloak.v2`)
  contre la version réellement déployée avant la prod (`theme.properties`
  contient une note à ce sujet).
- Ne plus jamais réintroduire un `realm-export.json` statique pour ce
  realm — toute évolution du realm passe par `scripts/keycloak_setup.py`.
