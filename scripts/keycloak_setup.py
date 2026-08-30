#!/usr/bin/env python3
"""Provisionne le realm `amh-hospitality` via l'API Admin Keycloak.

Remplace l'approche initiale (--import-realm avec un realm-export.json écrit
à la main), qui faisait échouer le Direct Grant avec l'erreur interne
Keycloak "resolve_required_actions".

Root cause identifiée empiriquement (Sprint 1, image
quay.io/keycloak/keycloak:24.0 / Keycloak 24.0.5) : CE N'ÉTAIT PAS un
problème de scopes/flows implicites manquants dans un realm importé — un
realm flambant neuf créé proprement via `POST /admin/realms` (aucune
customisation, un seul utilisateur simple) reproduit EXACTEMENT la même
erreur. Le bug touche donc N'IMPORTE QUEL realm autre que `master` sur cette
version d'image : la résolution des required actions plante pour tout
utilisateur, même sans aucune required action qui lui soit assignée.
Contournement vérifié : désactiver (`enabled: false`) la totalité des
required actions du realm (`disable_required_actions()` ci-dessous) fait
disparaître l'erreur. Aucune n'est nécessaire en Sprint 1 (WebAuthn réel est
Sprint 6+, D4) — à réévaluer si l'image Keycloak est mise à jour vers une
version corrigée.

Usage :
    python scripts/keycloak_setup.py

Idempotent : peut être relancé sans dupliquer realm/clients/roles/users
existants (vérifie l'existence avant de créer).
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

KEYCLOAK_URL = "http://localhost:8080"
REALM = "amh-hospitality"

# RP ID du policy WebAuthn Passwordless (biom.txt) — doit correspondre au host
# qui sert réellement la page de login hébergée par Keycloak. En dev c'est
# "localhost" (KC_HOSTNAME). En prod, biom.txt fixe `pms.amhhospitality.com`,
# ce qui suppose que Keycloak soit atteignable sous ce même domaine parent au
# moment du login — pas encore le cas (Kong ne proxy pas Keycloak, voir
# infra/kong/kong.yml) : à ajuster avec le vrai hostname avant mise en prod.
WEBAUTHN_RP_ID = "localhost"
WEBAUTHN_RP_ENTITY_NAME = "AMH Hospitality PMS"

REALM_ROLES = [
    "femme_de_chambre",
    "gouvernante",
    "receptionniste",
    "manager",
    "admin",
    "comptable",
    "agence_externe",
]

CLIENTS = [
    {
        "clientId": "pms-frontend",
        "publicClient": True,
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": True,  # dev only — smoke tests. Désactiver en prod (D4).
        "serviceAccountsEnabled": False,
        "redirectUris": [
            "http://localhost:3000/api/auth/callback",
            "https://pms-dev.amhhospitality.com/api/auth/callback",
        ],
        "webOrigins": ["http://localhost:3000", "https://pms-dev.amhhospitality.com"],
        # "post.logout.redirect.uris" (séparé de "redirectUris" ci-dessus,
        # Keycloak 24 le valide indépendamment) manquait — sans lui,
        # /api/auth/logout redirigeait vers /realms/.../logout mais Keycloak
        # ignorait silencieusement post_logout_redirect_uri (non enregistré)
        # et ne terminait jamais vraiment la session SSO : bug réel trouvé
        # en testant le logout, corrigé ici pour toute nouvelle provision de
        # realm (les clients déjà créés doivent être patchés séparément, ce
        # script ne met pas à jour un client existant).
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "post.logout.redirect.uris": "http://localhost:3000/*##https://pms-dev.amhhospitality.com/*",
        },
    },
    {
        "clientId": "pms-mobile",
        "publicClient": True,
        "standardFlowEnabled": True,
        "serviceAccountsEnabled": False,
        "redirectUris": ["amhpms://callback"],
        "attributes": {"pkce.code.challenge.method": "S256"},
    },
    {
        "clientId": "svc-auth-gateway",
        "publicClient": False,
        "secret": "dev-secret-auth-gateway",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-establishment",
        "publicClient": False,
        "secret": "dev-secret-establishment",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-housekeeping",
        "publicClient": False,
        "secret": "dev-secret-housekeeping",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-pricing",
        "publicClient": False,
        "secret": "dev-secret-pricing",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-partner",
        "publicClient": False,
        "secret": "dev-secret-partner",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-channel-manager",
        "publicClient": False,
        "secret": "dev-secret-channel-manager",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-reservation",
        "publicClient": False,
        "secret": "dev-secret-reservation",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-frontoffice",
        "publicClient": False,
        "secret": "dev-secret-frontoffice",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-analytics",
        "publicClient": False,
        "secret": "dev-secret-analytics",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-nightaudit",
        "publicClient": False,
        "secret": "dev-secret-nightaudit",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
    {
        "clientId": "svc-notification",
        "publicClient": False,
        "secret": "dev-secret-notification",
        "standardFlowEnabled": False,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
    },
]

TEST_USERS = [
    {
        "username": "sidi.omar",
        "email": "sidi.omar@amhhospitality.com",
        "role": "admin",
        "is_super_admin": True,
    },
    {
        "username": "test.receptionniste",
        "email": "reception@riadyasmine.amhhospitality.com",
        "role": "receptionniste",
        "is_super_admin": False,
    },
    {
        "username": "test.gouvernante",
        "email": "gouvernante@riadyasmine.amhhospitality.com",
        "role": "gouvernante",
        "is_super_admin": False,
    },
    {
        "username": "test.femmedechambre",
        "email": "femme.chambre@riadyasmine.amhhospitality.com",
        "role": "femme_de_chambre",
        "is_super_admin": False,
    },
]

TEST_PASSWORD = "ChangeMe123!"


def request(method: str, path: str, token: str | None = None, body: dict | list | None = None) -> tuple[int, dict | list | None]:
    url = f"{KEYCLOAK_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw.decode("utf-8", errors="replace")}


def get_location_id(path_prefix: str, token: str, search_field: str, search_value: str) -> str | None:
    status, body = request("GET", f"{path_prefix}?{search_field}={search_value}&exact=true", token)
    if status == 200 and body:
        return body[0]["id"]
    return None


def wait_for_keycloak() -> None:
    for _ in range(60):
        try:
            with urllib.request.urlopen(f"{KEYCLOAK_URL}/realms/master") as resp:
                if resp.status == 200:
                    return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    raise SystemExit("Keycloak did not become reachable in time")


def get_master_admin_token() -> str:
    data = "&".join(
        [
            "grant_type=password",
            "client_id=admin-cli",
            "username=admin",
            "password=admin_dev_password",
        ]
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def ensure_realm(token: str) -> None:
    status, _ = request("GET", f"/admin/realms/{REALM}", token)
    if status == 200:
        print(f"Realm '{REALM}' already exists, skipping creation.")
        return
    status, body = request(
        "POST",
        "/admin/realms",
        token,
        {"realm": REALM, "enabled": True, "registrationAllowed": False, "loginTheme": "amh-hospitality"},
    )
    if status not in (201, 204):
        raise SystemExit(f"Failed to create realm: {status} {body}")
    print(f"Realm '{REALM}' created.")


def enable_unmanaged_attributes(token: str) -> None:
    """Keycloak 24 introduit le "User Profile" déclaratif : par défaut
    (`unmanagedAttributePolicy: None`), toute attribut utilisateur non
    déclaré explicitement dans le schéma (seuls username/email/firstName/
    lastName le sont par défaut) est silencieusement ignoré à l'écriture —
    `establishment_ids`/`is_super_admin` (D2) ne persistaient pas du tout
    sans ce correctif, confirmé empiriquement en vérification Sprint 1."""
    status, profile = request("GET", f"/admin/realms/{REALM}/users/profile", token)
    if status != 200:
        print(f"  WARNING: could not read user profile config: {status}")
        return
    if profile.get("unmanagedAttributePolicy") == "ENABLED":
        return
    profile["unmanagedAttributePolicy"] = "ENABLED"
    status, _ = request("PUT", f"/admin/realms/{REALM}/users/profile", token, profile)
    if status not in (200, 204):
        print(f"  WARNING: failed to enable unmanaged attributes: {status}")
    else:
        print("Unmanaged user attributes enabled (required for establishment_ids/is_super_admin).")


def configure_webauthn_policy(token: str) -> None:
    """Policy WebAuthn Passwordless (biom.txt §Flux A/B) : clé résidente
    (discoverable credential, nécessaire pour `allowCredentials` vide côté
    login QR) + user verification obligatoire (Face ID/empreinte, jamais
    juste "present"). GET-modifie-PUT sur la représentation complète du
    realm pour ne pas écraser les autres champs (même précaution que
    enable_unmanaged_attributes ci-dessus).

    `authenticatorAttachment` volontairement "not specified", PAS
    "cross-platform" : forcer cross-platform empêche le navigateur d'offrir
    le capteur intégré de l'appareil qui exécute la cérémonie — testé en
    vrai sur téléphone (Chrome Android), le bouton "Lier mon téléphone"
    échouait systématiquement avec NotAllowedError car Android refuse
    d'utiliser son propre capteur d'empreinte quand le site exige
    explicitement un authenticator externe. "not specified" laisse le
    navigateur/OS choisir : capteur intégré sur téléphone (Flux A), QR
    cross-device sur desktop sans capteur (Flux B) — les deux cas de
    biom.txt restent couverts."""
    status, realm = request("GET", f"/admin/realms/{REALM}", token)
    if status != 200:
        print(f"  WARNING: could not read realm config: {status}")
        return
    realm.update(
        {
            "webAuthnPolicyPasswordlessRpEntityName": WEBAUTHN_RP_ENTITY_NAME,
            "webAuthnPolicyPasswordlessRpId": WEBAUTHN_RP_ID,
            "webAuthnPolicyPasswordlessSignatureAlgorithms": ["ES256", "RS256"],
            "webAuthnPolicyPasswordlessAttestationConveyancePreference": "none",
            "webAuthnPolicyPasswordlessAuthenticatorAttachment": "not specified",
            "webAuthnPolicyPasswordlessRequireResidentKey": "Yes",
            "webAuthnPolicyPasswordlessUserVerificationRequirement": "required",
            "webAuthnPolicyPasswordlessCreateTimeout": 120,
            "webAuthnPolicyPasswordlessAvoidSameAuthenticatorRegister": False,
            # Nécessaire pour que infra/keycloak/themes/amh-hospitality/login/
            # messages/messages_fr.properties soit réellement servi — sans
            # internationalisation activée, Keycloak sert toujours l'anglais
            # du thème parent quel que soit le fichier _fr présent.
            "internationalizationEnabled": True,
            "supportedLocales": ["fr", "en"],
            "defaultLocale": "fr",
        }
    )
    status, body = request("PUT", f"/admin/realms/{REALM}", token, realm)
    if status not in (204, 200):
        print(f"  WARNING: failed to set WebAuthn passwordless policy: {status} {body}")
    else:
        print(f"WebAuthn passwordless policy configured (rpId={WEBAUTHN_RP_ID}).")


def configure_events(token: str) -> None:
    """Active les login events realm (§ auth_audit_log) — sans ça
    `GET /admin/realms/{realm}/events` renvoie toujours une liste vide,
    même après un login réel."""
    status, config = request("GET", f"/admin/realms/{REALM}/events/config", token)
    if status != 200:
        print(f"  WARNING: could not read events config: {status}")
        return
    if config.get("eventsEnabled") and config.get("adminEventsEnabled"):
        return
    config["eventsEnabled"] = True
    config["adminEventsEnabled"] = True
    config["eventsExpiration"] = 2592000  # 30 jours
    status, body = request("PUT", f"/admin/realms/{REALM}/events/config", token, config)
    if status not in (204, 200):
        print(f"  WARNING: failed to enable realm events: {status} {body}")
    else:
        print("Realm login events enabled (auth_audit_log polling source).")


def configure_browser_flow_webauthn(token: str) -> None:
    """Recette standard Keycloak "Passwordless" : copie le flow `browser`,
    passe le sous-flow `forms` (username/password) en ALTERNATIVE, et ajoute
    `WebAuthn Passwordless Authenticator` en ALTERNATIVE au niveau racine —
    mais PAS nu : dans un sous-flow gardé par `Condition - user configured`
    (même mécanisme que le sous-flow OTP conditionnel déjà présent dans le
    flow `browser` stock). Sans cette garde, le thème classic déclenche
    navigator.credentials.get() automatiquement dès que la page se charge,
    y compris pour un utilisateur SANS aucun credential WebAuthn — ça échoue
    aussitôt (NotAllowedError) et fait échouer tout le flow au lieu de
    retomber sur le formulaire mot de passe, cassant au passage kc_action
    (bug réel constaté en test navigateur : "Lier mon téléphone" first-time
    renvoyait kc_action_status=error sans jamais montrer l'écran
    d'enregistrement). Comportement obtenu avec la garde : un utilisateur
    SANS credential saute directement le sous-flow WebAuthn (condition
    fausse) et passe par le formulaire ou par le required action demandé
    via kc_action ; un utilisateur AVEC credential est invité à
    s'authentifier via WebAuthn (QR cross-device si "cross-platform" +
    resident key, cf. configure_webauthn_policy).
    N'A PAS BESOIN de required actions (donc pas concerné par le bug
    Keycloak 24.0.5 documenté dans disable_required_actions ci-dessous) : ce
    sont des executions de flow, une sous-partie différente de l'API."""
    new_flow_alias = "browser-webauthn"

    status, flows = request("GET", f"/admin/realms/{REALM}/authentication/flows", token)
    if status != 200:
        print(f"  WARNING: could not list authentication flows: {status}")
        return
    already_exists = any(f["alias"] == new_flow_alias for f in flows)

    if not already_exists:
        status, body = request(
            "POST",
            f"/admin/realms/{REALM}/authentication/flows/browser/copy",
            token,
            {"newName": new_flow_alias},
        )
        if status not in (201, 204):
            print(f"  WARNING: failed to copy browser flow: {status} {body}")
            return
        print(f"Authentication flow '{new_flow_alias}' created (copy of 'browser').")

    status, executions = request(
        "GET", f"/admin/realms/{REALM}/authentication/flows/{new_flow_alias}/executions", token
    )
    if status != 200:
        print(f"  WARNING: could not list executions of '{new_flow_alias}': {status}")
        return

    forms_execution = next(
        (
            e
            for e in executions
            if e.get("level") == 0 and e.get("authenticationFlow") and "forms" in e.get("displayName", "").lower()
        ),
        None,
    )
    if forms_execution and forms_execution.get("requirement") != "ALTERNATIVE":
        forms_execution["requirement"] = "ALTERNATIVE"
        status, body = request(
            "PUT", f"/admin/realms/{REALM}/authentication/flows/{new_flow_alias}/executions", token, forms_execution
        )
        # Keycloak 24.0 renvoie 202 (pas 204) sur ce endpoint précis, constaté
        # empiriquement en vérification — l'update est bien appliquée malgré
        # le code inhabituel.
        if status not in (200, 202, 204):
            print(f"  WARNING: failed to set 'forms' subflow to ALTERNATIVE: {status} {body}")
    elif not forms_execution:
        print(f"  WARNING: could not locate 'forms' subflow inside '{new_flow_alias}' — leaving as-is.")

    # Un utilisateur SANS credential WebAuthn (cas "Lier mon téléphone", 1re
    # fois) passe aussi par ce flow via kc_action — s'il exécute quand même
    # l'authenticator WebAuthn (comme une ALTERNATIVE nue le ferait, bug
    # constaté empiriquement : le thème classic déclenche
    # navigator.credentials.get() automatiquement au chargement de la page),
    # ça échoue immédiatement (NotAllowedError, aucun credential à
    # présenter) et Keycloak abandonne TOUT le flow — kc_action_status=error,
    # jamais d'écran d'enregistrement. Recette officielle Keycloak
    # "Passwordless" (déjà utilisée par le sous-flow OTP du flow `browser`
    # stock) : ne tenter l'authenticator QUE si l'utilisateur a déjà un
    # credential de ce type, via un sous-flow gardé par
    # `conditional-user-configured`.
    stray_top_level = next(
        (
            e
            for e in executions
            if e.get("level") == 0 and e.get("providerId") == "webauthn-authenticator-passwordless"
        ),
        None,
    )
    if stray_top_level:
        status, _ = request(
            "DELETE", f"/admin/realms/{REALM}/authentication/executions/{stray_top_level['id']}", token
        )
        if status in (204, 200):
            print("Removed unguarded top-level WebAuthn execution (replaced by conditional subflow below).")
        else:
            print(f"  WARNING: failed to remove stray top-level WebAuthn execution: {status}")
        status, executions = request(
            "GET", f"/admin/realms/{REALM}/authentication/flows/{new_flow_alias}/executions", token
        )

    webauthn_subflow_alias = f"{new_flow_alias} WebAuthn Passwordless"
    # L'alias contient des espaces — nécessaire dans le path d'URL admin REST.
    webauthn_subflow_alias_url = urllib.parse.quote(webauthn_subflow_alias, safe="")
    webauthn_subflow = next(
        (
            e
            for e in executions
            if e.get("level") == 0 and e.get("authenticationFlow") and e.get("displayName") == webauthn_subflow_alias
        ),
        None,
    )
    if not webauthn_subflow:
        status, body = request(
            "POST",
            f"/admin/realms/{REALM}/authentication/flows/{new_flow_alias}/executions/flow",
            token,
            {"alias": webauthn_subflow_alias, "type": "basic-flow", "description": "WebAuthn passwordless, gated on existing credential"},
        )
        if status not in (201, 204):
            print(f"  WARNING: failed to create WebAuthn conditional subflow: {status} {body}")
            return
        print(f"Subflow '{webauthn_subflow_alias}' created under '{new_flow_alias}'.")
        status, executions = request(
            "GET", f"/admin/realms/{REALM}/authentication/flows/{new_flow_alias}/executions", token
        )
        webauthn_subflow = next(
            (e for e in executions if e.get("level") == 0 and e.get("displayName") == webauthn_subflow_alias), None
        )

    if webauthn_subflow and webauthn_subflow.get("requirement") != "ALTERNATIVE":
        webauthn_subflow["requirement"] = "ALTERNATIVE"
        status, body = request(
            "PUT", f"/admin/realms/{REALM}/authentication/flows/{new_flow_alias}/executions", token, webauthn_subflow
        )
        if status not in (200, 202, 204):
            print(f"  WARNING: failed to set WebAuthn subflow to ALTERNATIVE: {status} {body}")

    condition_execution = next(
        (e for e in executions if e.get("providerId") == "conditional-user-configured" and e.get("level") == 1),
        None,
    )
    if not condition_execution:
        status, body = request(
            "POST",
            f"/admin/realms/{REALM}/authentication/flows/{webauthn_subflow_alias_url}/executions/execution",
            token,
            {"provider": "conditional-user-configured"},
        )
        if status not in (201, 204):
            print(f"  WARNING: failed to add 'Condition - user configured' execution: {status} {body}")
            return
        status, executions = request(
            "GET", f"/admin/realms/{REALM}/authentication/flows/{new_flow_alias}/executions", token
        )
        condition_execution = next(
            (e for e in executions if e.get("providerId") == "conditional-user-configured" and e.get("level") == 1),
            None,
        )

    if condition_execution and condition_execution.get("requirement") != "REQUIRED":
        condition_execution["requirement"] = "REQUIRED"
        status, body = request(
            "PUT",
            f"/admin/realms/{REALM}/authentication/flows/{webauthn_subflow_alias_url}/executions",
            token,
            condition_execution,
        )
        if status not in (200, 202, 204):
            print(f"  WARNING: failed to set condition execution to REQUIRED: {status} {body}")

    webauthn_execution = next(
        (e for e in executions if e.get("providerId") == "webauthn-authenticator-passwordless" and e.get("level") == 1),
        None,
    )
    if not webauthn_execution:
        status, body = request(
            "POST",
            f"/admin/realms/{REALM}/authentication/flows/{webauthn_subflow_alias_url}/executions/execution",
            token,
            {"provider": "webauthn-authenticator-passwordless"},
        )
        if status not in (201, 204):
            print(f"  WARNING: failed to add WebAuthn Passwordless Authenticator execution: {status} {body}")
            return
        status, executions = request(
            "GET", f"/admin/realms/{REALM}/authentication/flows/{new_flow_alias}/executions", token
        )
        webauthn_execution = next(
            (
                e
                for e in executions
                if e.get("providerId") == "webauthn-authenticator-passwordless" and e.get("level") == 1
            ),
            None,
        )

    if webauthn_execution and webauthn_execution.get("requirement") != "REQUIRED":
        webauthn_execution["requirement"] = "REQUIRED"
        status, body = request(
            "PUT",
            f"/admin/realms/{REALM}/authentication/flows/{webauthn_subflow_alias_url}/executions",
            token,
            webauthn_execution,
        )
        if status not in (200, 202, 204):
            print(f"  WARNING: failed to set WebAuthn execution to REQUIRED: {status} {body}")
        else:
            print("WebAuthn Passwordless Authenticator added, gated behind 'Condition - user configured'.")

    status, realm = request("GET", f"/admin/realms/{REALM}", token)
    if status == 200 and realm.get("browserFlow") != new_flow_alias:
        realm["browserFlow"] = new_flow_alias
        status, body = request("PUT", f"/admin/realms/{REALM}", token, realm)
        if status not in (204, 200):
            print(f"  WARNING: failed to bind '{new_flow_alias}' as browser flow: {status} {body}")
        else:
            print(f"Realm browser flow set to '{new_flow_alias}'.")


