from enum import StrEnum

from pydantic import BaseModel, Field


class ScenarioName(StrEnum):
    SEND_REVIEWS = "diddisend-reviews"
    GO_REVIEWS = "diddigo-reviews"
    FOOD_REVIEWS = "diddifood-reviews"


class ReviewStep(BaseModel):
    key: str
    product: str
    role: str
    resource_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class RunRequest(BaseModel):
    scenario: ScenarioName
    steps: list[ReviewStep] = Field(min_length=1)

    def validate_contract(self) -> None:
        allowed = {
            ScenarioName.SEND_REVIEWS: {("diddisend", "sender"), ("diddisend", "courier")},
            ScenarioName.GO_REVIEWS: {("diddigo", "passenger"), ("diddigo", "driver")},
            ScenarioName.FOOD_REVIEWS: {("diddifood", "customer"), ("diddifood", "courier")},
        }[self.scenario]
        for step in self.steps:
            if (step.product, step.role) not in allowed:
                raise ValueError(f"role {step.role} is not allowed in scenario {self.scenario}")
            if step.product == "diddifood" and step.role == "restaurant":
                raise ValueError("DiddiFood restaurant rating contract is unavailable")
