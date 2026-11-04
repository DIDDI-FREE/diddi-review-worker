import pytest

from app.adapters.pay_gate import FinancialOperationBlocked, PayTestModeGate
from app.orchestration.retry import bounded_retry


def test_financial_operation_requires_confirmed_test_mode():
    with pytest.raises(FinancialOperationBlocked):
        PayTestModeGate().require_test_mode()
    PayTestModeGate(True).require_test_mode()


@pytest.mark.asyncio
async def test_retry_is_bounded():
    calls = 0

    async def action():
        nonlocal calls
        calls += 1
        raise TimeoutError()

    with pytest.raises(RuntimeError, match="bounded retry"):
        await bounded_retry(action, attempts=3)
    assert calls == 3
