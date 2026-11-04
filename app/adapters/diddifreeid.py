from app.auth.jwt import ReviewClaims, validate_review_claims


class DiddiFreeIDAdapter:
    def __init__(self, *, jwks_url: str, issuer: str, audience: str, algorithms: list[str]) -> None:
        self.options = {"jwks_url": jwks_url, "issuer": issuer, "audience": audience, "algorithms": algorithms}

    def validate_actor_token(self, token: str) -> ReviewClaims:
        return validate_review_claims(token, **self.options)