def disable_required_actions(token: str) -> None:
    """Contournement du bug Keycloak 24.0.5 décrit en tête de fichier —
    désactive toutes les required actions pour que la résolution ne plante
    plus au login (Direct Grant ou Authorization Code)."""
    status, actions = request("GET", f"/admin/realms/{REALM}/authentication/required-actions", token)
    if status != 200:
        print(f"  WARNING: could not list required actions: {status}")
        return
    for action in actions:
        if not action.get("enabled"):
            continue
        action["enabled"] = False
        status, _ = request(
            "PUT",
            f"/admin/realms/{REALM}/authentication/required-actions/{action['alias']}",
            token,
            action,
        )
        if status not in (204, 201):
            print(f"  WARNING: failed to disable required action {action['alias']}: {status}")
    print("Required actions disabled (Keycloak 24.0.5 workaround, see module docstring).")


def enable_required_action(token: str, alias: str) -> None:
    """Réactive une required action précise après le disable_required_actions()
    global ci-dessus, sans revenir sur le contournement pour les autres."""
    status, action = request("GET", f"/admin/realms/{REALM}/authentication/required-actions/{alias}", token)
    if status != 200:
        print(f"  WARNING: could not read {alias} required action: {status}")
        return
    if action.get("enabled"):
        return
    action["enabled"] = True
    status, body = request(
        "PUT", f"/admin/realms/{REALM}/authentication/required-actions/{alias}", token, action
    )
    if status not in (204, 201):
        print(f"  WARNING: failed to enable {alias} required action: {status} {body}")
    else:
        print(f"'{alias}' required action re-enabled.")


