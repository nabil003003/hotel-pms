# D11 — notification-service : livraison "stub" en dev, pas de vrai fournisseur

**Statut** : Adopté, Sprint 5.

## Contexte

Le spec (§2.1, ligne 118) décrit `notification-service` comme "Emails, push,
alertes métier, SMS", consommé par tous les autres services via événements.
Aucune section §5.x du spec ne transcrit de schéma SQL pour ce service (à la
différence de tous les autres) — `notif_db` existe dans la liste des bases
(ligne 1456) mais sans DDL associé : le schéma est donc à concevoir, pas à
transcrire.

Il n'y a ni serveur SMTP, ni passerelle SMS/push dans `infra/docker-compose.yml`
(pas de MailHog, pas de Twilio/FCM mockés) — les ajouter serait une dépendance
d'infra non demandée pour un besoin de démonstration.

## Décision

- Schéma conçu pour ce sprint : table `notifications` (id, establishment_id,
  event_type, channel, recipient_role, subject, body, status, related_entity_id,
  created_at, sent_at). `channel` ∈ {email, push, sms} par type d'événement,
  selon le mapping prose du spec (ex. ligne 613 : "email + push" pour l'écart
  Night Audit).
- **Pas de résolution d'utilisateur réel** : `recipient_role` stocke un rôle
  (`admin`, `manager`, `receptionniste`, `gouvernante`) plutôt qu'un email
  résolu via l'API Admin Keycloak — résoudre les vrais utilisateurs par
  établissement+rôle nécessiterait un appel cross-service supplémentaire vers
  auth-gateway-service pour une valeur qui ne serait de toute façon jamais
  vraiment envoyée (pas de fournisseur réel, voir point suivant). Hors-scope
  Sprint 5, note pour un futur sprint si un vrai fournisseur est branché.
- **Livraison "stub"** : `deliver()` ne fait qu'un `logger.info` + marque la
  ligne `status="sent"` immédiatement (pas de file de retry, pas de vrai appel
  externe). L'interface (`app/infrastructure/delivery.py`) est isolée
  derrière une fonction unique précisément pour qu'un vrai provider
  (SendGrid, Twilio, FCM...) puisse être branché plus tard sans toucher au
  reste du service.
- Événements consommés (Appendix C, filtré aux lignes où `notification` est
  listé comme consommateur) : `booking.created`, `booking.checked_in`,
  `booking.checked_out`, `booking.cancelled`, `room.incident_reported`,
  `channel.sync_failed`. `audit.closed` n'est **pas** consommé de façon
  événementielle par notification-service — voir D12 (l'email de rapport et
  l'alerte d'écart Night Audit sont des appels REST synchrones directs
  depuis night-audit-service, pas un flux asynchrone, car ils ont besoin de
  transporter des données absentes du payload `audit.closed` de l'Appendix C
  — `report_urls`, détail de l'écart).
- `POST /api/v1/notifications/send` expose ce même chemin de création aux
  appels directs (réservé aux comptes de service via `require_super_admin`,
  même pattern que les autres endpoints internes cross-service du monorepo).

## Conséquences

- Aucune notification n'est réellement livrée en dev — seulement journalisée
  et persistée. `GET /api/v1/notifications` permet de vérifier qu'une
  notification aurait bien été envoyée (utilisé par le smoke test Sprint 5).
- Si un vrai fournisseur est branché plus tard, il faudra aussi résoudre de
  vrais destinataires (voir point ci-dessus) — actuellement non fait.
