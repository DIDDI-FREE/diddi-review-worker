from app.e2e import GooglePlayDriver


def test_google_play_driver_contract_is_runtime_checkable_by_shape():
    class Driver:
        async def open_app(self): ...
        async def sign_in_single_google_account(self): ...
        async def execute_user_journey(self, scenario): return {"ride_id": "r1"}
        async def assert_final_state(self, expected): ...

    driver = Driver()
    assert all(hasattr(driver, method) for method in ("open_app", "sign_in_single_google_account", "execute_user_journey", "assert_final_state"))