def enable_webauthn_register_required_action(token: str) -> None:
    """Active webauthn-register et webauthn-register-passwordless (biom.txt Flux A).
    Safe : defaultAction est false, déclenché uniquement via kc_action."""
    enable_required_action(token, "webauthn-register")
    enable_required_action(token, "webauthn-register-passwordless")


def enable_update_password_required_action(token: str) -> None:
    """`UPDATE_PASSWORD` — contrairement à webauthn-register-passwordless
    ci-dessus, CETTE action est explicitement mise dans `requiredActions` de
    chaque nouvel utilisateur par KeycloakAdminClient.create_user (mot de
    passe temporaire à changer au premier login) : c'est exactement le
    scénario que le bug Keycloak 24.0.5 documenté en tête de fichier visait
    à l'origine. Vérifié empiriquement avant activation (spike Sprint biom) :
    un utilisateur fraîchement créé avec UPDATE_PASSWORD dans ses
    requiredActions atteint bien l'écran de changement de mot de passe sans
    crash 500, et les utilisateurs existants sans required action assignée
    continuent de se logger normalement — le bug ne se reproduit pas sur
    cette version d'image pour ce scénario précis."""
    enable_required_action(token, "UPDATE_PASSWORD")


def ensure_roles(token: str) -> None:
    for role in REALM_ROLES:
        status, _ = request("GET", f"/admin/realms/{REALM}/roles/{role}", token)
        if status == 200:
            continue
        status, body = request("POST", f"/admin/realms/{REALM}/roles", token, {"name": role})
        if status not in (201, 204):
            raise SystemExit(f"Failed to create role {role}: {status} {body}")
        print(f"Role created: {role}")


