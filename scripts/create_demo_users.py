#!/usr/bin/env python3
"""Crée des comptes de démo simples (un par profil), en plus des comptes de
test existants (`sidi.omar`, `test.receptionniste`, etc. — voir
`keycloak_setup.py`). Demandé pour une démo rapide : email = mot de passe,
un compte par rôle métier réellement utilisé par le frontend (admin,
manager, receptionniste, gouvernante, femme_de_chambre). `comptable` et
`agence_externe` existent comme rôles Keycloak mais n'ont aucune interface
dédiée construite — pas de compte créé pour eux, ce serait une démo trompeuse.

Idempotent : relançable sans dupliquer/écraser les comptes existants (mot
de passe remis à jour si le compte existe déjà, pour rester cohérent si ce
script est relancé après modification de DEMO_USERS).

Usage: python scripts/create_demo_users.py
Prérequis : Keycloak démarré + realm déjà provisionné (keycloak_setup.py)
+ RIAD_YASMINE_ID connu (créé par seed_sprint1.sh).
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

KEYCLOAK_URL = "http://localhost:8080"
REALM = "amh-hospitality"
RIAD_YASMINE_ID = "4f9cb82b-4ded-491c-b85d-ba2cd6d36fda"

DEMO_USERS = [
    {"email": "admin@amh.com", "role": "admin", "is_super_admin": False},
    {"email": "manager@amh.com", "role": "manager", "is_super_admin": False},
    {"email": "receptionniste@amh.com", "role": "receptionniste", "is_super_admin": False},
    {"email": "gouvernante@amh.com", "role": "gouvernante", "is_super_admin": False},
    {"email": "femmedechambre@amh.com", "role": "femme_de_chambre", "is_super_admin": False},
]


def request(method: str, path: str, token: str, body: dict | list | None = None) -> tuple[int, dict | list | None]:
    url = f"{KEYCLOAK_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, (json.loads(raw) if raw else None)


def get_master_admin_token() -> str:
    data = "grant_type=password&client_id=admin-cli&username=admin&password=admin_dev_password"
    req = urllib.request.Request(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data=data.encode(), method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def find_user_id(token: str, email: str) -> str | None:
    status, body = request("GET", f"/admin/realms/{REALM}/users?username={email}&exact=true", token)
    if status == 200 and body:
        return body[0]["id"]
    return None


def main() -> None:
    token = get_master_admin_token()

    for user in DEMO_USERS:
        email = user["email"]
        user_id = find_user_id(token, email)

        if user_id is None:
            payload = {
                "username": email,
                "email": email,
                "enabled": True,
                "emailVerified": True,
                "attributes": {
                    "is_super_admin": ["true" if user["is_super_admin"] else "false"],
                    "establishment_ids": [RIAD_YASMINE_ID],
                },
                "credentials": [{"type": "password", "value": email, "temporary": False}],
            }
            status, body = request("POST", f"/admin/realms/{REALM}/users", token, payload)
            if status not in (201, 204):
                print(f"FAILED to create {email}: {status} {body}", file=sys.stderr)
                continue
            user_id = find_user_id(token, email)
            print(f"Created {email}")
        else:
            # Idempotent re-run: keep password/attributes in sync with DEMO_USERS.
            request("PUT", f"/admin/realms/{REALM}/users/{user_id}", token, {
                "attributes": {
                    "is_super_admin": ["true" if user["is_super_admin"] else "false"],
                    "establishment_ids": [RIAD_YASMINE_ID],
                },
            })
            request("PUT", f"/admin/realms/{REALM}/users/{user_id}/reset-password", token, {
                "type": "password", "value": email, "temporary": False,
            })
            print(f"Already existed, refreshed: {email}")

        role_status, role = request("GET", f"/admin/realms/{REALM}/roles/{user['role']}", token)
        if role_status == 200:
            request("POST", f"/admin/realms/{REALM}/users/{user_id}/role-mappings/realm", token, [role])

    print("\nDemo accounts ready (password = email):")
    for user in DEMO_USERS:
        print(f"  {user['email']}  /  {user['email']}   (role={user['role']})")


if __name__ == "__main__":
    main()
