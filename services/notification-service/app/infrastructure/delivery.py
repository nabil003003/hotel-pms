"""Livraison "stub" (D11) — aucun fournisseur SMTP/SMS/push réel dans
`infra/docker-compose.yml`. Interface isolée à dessein : brancher un vrai
fournisseur plus tard ne touche que ce module."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def deliver(*, channel: str, recipient_role: str, subject: str, body: str) -> bool:
    logger.info("[stub-%s] to role=%s subject=%r body=%r", channel, recipient_role, subject, body)
    return True
