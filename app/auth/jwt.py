from dataclasses import dataclass
from typing import Any

import jwt


@dataclass(frozen=True)
class ReviewClaims:
    user_id: str
    role: str
    is_review_account: bool


def validate_review_claims(
    token: str,
    *,
    jwks_url: str,
    issuer: str,
    audience: str,
    algorithms: list[str],
) -> ReviewClaims:
    key = jwt.PyJWKClient(jwks_url, cache_keys=True).get_signing_key_from_jwt(token).key
    claims: dict[str, Any] = jwt.decode(
        token, key, algorithms=algorithms, issuer=issuer, audience=audience,
        options={"require": ["sub", "exp", "iss", "aud"]},
    )
    marker = claims.get("is_review_account")
    if type(marker) is not bool or marker is not True:
        raise ValueError("token is not a review account token")
    return ReviewClaims(user_id=str(claims["sub"]), role=str(claims.get("role", "user")), is_review_account=True)


def redact_token(value: str) -> str:
    return f"{value[:8]}…" if value else "<empty>"

