# OpenAPI agrégé

Chaque service FastAPI expose déjà son schéma OpenAPI natif sur `/openapi.json`
(ex : http://localhost:8001/openapi.json pour auth-gateway-service en local).

Ce dossier accueillera l'agrégation Kong (`/docs` unifié, §8.3 point 1) à
partir du Sprint 2, une fois Kong introduit (profil `gateway`). En Sprint 1,
consulter directement le `/openapi.json` de chacun des 3 services (ports
8001/8002/8003).