def ensure_client_scope(token: str) -> str:
    scopes_status, scopes = request("GET", f"/admin/realms/{REALM}/client-scopes", token)
    existing = next((s for s in scopes if s["name"] == "amh-tenant"), None) if scopes_status == 200 else None
    if existing:
        return existing["id"]

    payload = {
        "name": "amh-tenant",
        "protocol": "openid-connect",
        "attributes": {"include.in.token.scope": "true", "display.on.consent.screen": "false"},
        "protocolMappers": [
            {
                "name": "establishment_ids",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "consentRequired": False,
                "config": {
                    "user.attribute": "establishment_ids",
                    "claim.name": "establishment_ids",
                    "jsonType.label": "String",
                    "multivalued": "true",
                    "id.token.claim": "true",
                    "access.token.claim": "true",
                    "userinfo.token.claim": "true",
                },
            },
            {
                "name": "is_super_admin",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "consentRequired": False,
                "config": {
                    "user.attribute": "is_super_admin",
                    "claim.name": "is_super_admin",
                    "jsonType.label": "boolean",
                    "id.token.claim": "true",
                    "access.token.claim": "true",
                    "userinfo.token.claim": "true",
                },
            },
        ],
    }
    status, body = request("POST", f"/admin/realms/{REALM}/client-scopes", token, payload)
    if status not in (201, 204):
        raise SystemExit(f"Failed to create amh-tenant client scope: {status} {body}")
    print("Client scope 'amh-tenant' created.")

    # NB : contrairement à /clients (?clientId=) et /users (?username=),
    # l'endpoint /client-scopes IGNORE silencieusement les query params de
    # filtre et retourne toujours la liste complète — get_location_id()
    # (qui suppose un filtre serveur) y renverrait le premier scope de la
    # liste au hasard. Recherche manuelle par nom dans la liste complète.
    _, all_scopes = request("GET", f"/admin/realms/{REALM}/client-scopes", token)
    created = next((s for s in all_scopes if s["name"] == "amh-tenant"), None)
    if not created:
        raise SystemExit("amh-tenant client scope created but not found on re-list")
    return created["id"]


