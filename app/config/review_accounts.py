import json

from pydantic import BaseModel, Field

from app.orchestration.reactive import AccountBinding


class ReviewAccountConfig(BaseModel):
    reviewer_user_id: str
    tested_role: str
    counter_role: str
    counter_user_id: str
    product: str
    enabled: bool = True
    email: str | None = None
    phone: str | None = None
    otp: str | None = None

    def credential(self):
        from app.auth.token_provider import ReviewAccountCredential

        if not self.email and not self.phone:
            raise ValueError(f"review account {self.reviewer_user_id} has no email or phone")
        if not self.otp:
            raise ValueError(f"review account {self.reviewer_user_id} has no OTP secret")
        return ReviewAccountCredential(self.reviewer_user_id, self.phone, self.otp, email=self.email)

    def binding(self) -> AccountBinding:
        return AccountBinding(
            reviewer_user_id=self.reviewer_user_id,
            tested_role=self.tested_role,
            counter_role=self.counter_role,
            counter_user_id=self.counter_user_id,
            product=self.product,
        )


class ReviewAccountRegistry(BaseModel):
    accounts: list[ReviewAccountConfig] = Field(default_factory=list)

    def bindings(self) -> list[AccountBinding]:
        return [account.binding() for account in self.accounts if account.enabled]

    @classmethod
    def from_json(cls, value: str) -> "ReviewAccountRegistry":
        parsed = json.loads(value)
        return cls.model_validate({"accounts": parsed})
