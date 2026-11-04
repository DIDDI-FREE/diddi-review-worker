class FinancialOperationBlocked(RuntimeError):
    pass


class TestModeGate:
    def __init__(self, confirmed: bool = False) -> None:
        self.confirmed = confirmed

    def require_test_mode(self) -> None:
        if not self.confirmed:
            raise FinancialOperationBlocked("DiddiPay test mode is not confirmed")
