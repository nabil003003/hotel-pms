#!/usr/bin/env python3
"""Configures Keycloak for Cloudflare Tunnel testing:
1. Updates client 'pms-frontend' redirectUris, webOrigins, and post.logout.redirect.uris with FRONTEND_TUNNEL
2. Enables required actions 'webauthn-register' and 'webauthn-register-passwordless'
3. Updates WebAuthn policies (standard and passwordless) with KEYCLOAK_TUNNEL rpId and full params
"""

import json
import urllib.parse
import urllib.request

KEYCLOAK_URL = "http://localhost:8080"
REALM = "amh-hospitality"

FRONTEND_TUNNEL = "https://rich-process-made-twelve.trycloudflare.com"
KEYCLOAK_HOSTNAME = "princess-power-investors-organization.trycloudflare.com"


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
    token = get_token()

    # 1. Update client pms-frontend
    status, clients = request("GET", f"/admin/realms/{REALM}/clients?clientId=pms-frontend", token)
    if status != 200 or not clients:
        raise SystemExit(f"Could not find pms-frontend client: {status} {clients}")
    
    client = clients[0]
    client_id = client["id"]
    
    redirect_uris = client.get("redirectUris", [])
    callback_url = f"{FRONTEND_TUNNEL}/api/auth/callback"
    if callback_url not in redirect_uris:
        redirect_uris.append(callback_url)
    
    web_origins = client.get("webOrigins", [])
    if FRONTEND_TUNNEL not in web_origins:
        web_origins.append(FRONTEND_TUNNEL)
    if "+" not in web_origins:
        web_origins.append("+")

    attributes = client.get("attributes", {})
    post_logout = attributes.get("post.logout.redirect.uris", "")
    tunnel_logout = f"{FRONTEND_TUNNEL}/*"
    if tunnel_logout not in post_logout:
        attributes["post.logout.redirect.uris"] = f"{post_logout}##{tunnel_logout}" if post_logout else tunnel_logout

    client["redirectUris"] = redirect_uris
    client["webOrigins"] = web_origins
    client["attributes"] = attributes

    status, resp = request("PUT", f"/admin/realms/{REALM}/clients/{client_id}", token, client)
    if status not in (200, 204):
        raise SystemExit(f"Failed to update client pms-frontend: {status} {resp}")
    print(f"Updated client 'pms-frontend' with redirectUri {callback_url} and webOrigin {FRONTEND_TUNNEL}")

    # 2. Enable required actions
    for action_alias in ["webauthn-register", "webauthn-register-passwordless"]:
        status, action = request("GET", f"/admin/realms/{REALM}/authentication/required-actions/{action_alias}", token)
        if status == 200 and not action.get("enabled"):
            action["enabled"] = True
            request("PUT", f"/admin/realms/{REALM}/authentication/required-actions/{action_alias}", token, action)
            print(f"Enabled required action '{action_alias}'")

    # 3. Update realm WebAuthn policies
    status, realm = request("GET", f"/admin/realms/{REALM}", token)
    if status != 200:
        raise SystemExit(f"Could not get realm info: {status} {realm}")
    
    realm.update({
        # Standard WebAuthn Policy (used by webauthn-register)
        "webAuthnPolicyRpEntityName": "AMH Hospitality PMS",
        "webAuthnPolicyRpId": KEYCLOAK_HOSTNAME,
        "webAuthnPolicySignatureAlgorithms": ["ES256", "RS256"],
        "webAuthnPolicyAttestationConveyancePreference": "none",
        "webAuthnPolicyAuthenticatorAttachment": "not specified",
        "webAuthnPolicyUserVerificationRequirement": "required",
        "webAuthnPolicyCreateTimeout": 120,
        "webAuthnPolicyAvoidSameAuthenticatorRegister": False,

        # Passwordless WebAuthn Policy (used by webauthn-register-passwordless)
        "webAuthnPolicyPasswordlessRpEntityName": "AMH Hospitality PMS",
        "webAuthnPolicyPasswordlessRpId": KEYCLOAK_HOSTNAME,
        "webAuthnPolicyPasswordlessSignatureAlgorithms": ["ES256", "RS256"],
        "webAuthnPolicyPasswordlessAttestationConveyancePreference": "none",
        "webAuthnPolicyPasswordlessAuthenticatorAttachment": "not specified",
        "webAuthnPolicyPasswordlessRequireResidentKey": "Yes",
        "webAuthnPolicyPasswordlessUserVerificationRequirement": "required",
        "webAuthnPolicyPasswordlessCreateTimeout": 120,
        "webAuthnPolicyPasswordlessAvoidSameAuthenticatorRegister": False,
    })

    status, resp = request("PUT", f"/admin/realms/{REALM}", token, realm)
    if status not in (200, 204):
        raise SystemExit(f"Failed to update realm WebAuthn policy: {status} {resp}")
    print(f"Updated realm '{REALM}' WebAuthn policies with rpId={KEYCLOAK_HOSTNAME}")


if __name__ == "__main__":
    main()
