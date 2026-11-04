from enum import StrEnum

from pydantic import BaseModel, Field


class Product(StrEnum):
    DIDDIGO = "diddigo"
    DIDDISEND = "diddisend"
    DIDDIFOOD = "diddifood"


class ActorRole(StrEnum):
    SENDER = "sender"
    COURIER = "courier"
    PASSENGER = "passenger"
    DRIVER = "driver"
    CUSTOMER = "customer"
    RESTAURANT = "restaurant"


class ReviewActor(BaseModel):
    user_id: str
    product: Product
    role: ActorRole
    access_token: str = Field(repr=False)
    is_review_account: bool

    def model_post_init(self, __context: object, /) -> None:
        if self.is_review_account is not True:
            raise ValueError("review actor must have is_review_account=true")
