import os
from base64 import b64decode
from enum import Enum
from typing import Optional, Union, List

from pydantic import ConfigDict, model_validator, field_validator
from pydantic_settings import BaseSettings


class AuthType(Enum):
    NOOP = "noop"
    JWT_LOCAL = "jwt_local"
    JWT_OIDC = "jwt_oidc"


class JWTSettingsBase(BaseSettings):
    iss: str
    aud: Union[str, list[str]]

    @field_validator("aud", mode="before")
    @classmethod
    def set_aud(cls, v) -> Union[str, List[str]]:
        if isinstance(v, str) and "," in v:
            return v.split(",")
        return v
    model_config = ConfigDict(env_prefix="jwt_",)


class JWTSettingsLocal(JWTSettingsBase):
    decode_key_b64: str
    decode_key: str = None
    alg: str

    @field_validator("decode_key", mode="before")
    @classmethod
    def set_decode_key(cls, v, values):
        """
        Key may be a multiline string (e.g. in the case of a public key), so to
        be able to set it from env, we set it as a base64 encoded string and
        decode it here.
        """
        decode_key_b64 = kwargs.get("decode_key_b64")
        if decode_key_b64:
            return b64decode(decode_key_b64).decode("utf-8")
        return v


class JWTSettingsOIDC(JWTSettingsBase):
    ...


class Settings(BaseSettings):
    auth_type: AuthType
    jwt_local: Optional[JWTSettingsLocal] = None
    jwt_oidc: Optional[JWTSettingsOIDC] = None

    @model_validator(mode="before")
    @classmethod
    def check_jwt_settings(cls, values):
        auth_type = values.get("auth_type")
        if auth_type == AuthType.JWT_LOCAL and values.get("jwt_local") is None:
            raise ValueError(
                "jwt local settings must be set when auth type is jwt_local."
            )
        if auth_type == AuthType.JWT_OIDC and values.get("jwt_oidc") is None:
            raise ValueError(
                "jwt oidc settings must be set when auth type is jwt_oidc."
            )
        return values


auth_type = AuthType(os.getenv("AUTH_TYPE", AuthType.NOOP.value).lower())
kwargs = {"auth_type": auth_type}
if auth_type == AuthType.JWT_LOCAL:
    kwargs["jwt_local"] = JWTSettingsLocal()
elif auth_type == AuthType.JWT_OIDC:
    kwargs["jwt_oidc"] = JWTSettingsOIDC()
settings = Settings(**kwargs)
