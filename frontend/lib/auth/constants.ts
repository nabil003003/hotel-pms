export const COOKIE_ACCESS_TOKEN = "amh_access_token";
export const COOKIE_REFRESH_TOKEN = "amh_refresh_token";
export const COOKIE_ID_TOKEN = "amh_id_token";
export const COOKIE_SESSION = "amh_session"; // claims non sensibles, lisibles côté client
export const COOKIE_PKCE_VERIFIER = "amh_pkce_verifier";
export const COOKIE_PKCE_STATE = "amh_pkce_state";
export const COOKIE_PHONE_LINK_TOKEN = "amh_phone_link_token";
export const COOKIE_LOGIN_LINK_TOKEN = "amh_login_link_token";

export const KEYCLOAK_URL = process.env.KEYCLOAK_URL ?? "http://localhost:8080";
export const KEYCLOAK_REALM = process.env.KEYCLOAK_REALM ?? "amh-hospitality";
export const KEYCLOAK_CLIENT_ID = process.env.KEYCLOAK_CLIENT_ID ?? "pms-frontend";
export const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export interface SessionClaims {
  sub: string;
  email?: string;
  roles: string[];
  establishment_ids: string[];
  is_super_admin: boolean;
  exp: number;
}
