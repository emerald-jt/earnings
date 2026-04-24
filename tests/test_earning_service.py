# 1. no overlap
# 2. overlap
# 3. get balance without pending recordings 
# 4. Get balance with pending recordings
# 5. Withdraw with sufficient balance
# 6. Withdraw with insufficient balance
# 7. Fraud detection with overlaps
import pytest
from datetime import datetime
from memory import InMemoryStore
from earning_service import EarningService
from models import RecordingEndRequest, WithdrawRequest

def make_earning_service() -> EarningService:
    return EarningService(InMemoryStore(), delay_seconds=60)

def to_int_time(dt: str) -> int:
    dt_obj = datetime.fromisoformat(dt)
    return int(dt_obj.timestamp())

def make_recording(recording_id: str, start_at: str, end_at: str, participants: list[str]):
    return RecordingEndRequest(
        recording_id=recording_id,
        start_at=start_at,
        end_at=end_at,
        participants=participants
    )

def make_withdraw_request(user_id: str, withdraw_amount: float):
    return WithdrawRequest(
        user_id=user_id,
        withdraw_amount=withdraw_amount
    )

def test_end_recording_no_overlap():
    earning_service = make_earning_service()
    req = make_recording("rec1", "2026-04-24T00:31:00", "2026-04-24T01:31:00", ["user1"])
    earning_service.end_recording(req)
    ledger = earning_service.store.user_ledgers["user1"]
    assert len(ledger.previous_recordings) == 1
    assert not ledger.previous_recordings[0].fraud_flag

def test_end_recording_with_overlap():
    earning_service = make_earning_service()
    req1 = make_recording("rec1", "2026-04-24T00:31:00", "2026-04-24T01:31:00", ["user1"])
    req2 = make_recording("rec2", "2026-04-24T01:01:00", "2026-04-24T02:01:00", ["user1"])
    earning_service.end_recording(req1)
    earning_service.end_recording(req2)
    ledger = earning_service.store.user_ledgers["user1"]
    assert len(ledger.previous_recordings) == 2
    assert ledger.previous_recordings[0].fraud_flag
    assert ledger.previous_recordings[1].fraud_flag

def test_get_balance_without_pending():
    earning_service = make_earning_service()
    req = make_recording("rec1", "2026-04-24T00:31:00", "2026-04-24T01:31:00", ["user1"])
    earning_service.end_recording(req)
    balance = earning_service.get_balance("user1", current_time=to_int_time("2026-04-24T01:33:00"))
    assert balance.balance == "1.00$"

def test_get_balance_with_pending():
    earning_service = make_earning_service()
    req = make_recording("rec1", "2026-04-24T00:31:00", "2026-04-24T01:31:00", ["user1"])
    earning_service.end_recording(req)
    balance = earning_service.get_balance("user1", current_time=to_int_time("2026-04-24T01:31:30"))
    assert balance.balance == "0.00$"

def test_withdraw_with_sufficient_balance():
    earning_service = make_earning_service()
    req = make_recording("rec1", "2026-04-24T00:31:00", "2026-04-24T01:31:00", ["user1"])
    earning_service.end_recording(req)
    response = earning_service.withdraw(make_withdraw_request("user1", 0.5), current_time=to_int_time("2026-04-24T01:33:00"))
    assert response.withdrawn_amount == "0.5$"
    assert response.remaining_balance == "0.50$"

def test_withdraw_with_insufficient_balance():
    earning_service = make_earning_service()
    req = make_recording("rec1", "2026-04-24T00:31:00", "2026-04-24T01:31:00", ["user1"])
    earning_service.end_recording(req)
    with pytest.raises(ValueError):
        earning_service.withdraw(make_withdraw_request("user1", 1.5), current_time=to_int_time("2026-04-24T01:33:00"))

def test_fraud_detection_with_overlaps():
    earning_service = make_earning_service()
    req1 = make_recording("rec1", "2026-04-24T00:31:00", "2026-04-24T01:31:00", ["user1"])
    req2 = make_recording("rec2", "2026-04-24T01:01:00", "2026-04-24T01:31:00", ["user1"])
    earning_service.end_recording(req1)
    earning_service.end_recording(req2)
    ledger = earning_service.store.user_ledgers["user1"]
    assert len(ledger.previous_recordings) == 2
    assert ledger.previous_recordings[0].fraud_flag
    assert ledger.previous_recordings[1].fraud_flag
    balance = earning_service.get_balance("user1", current_time=to_int_time("2026-04-24T01:33:30"))
    assert balance.balance == "0.00$"