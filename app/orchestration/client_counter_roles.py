"""Counter-role progression for resources created by a review client."""

from app.orchestration.food_workflow import FoodRestaurantWorkflow
from app.orchestration.go_workflow import GoDriverWorkflow
from app.orchestration.send_workflow import SendCourierWorkflow


class ClientCounterRoleRunner:
    """Delegates each client-triggered resource to its normal counter-role workflow."""

    def __init__(self, *, go, send, food) -> None:
        self.go = GoDriverWorkflow(go)
        self.send = SendCourierWorkflow(send)
        self.food = FoodRestaurantWorkflow(food)

    async def advance_go(self, ride_id: str, **kwargs) -> bool:
        return await self.go.advance(ride_id, **kwargs)

    async def advance_send(self, delivery_id: str, **kwargs) -> bool:
        return await self.send.advance(delivery_id, **kwargs)

    async def advance_food(self, restaurant_id: str, order_id: str, **kwargs) -> bool:
        return await self.food.advance(restaurant_id, order_id, **kwargs)