def ensure_clients(token: str, amh_tenant_scope_id: str) -> dict[str, str]:
    client_ids: dict[str, str] = {}
    for client_def in CLIENTS:
        client_id_name = client_def["clientId"]
        existing_id = get_location_id(f"/admin/realms/{REALM}/clients", token, "clientId", client_id_name)
        if existing_id:
            client_ids[client_id_name] = existing_id
            continue

        status, body = request("POST", f"/admin/realms/{REALM}/clients", token, client_def)
        if status not in (201, 204):
            raise SystemExit(f"Failed to create client {client_id_name}: {status} {body}")

        internal_id = get_location_id(f"/admin/realms/{REALM}/clients", token, "clientId", client_id_name)
        client_ids[client_id_name] = internal_id
        print(f"Client created: {client_id_name}")

        # Attache amh-tenant comme default client scope (D2)
        status, _ = request(
            "PUT",
            f"/admin/realms/{REALM}/clients/{internal_id}/default-client-scopes/{amh_tenant_scope_id}",
            token,
        )
        if status not in (204, 201):
            print(f"  WARNING: failed to attach amh-tenant scope to {client_id_name}: {status}")

    return client_ids


def assign_service_account_realm_management_roles(token: str, svc_auth_gateway_client_id: str) -> None:
    status, sa_user = request(
        "GET", f"/admin/realms/{REALM}/clients/{svc_auth_gateway_client_id}/service-account-user", token
    )
    if status != 200:
        print(f"  WARNING: could not fetch service account user for svc-auth-gateway: {status}")
        return
    sa_user_id = sa_user["id"]

    rm_client_id = get_location_id(f"/admin/realms/{REALM}/clients", token, "clientId", "realm-management")
    if not rm_client_id:
        print("  WARNING: realm-management client not found")
        return

    # "view-events" pour app/infrastructure/audit_poller.py (biom.txt
    # auth_audit_log). "view-realm" pour KeycloakAdminClient.create_user
    # (lookup GET /roles/{role} avant assignation, provision_user) — sans
    # lui, la création d'un worker via POST /api/v1/auth/users échoue en 500
    # (403 Keycloak sur la lecture du rôle) : bug pré-existant, jamais
    # exercé de bout en bout avant vérification biom.txt (ensure_users
    # ci-dessous utilise le token admin-cli du realm master, un chemin
    # différent qui masquait le problème). manage-users/view-users seuls ne
    # couvrent pas la lecture de rôle — constaté empiriquement.
    for role_name in ["manage-users", "view-users", "view-events", "view-realm"]:
        status, role = request(
            "GET", f"/admin/realms/{REALM}/clients/{rm_client_id}/roles/{role_name}", token
        )
        if status != 200:
            continue
        request(
            "POST",
            f"/admin/realms/{REALM}/users/{sa_user_id}/role-mappings/clients/{rm_client_id}",
            token,
            [role],
        )
    print("svc-auth-gateway service account granted manage-users/view-users.")


