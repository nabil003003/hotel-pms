# notification-service

Sprint 5. Livraison "stub" (D11) — pas de vrai fournisseur SMTP/SMS/push,
chaque notification est journalisée et persistée dans `notifications`
(`notif_db`), destinataire résolu par rôle (`recipient_role`), pas par
email réel.

Consomme (Appendix C) : `booking.created`, `booking.checked_in`,
`booking.checked_out`, `booking.cancelled`, `room.incident_reported`,
`channel.sync_failed`. `POST /api/v1/notifications/send` expose le même
chemin de création pour les appels directs de night-audit-service (alerte
d'écart pré-audit, email de rapport post-audit — voir D11/D12).

Voir `docs/decisions/D11-notification-service-dev-stub.md`.
