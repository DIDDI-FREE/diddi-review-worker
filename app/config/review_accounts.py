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
