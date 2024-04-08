import os
from base64 import b64decode
from enum import StrEnum
from typing import Optional

from pydantic import BaseSettings, root_validator, validator


class AuthType(StrEnum):
    NOOP = "noop"
    JWT_BASIC = "jwt_basic"
    JWT_OIDC = "jwt_oidc"


class JWTSettingsBase(BaseSettings):
    iss: str
    aud: str

    class Config:
        env_prefix = "jwt_"


class JWTSettingsBasic(JWTSettingsBase):
    decode_key_b64: str
    decode_key: str = None

    @validator("decode_key", pre=True, always=True)
    def set_decode_key(cls, v, values):
        """
        Key may be a multiline string (e.g. in the case of a public key), so to
        be able to set it from env, we set it as a base64 encoded string and
        decode it here.
        """
        return b64decode(values["decode_key_b64"]).decode("utf-8")


class JWTSettingsOIDC(JWTSettingsBase):
    ...


class Settings(BaseSettings):
    auth_type: AuthType
    jwt_basic: Optional[JWTSettingsBasic] = None
    jwt_oidc: Optional[JWTSettingsOIDC] = None

    @root_validator(pre=True)
    def check_jwt_settings(cls, values):
        auth_type = values.get("auth_type")
        if auth_type == AuthType.JWT_BASIC and values.get("jwt_basic") is None:
            raise ValueError(
                "jwt basic settings must be set when auth type is jwt_basic."
            )
        if auth_type == AuthType.JWT_OIDC and values.get("jwt_oidc") is None:
            raise ValueError(
                "jwt oidc settings must be set when auth type is jwt_oidc."
            )
        return values


auth_type = AuthType(os.getenv("AUTH_TYPE", AuthType.NOOP).lower())
kwargs = {"auth_type": auth_type}
if auth_type == AuthType.JWT_BASIC:
    kwargs["jwt_basic"] = JWTSettingsBasic()
elif auth_type == AuthType.JWT_OIDC:
    kwargs["jwt_oidc"] = JWTSettingsOIDC()
settings = Settings(**kwargs)
