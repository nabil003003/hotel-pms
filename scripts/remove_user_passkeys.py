#!/usr/bin/env python3
"""Removes WebAuthn / Passkey credentials for a specified user in Keycloak."""

import json
import sys
import urllib.parse
import urllib.request

KEYCLOAK_URL = "http://localhost:8080"
REALM = "amh-hospitality"
USERNAME = "sidi.omar"


def get_token():
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": "admin",
        "password": "admin_dev_password",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def request(method, path, token, body=None):
    headers = {"Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{KEYCLOAK_URL}{path}",
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else None


def main():
    target_username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    token = get_token()

    # Find user
    status, users = request("GET", f"/admin/realms/{REALM}/users?username={target_username}&exact=true", token)
    if status != 200 or not users:
        print(f"Error finding user '{target_username}': status={status}, users={users}")
        sys.exit(1)

    user_id = users[0]["id"]
    print(f"Found user '{target_username}' with ID: {user_id}")

    # Get credentials
    status, credentials = request("GET", f"/admin/realms/{REALM}/users/{user_id}/credentials", token)
    if status != 200:
        print(f"Error fetching credentials: status={status}, body={credentials}")
        sys.exit(1)

    print(f"Total credentials found for {target_username}: {len(credentials)}")
    removed_count = 0
    for cred in credentials:
        cred_type = cred.get("type", "")
        cred_id = cred.get("id")
        user_label = cred.get("userLabel", "")
        print(f" - Credential: type={cred_type}, id={cred_id}, label={user_label}")
        if "webauthn" in cred_type.lower():
            del_status, _ = request("DELETE", f"/admin/realms/{REALM}/users/{user_id}/credentials/{cred_id}", token)
            if del_status in (200, 204):
                print(f"   --> Successfully deleted passkey credential {cred_id} ({user_label})")
                removed_count += 1
            else:
                print(f"   --> Failed to delete credential {cred_id}: {del_status}")

    if removed_count == 0:
        print(f"No passkey / WebAuthn credentials found to remove for user '{target_username}'.")
    else:
        print(f"Successfully removed {removed_count} passkey credential(s) for user '{target_username}'.")


if __name__ == "__main__":
    main()