def mark_service_account_super_admin(token: str, client_id: str, client_name: str, reason: str) -> None:
    status, sa_user = request("GET", f"/admin/realms/{REALM}/clients/{client_id}/service-account-user", token)
    if status != 200:
        print(f"  WARNING: could not fetch service account user for {client_name}: {status}")
        return
    sa_user["attributes"] = {**sa_user.get("attributes", {}), "is_super_admin": ["true"]}
    status, _ = request("PUT", f"/admin/realms/{REALM}/users/{sa_user['id']}", token, sa_user)
    if status not in (204, 201):
        print(f"  WARNING: failed to set is_super_admin on {client_name} service account: {status}")
    else:
        print(f"{client_name} service account marked is_super_admin=true ({reason}).")


def ensure_users(token: str) -> None:
    for user_def in TEST_USERS:
        existing_id = get_location_id(f"/admin/realms/{REALM}/users", token, "username", user_def["username"])
        if existing_id:
            print(f"User already exists, skipping: {user_def['username']}")
            continue

        payload = {
            "username": user_def["username"],
            "email": user_def["email"],
            "enabled": True,
            "emailVerified": True,
            "attributes": {
                "is_super_admin": ["true" if user_def["is_super_admin"] else "false"],
                "establishment_ids": [],
            },
            "credentials": [{"type": "password", "value": TEST_PASSWORD, "temporary": False}],
        }
        status, body = request("POST", f"/admin/realms/{REALM}/users", token, payload)
        if status not in (201, 204):
            raise SystemExit(f"Failed to create user {user_def['username']}: {status} {body}")

        user_id = get_location_id(f"/admin/realms/{REALM}/users", token, "username", user_def["username"])
        role_status, role = request("GET", f"/admin/realms/{REALM}/roles/{user_def['role']}", token)
        if role_status == 200:
            request("POST", f"/admin/realms/{REALM}/users/{user_id}/role-mappings/realm", token, [role])

        print(f"User created: {user_def['username']} (role={user_def['role']})")


