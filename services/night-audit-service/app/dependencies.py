from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db as _get_db
from app.infrastructure.keycloak import TokenValidationError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    sub: str
    email: str | None = None
    roles: list[str] = field(default_factory=list)
    establishment_ids: list[str] = field(default_factory=list)
    is_super_admin: bool = False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    try:
        claims = await decode_access_token(credentials.credentials)
    except TokenValidationError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}") from exc

    realm_access = claims.get("realm_access", {}) or {}
    is_super_admin_claim = claims.get("is_super_admin", False)
    if isinstance(is_super_admin_claim, str):
        is_super_admin_claim = is_super_admin_claim.lower() == "true"

    return CurrentUser(
        sub=claims["sub"],
        email=claims.get("email"),
        roles=realm_access.get("roles", []),
        establishment_ids=claims.get("establishment_ids", []) or [],
        is_super_admin=bool(is_super_admin_claim),
    )


def require_roles(*allowed_roles: str):
    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.is_super_admin:
            return user
        if not set(user.roles) & set(allowed_roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return _check


def assert_path_establishment_access(user: CurrentUser, establishment_id) -> None:
    if user.is_super_admin:
        return
    if str(establishment_id) not in user.establishment_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No access to this establishment")
