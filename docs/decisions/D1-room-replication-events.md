# D1 — Réplication des chambres establishment-service → housekeeping-service

**Statut** : Adopté, Sprint 1.

## Contexte

Le spec (§2.1) déclare `housekeeping-service` dépendant de `establishment-service`,
et lui donne sa propre table `rooms` (§5.4, copie locale numero/categorie/floor).
Mais l'Appendix C (catalogue d'événements RabbitMQ) ne définit aucun événement
de création/mise à jour de chambre — un vrai trou du spec pour tenir cette
réplication à jour.

## Décision

`establishment-service` publie 3 événements nouveaux (absents de l'Appendix C
d'origine), sur l'exchange `amh.establishment` :

- `establishment.created`
- `establishment.rooms_imported` (batch, après un import CSV ou bulk)
- `establishment.room_updated` (création/édition/soft-delete unitaire)

`housekeeping-service` les consomme (queue `housekeeping.establishment_events`)
pour upsert sa copie locale de `rooms` (statut par défaut `Propre`).

Filet de sécurité : `POST /api/v1/internal/resync/{establishment_id}` sur
housekeeping-service, qui rappelle `GET /establishments/{id}/rooms` en REST
(D1 ne suppose pas de livraison exactement-une-fois de RabbitMQ en Sprint 1).

## Conséquences

- Sprint 2+ : tout nouveau service ayant besoin d'une vue des chambres
  (pricing-service pour la grille tarifaire, reservation-service pour la
  disponibilité) devra soit consommer les mêmes événements, soit appeler
  establishment-service en REST — décider au cas par cas plutôt que
  généraliser prématurément.
