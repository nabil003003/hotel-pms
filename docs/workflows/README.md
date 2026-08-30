# Diagrammes de séquence par workflow

Un fichier Markdown par workflow (A–K, voir §4 du spec), contenant un
diagramme Mermaid de séquence — livrable §8.3 point 2. Rempli en Sprint 8
(D15) une fois tous les workflows implémentés et vérifiés (Sprints 1-7) :
chaque diagramme reflète le comportement réel du code, pas l'aspiration
initiale du spec (ex. Workflow F documenté comme un dialogue de formulaire,
pas un drag & drop — ce frontend n'en a pas, voir D14).

| Workflow | Fichier | Résumé |
|---|---|---|
| A | [workflow-a-walkin.md](./workflow-a-walkin.md) | Réservation directe walk-in |
| B | [workflow-b-b2b.md](./workflow-b-b2b.md) | Réservation agence B2B (tarif négocié) |
| C | [workflow-c-ota.md](./workflow-c-ota.md) | Réservation OTA (webhook synchrone) |
| D | [workflow-d-checkin.md](./workflow-d-checkin.md) | Check-in (saga folios) |
| E | [workflow-e-extra.md](./workflow-e-extra.md) | Extra en cours de séjour |
| F | [workflow-f-roomshift.md](./workflow-f-roomshift.md) | Changement de chambre / upsell |
| G | [workflow-g-checkout.md](./workflow-g-checkout.md) | Check-out |
| H | [workflow-h-housekeeping.md](./workflow-h-housekeeping.md) | Housekeeping temps réel (PWA) |
| I | [workflow-i-nightaudit.md](./workflow-i-nightaudit.md) | Night Audit (verify → close) |
| J | [workflow-j-analytics.md](./workflow-j-analytics.md) | Dashboard Analytics |
| K | [workflow-k-establishment-config.md](./workflow-k-establishment-config.md) | Configuration établissement (admin) |
