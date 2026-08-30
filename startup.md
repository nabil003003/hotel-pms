# Démarrage du projet — PMS AMH Hospitality

Guide pratique pour relancer la stack complète après un arrêt (`docker compose down`, redémarrage machine, etc.). Voir aussi le `README.md` principal pour le détail architecture/décisions.

## Pré-requis

- Docker Desktop démarré
- Node.js / npm installés (pour le frontend)

## Démarrage en une commande (recommandé)

```bash
./scripts/start_all.sh
```

Enchaîne automatiquement les étapes 1 à 3 ci-dessous (infra Docker, provisioning
Keycloak, migrations Alembic sur les 11 services) puis lance le frontend
(`npm install` + `npm run dev`, bloquant — Ctrl+C pour arrêter). Idempotent :
sans risque de le relancer sur une stack déjà up.

Options :
- `--build` : reconstruit les images Docker avant de démarrer (si du code
  backend a changé depuis le dernier build).
- `--no-frontend` : n'installe/ne lance pas le frontend (infra + migrations
  seulement, utile en CI ou si le frontend tourne déjà séparément).

L'étape 4 (peuplement des données de référence) reste manuelle — voir plus bas,
elle ne s'applique qu'à une base neuve, pas à un redémarrage normal.

Le détail pas-à-pas ci-dessous reste utile pour déboguer une étape précise ou
comprendre ce que fait le script.

## 1. Lancer l'infra + les 11 microservices

Depuis la racine du projet :

```bash
cd infra
docker compose -f docker-compose.yml --profile core up -d
```

(Ajouter `--build` uniquement si du code backend a changé depuis le dernier build : `docker compose -f docker-compose.yml --profile core up -d --build`.)

Ça démarre : Postgres, Redis, RabbitMQ, Keycloak, MinIO + les 11 services métier (auth-gateway, establishment, housekeeping, pricing, partner, channel-manager, reservation, front-office, analytics, night-audit, notification).

Vérifier que tout est `healthy` :

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 2. Provisionner Keycloak (idempotent — sans risque de le relancer)

```bash
python scripts/keycloak_setup.py
```

Crée le realm `amh-hospitality`, les rôles, les comptes de service, et les utilisateurs de test si absents.

## 3. Appliquer les migrations (idempotent — no-op si déjà à jour)

```bash
cd infra
for svc in auth-gateway-service establishment-service housekeeping-service pricing-service partner-service channel-manager-service reservation-service front-office-service analytics-service night-audit-service notification-service; do
  docker compose -f docker-compose.yml exec "$svc" alembic upgrade head
done
```

## 4. (Uniquement sur une base neuve) Peupler les données de référence

Si les tables sont vides (nouvelle installation, pas juste un redémarrage) :

```bash
./scripts/seed_sprint1.sh
export RIAD_YASMINE_ID=<uuid affiché par le script>
./scripts/seed_sprint2.sh
./scripts/seed_sprint3.sh
./scripts/seed_sprint4.sh
./scripts/seed_sprint5.sh
```

Sur un redémarrage normal, les données persistent dans le volume Docker `pgdata` — cette étape n'est pas nécessaire.

## 5. Lancer le frontend

```bash
cd frontend
npm run dev
```

Accessible sur **http://localhost:3000**.

## Comptes de test

Mot de passe pour tous : `ChangeMe123!`

| Utilisateur | Rôle |
|---|---|
| `sidi.omar` | super-admin |
| `test.receptionniste` | réceptionniste |
| `test.gouvernante` | gouvernante |
| `test.femmedechambre` | femme de chambre |

## Ports utiles

| Service | Port |
|---|---|
| Frontend | 3000 |
| Keycloak (admin console) | 8080 |
| auth-gateway-service | 8001 |
| establishment-service | 8002 |
| housekeeping-service | 8003 |
| pricing-service | 8004 |
| partner-service | 8005 |
| channel-manager-service | 8006 |
| reservation-service | 8007 |
| front-office-service | 8008 |
| analytics-service | 8009 |
| night-audit-service | 8010 |
| notification-service | 8011 |
| RabbitMQ management | 15672 |
| MinIO console | 9001 |
| Postgres | 5432 |
| Redis | 6379 |

## Arrêt propre

```bash
# Frontend : Ctrl+C dans le terminal npm run dev

# Infra Docker (arrête les conteneurs, garde les volumes/données)
cd infra
docker compose -f docker-compose.yml --profile core down
```

Pour tout effacer y compris les données (`pgdata`, etc.) : ajouter `-v` à la commande `down` (⚠️ destructif, à réserver à une remise à zéro volontaire).

## Notes utiles

- La **date métier** (business date) de l'établissement peut être en avance sur la date calendaire après une clôture night-audit — voir `docs/decisions/` et le comportement de `night-audit-service` (`GET /api/v1/night-audit/business-date`) si des écrans semblent afficher des données "figées" ou rejettent une action avec `Business date locked`.
- `kpi/today`/`kpi/monthly` (Analytics) sont cachés côté Redis (5 min / 1h) mais invalidés automatiquement à chaque check-in/charge/paiement/check-out — pas besoin de flush manuel en usage normal.
