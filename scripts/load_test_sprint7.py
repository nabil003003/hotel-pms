"""Sprint 7 (D14) — test de charge pragmatique, scénario spec §7.4 :
"15 réceptionnistes créant 30 réservations/minute simultanément".

Ni k6 ni Locust ne sont installés sur cette machine et ce sprint n'installe
pas un nouvel outil externe pour un run ponctuel — substitution en
asyncio+httpx qui reproduit la charge réelle (15 workers concurrents,
30 requêtes POST /bookings au total) et mesure un p95 réel, comparé à
l'objectif spec de < 200ms. Un seul scénario de charge est reproduit ici (les
3 autres — Night Audit 50 chambres, WebSocket 30 clients, 50 webhooks OTA/min
— restent non testés, notés comme dette dans D14).

Chaque requête cible une date d'arrivée future distincte (offset croissant,
loin dans le futur) pour qu'aucune des 30 réservations concurrentes ne se
dispute la même chambre/date — l'objectif est de mesurer la latence de
l'endpoint sous concurrence, pas de retester le verrouillage Redis (déjà
couvert par `test_integration_sprint7.py`, scénario 3).

Prérequis : `docker compose --profile core up -d` (stack déjà chaude,
keycloak_setup.py déjà exécuté).
"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from datetime import date, timedelta

import httpx

KEYCLOAK_URL = "http://localhost:8080"
RESERVATION_URL = "http://localhost:8007"
REALM = "amh-hospitality"

RIAD_YASMINE_ID = "4f9cb82b-4ded-491c-b85d-ba2cd6d36fda"

CONCURRENCY = 15
TOTAL_BOOKINGS = 30
TARGET_P95_MS = 200
# Loin dans le futur pour ne jamais entrer en collision avec des données de
# test déjà seedées près de "aujourd'hui" par les sprints précédents.
DATE_OFFSET_START_DAYS = 700


def log(msg: str) -> None:
    print(f"==> {msg}", flush=True)


async def get_token(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "password", "client_id": "pms-frontend",
            "username": "test.receptionniste", "password": "ChangeMe123!",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def create_one_booking(
    client: httpx.AsyncClient, headers: dict, semaphore: asyncio.Semaphore, index: int
) -> tuple[int, float]:
    check_in = date.today() + timedelta(days=DATE_OFFSET_START_DAYS + index)
    check_out = check_in + timedelta(days=1)
    payload = {
        "establishment_id": RIAD_YASMINE_ID, "market_segment_category": "DIRECT",
        "room_category": "Chambre Standard", "check_in_date": check_in.isoformat(),
        "check_out_date": check_out.isoformat(), "regime": "BB", "taxes_payment_mode": "on_site",
        "adults": 1, "customer": {"first_name": "Load", "last_name": f"Test{index}"},
        "source": "walk_in", "deposit_paid": True,
    }
    async with semaphore:
        start = time.perf_counter()
        resp = await client.post(f"{RESERVATION_URL}/api/v1/bookings", headers=headers, json=payload)
        elapsed_ms = (time.perf_counter() - start) * 1000
    return resp.status_code, elapsed_ms


async def main() -> None:
    async with httpx.AsyncClient(timeout=20.0) as client:
        token = await get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        semaphore = asyncio.Semaphore(CONCURRENCY)

        log(f"Firing {TOTAL_BOOKINGS} POST /bookings at concurrency={CONCURRENCY} "
            f"(spec §7.4: 15 réceptionnistes x 30 réservations/minute)")
        wall_start = time.perf_counter()
        results = await asyncio.gather(*(
            create_one_booking(client, headers, semaphore, i) for i in range(TOTAL_BOOKINGS)
        ))
        wall_elapsed = time.perf_counter() - wall_start

    statuses = [r[0] for r in results]
    latencies = sorted(r[1] for r in results)
    failures = [s for s in statuses if s != 201]

    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95) - 1]
    p99 = latencies[int(len(latencies) * 0.99) - 1] if len(latencies) >= 100 else max(latencies)
    avg = statistics.mean(latencies)

    log(f"Wall time for {TOTAL_BOOKINGS} bookings @ concurrency {CONCURRENCY}: {wall_elapsed:.2f}s")
    log(f"Latency (ms) — min={min(latencies):.1f} avg={avg:.1f} p50={p50:.1f} p95={p95:.1f} p99={p99:.1f} max={max(latencies):.1f}")
    log(f"Status codes: {sorted(set(statuses))} ({len(failures)} non-201)")

    if failures:
        print(f"\nFAILED: {len(failures)}/{TOTAL_BOOKINGS} requests did not return 201", file=sys.stderr)
        sys.exit(1)

    if p95 > TARGET_P95_MS:
        print(f"\nMEASURED (not failing the run): p95={p95:.1f}ms exceeds spec target of {TARGET_P95_MS}ms", file=sys.stderr)
    else:
        log(f"p95={p95:.1f}ms meets spec target of < {TARGET_P95_MS}ms")

    log("Sprint 7 load test: DONE")


if __name__ == "__main__":
    asyncio.run(main())
