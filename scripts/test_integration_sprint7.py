"""Sprint 7 (D14) — scénarios d'intégration du spec §7.2 jamais exercés par
les smoke tests des sprints précédents (tous utilisaient le chemin "heureux") :

1. Night Audit avec écart détecté (DiscrepancyError + alerte notification).
2. Room Shifting avec conflit de chambre (409 ROOM_CONFLICT).
3. Double-booking concurrent (une seule des deux requêtes doit gagner).
4. Webhook OTA avec mapping room_type_id absent (422 MAPPING_ERROR).
5. Expiration automatique d'une option (boucle asyncio, pas de Celery).

Prérequis : `docker compose --profile core up -d` + seed_sprint1..5.sh déjà
exécutés (RIAD_YASMINE_ID connu). Contrairement aux smoke tests bash
existants, ce script est en Python (httpx + asyncio) car le scénario 3 exige
une vraie concurrence (deux requêtes tirées en parallèle) et le scénario 5
manipule directement Postgres via `docker compose exec`.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import subprocess
import sys
import uuid
from datetime import date, datetime, timedelta

import httpx

KEYCLOAK_URL = "http://localhost:8080"
RESERVATION_URL = "http://localhost:8007"
HOUSEKEEPING_URL = "http://localhost:8003"
FRONT_OFFICE_URL = "http://localhost:8008"
NIGHT_AUDIT_URL = "http://localhost:8010"
NOTIFICATION_URL = "http://localhost:8011"
CHANNEL_URL = "http://localhost:8006"
ESTABLISHMENT_URL = "http://localhost:8002"
REALM = "amh-hospitality"
WEBHOOK_HMAC_SECRET = "dev-webhook-hmac-secret"
COMPOSE_FILE = "infra/docker-compose.yml"

RIAD_YASMINE_ID = "4f9cb82b-4ded-491c-b85d-ba2cd6d36fda"

STANDARD_ROOM_A = "e8115b73-8b95-4488-9370-8b453c79f883"
STANDARD_ROOM_B = "afd280c2-8ae7-475c-8072-3a9950560766"


def log(msg: str) -> None:
    print(f"==> {msg}", flush=True)


async def get_token(client: httpx.AsyncClient, username: str, password: str) -> str:
    resp = await client.post(
        f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={"grant_type": "password", "client_id": "pms-frontend", "username": username, "password": password},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def ensure_room_ready(client: httpx.AsyncClient, headers: dict, room_id: str) -> None:
    resp = await client.get(f"{HOUSEKEEPING_URL}/api/v1/rooms/{room_id}/status", headers=headers)
    resp.raise_for_status()
    if resp.json()["statut"] not in ("Propre", "Contrôlée"):
        r = await client.patch(
            f"{HOUSEKEEPING_URL}/api/v1/rooms/{room_id}/status", headers=headers, json={"new_status": "Propre"}
        )
        r.raise_for_status()


def run_sql(database: str, sql: str) -> str:
    result = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "exec", "-T", "postgres", "psql", "-U", "amh", "-d", database, "-c", sql],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


# ------------------------------------------------------- 1. Night Audit écart


async def test_night_audit_discrepancy(client: httpx.AsyncClient, headers: dict) -> None:
    log("[1/5] Night Audit — écart détecté")
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Clear any stale lock/closed-audit-run left by a previous same-day run —
    # audit_runs has a unique (establishment_id, business_date) constraint, so a
    # prior close for today (real calendar date, front-office's Folio.business_date
    # always uses date.today() with no rollover) makes verify() 409 ALREADY_CLOSED
    # before it even reaches the discrepancy check.
    run_sql("fo_db", f"DELETE FROM business_date_locks WHERE business_date = '{today}';")
    run_sql("reserv_db", f"DELETE FROM business_date_locks WHERE business_date = '{today}';")
    run_sql("audit_db", f"DELETE FROM audit_snapshots WHERE establishment_id = '{RIAD_YASMINE_ID}' AND business_date = '{today}';")
    run_sql("audit_db", f"DELETE FROM audit_runs WHERE establishment_id = '{RIAD_YASMINE_ID}' AND business_date = '{today}';")

    booking = (await client.post(
        f"{RESERVATION_URL}/api/v1/bookings", headers=headers,
        json={
            "establishment_id": RIAD_YASMINE_ID, "market_segment_category": "DIRECT",
            "room_category": "Chambre Standard", "check_in_date": today, "check_out_date": tomorrow,
            "regime": "BB", "taxes_payment_mode": "on_site", "adults": 1,
            "customer": {"first_name": "Sprint7", "last_name": "Discrepancy"},
            "source": "walk_in", "deposit_paid": True,
        },
    )).json()
    await ensure_room_ready(client, headers, booking["room_id"])

    checkin = (await client.post(
        f"{FRONT_OFFICE_URL}/api/v1/folios/check-in", headers=headers,
        json={"establishment_id": RIAD_YASMINE_ID, "booking_id": booking["id"]},
    )).json()
    folio_id = checkin["folio_ids"][0]

    # Charge added but deliberately NOT paid -> total_debits > total_credits for today.
    charge_resp = await client.post(
        f"{FRONT_OFFICE_URL}/api/v1/folios/{folio_id}/charges", headers=headers,
        json={"poste_comptable": "BAR", "libelle": "Sprint7 unpaid charge", "quantity": 1, "unit_price_ht": 100},
    )
    charge_resp.raise_for_status()

    verify_resp = await client.post(
        f"{NIGHT_AUDIT_URL}/api/v1/night-audit/verify", headers=headers,
        json={"establishment_id": RIAD_YASMINE_ID, "business_date": today},
    )
    assert verify_resp.status_code == 409, f"expected 409, got {verify_resp.status_code}: {verify_resp.text}"
    detail = verify_resp.json()["detail"]
    assert detail["code"] == "DISCREPANCY_DETECTED", detail
    assert detail["discrepancy"] != 0, "expected a non-zero discrepancy"
    log(f"    -> verify correctly rejected with discrepancy={detail['discrepancy']}")

    found = False
    for _ in range(10):
        notifs = (await client.get(
            f"{NOTIFICATION_URL}/api/v1/notifications", headers=headers,
            params={"establishment_id": RIAD_YASMINE_ID, "event_type": "audit.discrepancy_detected"},
        )).json()
        if notifs:
            found = True
            break
        await asyncio.sleep(2)
    assert found, "expected at least one audit.discrepancy_detected notification"
    log("    -> discrepancy alert recorded in notification-service")

    # Cleanup: settle the folio so today's business_date stays balanced for
    # anyone re-running Night Audit for real afterwards.
    folio = (await client.get(f"{FRONT_OFFICE_URL}/api/v1/folios/{folio_id}", headers=headers)).json()
    if folio["balance"] > 0:
        await client.post(
            f"{FRONT_OFFICE_URL}/api/v1/folios/{folio_id}/payments", headers=headers,
            json={"mode": "CB", "montant": folio["balance"]},
        )
    await client.post(
        f"{FRONT_OFFICE_URL}/api/v1/folios/check-out", headers=headers,
        json={"establishment_id": RIAD_YASMINE_ID, "booking_id": booking["id"]},
    )
    log("    -> cleaned up (folio settled + checked out)")


# ------------------------------------------------------- 2. Room Shift conflict


async def test_room_shift_conflict(client: httpx.AsyncClient, headers: dict) -> None:
    log("[2/5] Room Shifting — conflit de chambre (409 ROOM_CONFLICT)")
    check_in = "2027-09-10"
    check_out = "2027-09-12"

    booking1 = (await client.post(
        f"{RESERVATION_URL}/api/v1/bookings", headers=headers,
        json={
            "establishment_id": RIAD_YASMINE_ID, "market_segment_category": "DIRECT",
            "room_category": "Chambre Standard", "room_id": STANDARD_ROOM_A,
            "check_in_date": check_in, "check_out_date": check_out,
            "regime": "BB", "taxes_payment_mode": "on_site", "adults": 1,
            "customer": {"first_name": "Sprint7", "last_name": "ShiftA"},
            "source": "walk_in", "deposit_paid": True,
        },
    )).json()
    booking2 = (await client.post(
        f"{RESERVATION_URL}/api/v1/bookings", headers=headers,
        json={
            "establishment_id": RIAD_YASMINE_ID, "market_segment_category": "DIRECT",
            "room_category": "Chambre Standard", "room_id": STANDARD_ROOM_B,
            "check_in_date": check_in, "check_out_date": check_out,
            "regime": "BB", "taxes_payment_mode": "on_site", "adults": 1,
            "customer": {"first_name": "Sprint7", "last_name": "ShiftB"},
            "source": "walk_in", "deposit_paid": True,
        },
    )).json()

    shift_resp = await client.patch(
        f"{RESERVATION_URL}/api/v1/bookings/{booking1['id']}/room", headers=headers,
        json={"new_room_id": STANDARD_ROOM_B, "same_category": True},
    )
    assert shift_resp.status_code == 409, f"expected 409, got {shift_resp.status_code}: {shift_resp.text}"
    assert shift_resp.json()["detail"]["code"] == "ROOM_CONFLICT", shift_resp.json()
    log("    -> correctly rejected (409 ROOM_CONFLICT)")

    for bid in (booking1["id"], booking2["id"]):
        await client.patch(
            f"{RESERVATION_URL}/api/v1/bookings/{bid}/status", headers=headers,
            json={"new_status": "status_cancelled", "reason": "Sprint7 integration test cleanup"},
        )


# ------------------------------------------------------- 3. Double-booking


async def test_double_booking_concurrency(client: httpx.AsyncClient, headers: dict) -> None:
    log("[3/5] Réservation walk-in — double-booking concurrent")
    check_in = "2027-10-05"
    check_out = "2027-10-07"

    def make_payload(last_name: str) -> dict:
        return {
            "establishment_id": RIAD_YASMINE_ID, "market_segment_category": "DIRECT",
            "room_category": "Chambre Standard", "room_id": STANDARD_ROOM_A,
            "check_in_date": check_in, "check_out_date": check_out,
            "regime": "BB", "taxes_payment_mode": "on_site", "adults": 1,
            "customer": {"first_name": "Sprint7", "last_name": last_name},
            "source": "walk_in", "deposit_paid": True,
        }

    results = await asyncio.gather(
        client.post(f"{RESERVATION_URL}/api/v1/bookings", headers=headers, json=make_payload("Concurrent1")),
        client.post(f"{RESERVATION_URL}/api/v1/bookings", headers=headers, json=make_payload("Concurrent2")),
        return_exceptions=True,
    )
    statuses = [r.status_code for r in results if isinstance(r, httpx.Response)]
    assert sorted(statuses) == [201, 409], f"expected exactly one 201 and one 409, got {statuses}"
    log(f"    -> exactly one booking succeeded, the other got 409 (statuses={statuses})")

    winner = next(r for r in results if isinstance(r, httpx.Response) and r.status_code == 201)
    await client.patch(
        f"{RESERVATION_URL}/api/v1/bookings/{winner.json()['id']}/status", headers=headers,
        json={"new_status": "status_cancelled", "reason": "Sprint7 integration test cleanup"},
    )


# ------------------------------------------------------- 4. OTA mapping absent


async def test_ota_webhook_unmapped(client: httpx.AsyncClient, headers: dict) -> None:
    log("[4/5] Webhook OTA — room_type_id sans mapping (422 MAPPING_ERROR)")
    body = {
        "ota_reference": f"SPRINT7-UNMAPPED-{uuid.uuid4().hex[:8]}",
        "property_id": "riad-yasmine-12345",
        "room_type_id": "does-not-exist-room-type",
        "guest_name": "Sprint7 Unmapped",
        "check_in": "2027-11-01", "check_out": "2027-11-03",
        "adults": 1, "children": 0, "total_amount": 500, "currency": "MAD", "status": "new",
    }
    raw = json.dumps(body).encode("utf-8")
    signature = hmac.new(WEBHOOK_HMAC_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()

    resp = await client.post(
        f"{CHANNEL_URL}/api/v1/channel/webhook/booking_com",
        params={"establishment_id": RIAD_YASMINE_ID},
        headers={"X-OTA-Signature": signature, "Content-Type": "application/json"},
        content=raw,
    )
    assert resp.status_code == 422, f"expected 422, got {resp.status_code}: {resp.text}"
    assert resp.json()["detail"]["code"] == "MAPPING_ERROR", resp.json()
    log("    -> correctly rejected (422 MAPPING_ERROR)")


# ------------------------------------------------------- 5. Option expiry


async def test_option_expiry(client: httpx.AsyncClient, headers: dict) -> None:
    log("[5/5] Expiration automatique d'une option (boucle asyncio, ~60s de patience)")
    check_in = "2027-12-01"
    check_out = "2027-12-03"

    booking = (await client.post(
        f"{RESERVATION_URL}/api/v1/bookings", headers=headers,
        json={
            "establishment_id": RIAD_YASMINE_ID, "market_segment_category": "DIRECT",
            "room_category": "Chambre Deluxe", "check_in_date": check_in, "check_out_date": check_out,
            "regime": "BB", "taxes_payment_mode": "on_site", "adults": 1,
            "customer": {"first_name": "Sprint7", "last_name": "OptionExpiry"},
            "source": "walk_in", "deposit_paid": False,
        },
    )).json()
    assert booking["status"] == "status_option", booking
    log(f"    -> booking={booking['id']} created as status_option")

    run_sql("reserv_db", f"UPDATE bookings SET option_expiry_date = now() - interval '1 minute' WHERE id = '{booking['id']}';")
    log("    -> option_expiry_date backdated, waiting for the poll loop to expire it")

    expired = False
    for _ in range(20):
        current = (await client.get(f"{RESERVATION_URL}/api/v1/bookings/{booking['id']}", headers=headers)).json()
        if current["status"] == "status_cancelled":
            expired = True
            break
        await asyncio.sleep(5)
    assert expired, f"expected status_cancelled after expiry, got {current['status']}"
    log("    -> option correctly auto-expired to status_cancelled")


async def main() -> None:
    async with httpx.AsyncClient(timeout=20.0) as client:
        token = await get_token(client, "sidi.omar", "ChangeMe123!")
        headers = {"Authorization": f"Bearer {token}"}

        await test_night_audit_discrepancy(client, headers)
        await test_room_shift_conflict(client, headers)
        await test_double_booking_concurrency(client, headers)
        await test_ota_webhook_unmapped(client, headers)
        await test_option_expiry(client, headers)

    print("\n==> Sprint 7 integration edge-case tests: ALL PASSED")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AssertionError as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
