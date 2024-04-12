from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Annotated

import jwt
import requests
from fastapi import Depends, HTTPException, Request
from fastapi.security.http import HTTPBearer

import app.storage as storage
from app.auth.settings import AuthType, settings
from app.schema import User


class AuthHandler(ABC):
    @abstractmethod
    async def __call__(self, request: Request) -> User:
        """Auth handler that returns a user object or raises an HTTPException."""


class NOOPAuth(AuthHandler):
    _default_sub = "static-default-user-id"

    async def __call__(self, request: Request) -> User:
        sub = request.cookies.get("opengpts_user_id") or self._default_sub
        user, _ = await storage.get_or_create_user(sub)
        return user


class JWTAuthBase(AuthHandler):
    async def __call__(self, request: Request) -> User:
        http_bearer = await HTTPBearer()(request)
        token = http_bearer.credentials

        try:
            payload = self.decode_token(token, self.get_decode_key(token))
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail=str(e))

        user, _ = await storage.get_or_create_user(payload["sub"])
        return user

    @abstractmethod
    def decode_token(self, token: str, decode_key: str) -> dict:
        ...

    @abstractmethod
    def get_decode_key(self, token: str) -> str:
        ...


class JWTAuthLocal(JWTAuthBase):
    """Auth handler that uses a hardcoded decode key from env."""

    def decode_token(self, token: str, decode_key: str) -> dict:
        return jwt.decode(
            token,
            decode_key,
            issuer=settings.jwt_local.iss,
            audience=settings.jwt_local.aud,
            algorithms=[settings.jwt_local.alg.upper()],
            options={"require": ["exp", "iss", "aud", "sub"]},
        )

    def get_decode_key(self, token: str) -> str:
        return settings.jwt_local.decode_key


class JWTAuthOIDC(JWTAuthBase):
    """Auth handler that uses OIDC discovery to get the decode key."""

    def decode_token(self, token: str, decode_key: str) -> dict:
        alg = self._decode_complete_unverified(token)["header"]["alg"]
        return jwt.decode(
            token,
            decode_key,
            issuer=settings.jwt_oidc.iss,
            audience=settings.jwt_oidc.aud,
            algorithms=[alg.upper()],
            options={"require": ["exp", "iss", "aud", "sub"]},
        )

    def get_decode_key(self, token: str) -> str:
        unverified = self._decode_complete_unverified(token)
        issuer = unverified["payload"].get("iss")
        kid = unverified["header"].get("kid")
        return self._get_jwk_client(issuer).get_signing_key(kid).key

    @lru_cache
    def _decode_complete_unverified(self, token: str) -> dict:
        return jwt.api_jwt.decode_complete(token, options={"verify_signature": False})

    @lru_cache
    def _get_jwk_client(self, issuer: str) -> jwt.PyJWKClient:
        """
        lru_cache ensures a single instance of PyJWKClient per issuer. This is
        so that we can take advantage of jwks caching (and invalidation) handled
        by PyJWKClient.
        """
        url = issuer.rstrip("/") + "/.well-known/openid-configuration"
        config = requests.get(url).json()
        return jwt.PyJWKClient(config["jwks_uri"], cache_jwk_set=True)


@lru_cache(maxsize=1)
def get_auth_handler() -> AuthHandler:
    if settings.auth_type == AuthType.JWT_LOCAL:
        return JWTAuthLocal()
    elif settings.auth_type == AuthType.JWT_OIDC:
        return JWTAuthOIDC()
    return NOOPAuth()


async def auth_user(
    request: Request, auth_handler: AuthHandler = Depends(get_auth_handler)
):
    return await auth_handler(request)


AuthedUser = Annotated[User, Depends(auth_user)]
