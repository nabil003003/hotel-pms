# Tester la connexion QR / empreinte digitale avec un vrai téléphone

Le flow QR (biom.txt Flux A/B) a besoin de WebAuthn, qui exige HTTPS et un
domaine que le téléphone peut réellement joindre — `localhost:3000` ne
fonctionne pas depuis un téléphone. On expose donc le frontend **et**
Keycloak via deux tunnels HTTPS [Cloudflare Tunnel](https://github.com/cloudflare/cloudflared)
(`trycloudflare.com`, gratuits, sans compte).

**Chaque tunnel génère une URL aléatoire différente à chaque lancement** —
il faut donc refaire les étapes 5 à 8 ci-dessous à chaque nouvelle session
de test (nouvelles URLs = nouvelle config à propager).

## Prérequis

- Docker Desktop démarré
- Node.js / npm installés
- `cloudflared.exe` — binaire portable, pas d'installation nécessaire :
  ```bash
  curl -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
  ```

## 1. Démarrer l'infra + les 11 microservices + les migrations

Depuis la racine du projet (voir aussi `startup.md` pour le détail) :

```bash
./scripts/start_all.sh --no-frontend
```

Vérifier que tout est `healthy` :

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 2. Démarrer le frontend

```bash
cd frontend
cp .env.example .env.local   # seulement si .env.local n'existe pas déjà
npm install --no-audit --no-fund
npm run dev
```

Accessible en local sur http://localhost:3000 — mais **inaccessible depuis
le téléphone** tant que les tunnels (étape 3) ne sont pas en place.

## 3. Lancer les deux tunnels Cloudflare

Un terminal séparé par tunnel (ou en arrière-plan) :

```bash
./cloudflared.exe tunnel --url http://localhost:3000 > tunnel_frontend.log 2>&1 &
./cloudflared.exe tunnel --url http://localhost:8080 > tunnel_keycloak.log 2>&1 &
```

Récupérer les deux URLs générées (attendre quelques secondes) :

```bash
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' tunnel_frontend.log | head -1
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' tunnel_keycloak.log | head -1
```

Exemple de sortie :
- Frontend : `https://ordering-ports-disclosure-fraction.trycloudflare.com`
- Keycloak : `https://fundamental-sleeping-swimming-programs.trycloudflare.com`

Garder ces deux URLs sous la main pour la suite — on les appelle
`$FRONTEND_TUNNEL` et `$KEYCLOAK_TUNNEL` ci-dessous.

## 4. Pointer Keycloak sur son propre tunnel

Éditer `infra/docker-compose.tunnel-override.yml` : remplacer l'ancien
hostname par le nouveau `$KEYCLOAK_TUNNEL` (sans le `https://`) partout où
il apparaît (`KC_HOSTNAME` du service `keycloak`, et `KEYCLOAK_ISSUER_URL`
des 11 microservices).

Puis relancer avec l'override fusionné (recrée Keycloak + les 11 services
avec les nouvelles variables d'env) :

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.tunnel-override.yml --profile core up -d
```

## 5. Pointer le frontend sur les deux tunnels

Éditer `frontend/.env.local` :

```
NEXT_PUBLIC_APP_URL=https://<FRONTEND_TUNNEL>
KEYCLOAK_URL=https://<KEYCLOAK_TUNNEL>
```

(Les autres variables — `AUTH_GATEWAY_URL`, etc. — restent en
`localhost`, ce sont des appels serveur-à-serveur internes au PC, pas
exposés au téléphone.)

Puis **redémarrer** le serveur Next.js (Next lit `.env.local` seulement au
démarrage) :

```bash
# Ctrl+C sur le process npm run dev existant, puis :
cd frontend && npm run dev
```

## 6. Autoriser l'URL du frontend dans le client Keycloak `pms-frontend`

Sans ça, Keycloak refuse la redirection avec `invalid_redirect_uri`.

Via la console admin (http://localhost:8080, `admin` / `admin_dev_password`,
realm `amh-hospitality` → Clients → `pms-frontend`) :
- **Valid redirect URIs** : ajouter `https://<FRONTEND_TUNNEL>/api/auth/callback`
- **Web origins** : ajouter `https://<FRONTEND_TUNNEL>`

Ou via l'API Admin (plus rapide si on scripte) : `GET` le client, ajouter
l'URL dans `redirectUris`/`webOrigins`, puis `PUT` la représentation
complète sur `/admin/realms/amh-hospitality/clients/{id}`.

## 7. Pointer la policy WebAuthn sur le tunnel Keycloak

Le RP ID WebAuthn doit être le domaine qui sert **réellement** la page de
cérémonie (celle de Keycloak, pas celle du frontend) — sinon erreur
`SecurityError: relying party ID is not a registrable domain suffix...`.

Console admin → realm `amh-hospitality` → **Authentication** → onglet
**Policies** → **WebAuthn Policy** :
- **Relying Party Entity Name** : `AMH Hospitality PMS`
- **Relying Party ID** : `<KEYCLOAK_TUNNEL>` (sans `https://`)

C'est la policy **non-passwordless** (`webAuthnPolicyRpId`) qui compte —
le flow 2FA "mot de passe + empreinte" utilise le credential type
`webauthn` standard, pas `webauthn-passwordless` (voir note plus bas).

## 8. Tester

Sur le **desktop**, ouvrir `https://<FRONTEND_TUNNEL>/login` (pas
`localhost` — sinon le QR encode une URL que le téléphone ne peut pas
joindre) et se connecter avec un compte de test
(`sidi.omar` / `ChangeMe123!`, voir `startup.md` pour la liste).

**Première fois pour ce compte** (aucune empreinte encore liée) : menu
utilisateur → **"Lier mon téléphone"**, scanner le QR affiché avec le
téléphone, entrer le mot de passe du compte sur le téléphone si demandé,
puis confirmer avec l'empreinte/Face ID. Le desktop doit automatiquement
repartir vers le tableau de bord une fois le lien confirmé.

**Connexion quotidienne** : `https://<FRONTEND_TUNNEL>/login/qr`, scanner
avec le téléphone déjà lié → mot de passe puis empreinte sur le téléphone
→ le desktop se connecte automatiquement dès que le téléphone valide.

## 9. Arrêt propre

```bash
# Frontend : Ctrl+C
# Tunnels : Ctrl+C sur chaque process cloudflared (ou kill les PID)
# Infra Docker :
cd infra && docker compose -f docker-compose.yml --profile core down
```

## Notes utiles

- **URLs éphémères** : à chaque relance de `cloudflared`, une nouvelle URL
  aléatoire est générée — les étapes 4 à 7 sont à refaire intégralement à
  chaque nouvelle session de test (nouveau `docker-compose.tunnel-override.yml`,
  nouveau `.env.local`, nouveau redirect URI Keycloak, nouveau RP ID).
- **Type de credential WebAuthn** : le flow "mot de passe + empreinte
  obligatoire" (2FA réel, pas juste une alternative) utilise le credential
  Keycloak standard `webauthn` (comme l'OTP), pas `webauthn-passwordless`.
  Un credential `webauthn-passwordless` lié sous un ancien tunnel ne
  fonctionnera plus après un changement de RP ID — il faut relier le
  téléphone ("Lier mon téléphone") à chaque nouveau tunnel Keycloak.
- **Comptes de test sans téléphone lié** passent directement par le mot de
  passe (l'étape empreinte est sautée tant qu'aucun credential `webauthn`
  n'est enregistré pour ce compte) — comportement voulu, pas un bug.
- `infra/docker-compose.tunnel-override.yml` est un fichier de dev
  temporaire (non committé durablement) — pour revenir à un dev localhost
  normal, relancer simplement `docker compose -f docker-compose.yml
  --profile core up -d` sans l'override.