def main() -> None:
    print("Waiting for Keycloak...")
    wait_for_keycloak()

    token = get_master_admin_token()
    ensure_realm(token)
    disable_required_actions(token)
    enable_webauthn_register_required_action(token)
    enable_update_password_required_action(token)
    enable_unmanaged_attributes(token)
    configure_webauthn_policy(token)
    configure_events(token)
    configure_browser_flow_webauthn(token)
    ensure_roles(token)
    scope_id = ensure_client_scope(token)
    client_ids = ensure_clients(token, scope_id)
    assign_service_account_realm_management_roles(token, client_ids["svc-auth-gateway"])
    mark_service_account_super_admin(token, client_ids["svc-housekeeping"], "svc-housekeeping", "D1 resync fallback")
    mark_service_account_super_admin(
        token, client_ids["svc-channel-manager"], "svc-channel-manager", "D3 ota_mappings REST lookup"
    )
    mark_service_account_super_admin(
        token, client_ids["svc-reservation"], "svc-reservation",
        "Sprint 3 cross-service calls to pricing/establishment/auth-gateway",
    )
    mark_service_account_super_admin(
        token, client_ids["svc-frontoffice"], "svc-frontoffice",
        "Sprint 4 cross-service calls to housekeeping/reservation/pricing",
    )
    mark_service_account_super_admin(
        token, client_ids["svc-analytics"], "svc-analytics",
        "Sprint 4 cross-service calls to reservation/establishment",
    )
    mark_service_account_super_admin(
        token, client_ids["svc-nightaudit"], "svc-nightaudit",
        "Sprint 5 cross-service calls to front-office/reservation/analytics/notification",
    )
    ensure_users(token)

    print("\nKeycloak setup complete.")
    print(f"Test users (password '{TEST_PASSWORD}'): {', '.join(u['username'] for u in TEST_USERS)}")


if __name__ == "__main__":
    main()
