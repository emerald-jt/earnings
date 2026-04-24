from memory import InMemoryStore, Recording, UserLedger, UserRecording
from models import RecordingEndRequest, WithdrawRequest, WithdrawResponse, BalanceResponse
from heapq import heappush, heappop
from datetime import datetime, timezone

class EarningService:
    def __init__(self, store: InMemoryStore, delay_seconds: int):
        self.store = store
        self.delay_seconds = delay_seconds

    def end_recording(self, req: RecordingEndRequest):
        end_at = self.to_int_time(req.end_at)
        start_at = self.to_int_time(req.start_at)
        if end_at <= start_at:
            raise ValueError("end time must be after start time")

        if req.recording_id in self.store.recordings:
            raise ValueError("Recording already processed")

        self.store.recordings[req.recording_id] = Recording(
            recording_id=req.recording_id,
            start_at=start_at,
            end_at=end_at,
            participants=req.participants
        )

        amount_cents = self.calculate_amount(start_at, end_at)

        for user_id in req.participants:
            ledger = self.get_or_create_ledger(user_id)
            new_recording = UserRecording(
                start_at=start_at,
                end_at=end_at,
                amount=amount_cents,
                recording_id=req.recording_id,
                fraud_flag=False
            )

            overlaps = self.find_overlap_and_insert(ledger.recordings, new_recording)
            for overlap in overlaps:
                new_recording.fraud_flag = True
                for overlap in overlaps:
                    overlap.fraud_flag = True
            
            heappush(ledger.pending_recordings, (new_recording.end_at, new_recording))
            ledger.pending_balance += amount_cents

    def calculate_amount(self, start_at: int, end_at: int) -> int:
        duration_seconds = end_at - start_at
        duration_minute = duration_seconds // 60
        return (duration_minute * 100) // 60
    
    def get_or_create_ledger(self, user_id: str) -> UserLedger:
        return self.store.user_ledgers.setdefault(user_id, UserLedger())
    
    def find_overlap_and_insert(self, previous_recordings: list[UserRecording], new_recording: UserRecording) -> UserRecording:
        overlaps: list[UserRecording] = []
        insert_index = self.store.find_insert_index(previous_recordings, new_recording.start_at)
        left = insert_index - 1
        right = insert_index
        if left >= 0 and previous_recordings[left].end_at > new_recording.start_at:
            overlaps.append(previous_recordings[left])
        if right < len(previous_recordings) and previous_recordings[right].start_at < new_recording.end_at:
            overlaps.append(previous_recordings[right])
        
        previous_recordings.insert(insert_index, new_recording)
        return overlaps
        
    def find_insert_index(self, previous_recordings: list[UserRecording], start_at) -> int:
        left = 0
        right = len(previous_recordings)
        while left < right:
            mid = (left + right) // 2
            if previous_recordings[mid].start_at < start_at:
                left = mid + 1
            else:
                right = mid
        return left
    
    def get_balance(self, user_id: str, current_time: int) -> BalanceResponse:
        if current_time is None:
            current_time = self.get_current_time()
        ledger = self.get_or_create_ledger(user_id)
        self.process_pending_recordings(ledger, current_time)
        return BalanceResponse(user_id=user_id, balance=str(ledger.balance / 100) + "$")
    
    def withdraw(self, req: WithdrawRequest, current_time: int) -> WithdrawResponse:
        if current_time is None:
            current_time = self.get_current_time()
        ledger = self.get_or_create_ledger(req.user_id)
        self.process_pending_recordings(ledger, current_time)
        if req.withdraw_amount * 100 > ledger.balance:
            raise ValueError("Insufficient balance")
        ledger.balance -= int(req.withdraw_amount * 100)
        return WithdrawResponse(
            user_id=req.user_id, 
            withdrawn_amount=str(req.withdraw_amount) + "$",
            remaining_balance=str(ledger.balance / 100) + "$"
        )
    
    def get_current_time(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())
    
    def to_int_time(self, dt: datetime) -> int:
        return int(dt.timestamp())

    def process_pending_recordings(self, ledger: UserLedger, current_time: int) -> None:
        while ledger.pending_recordings and ledger.pending_recordings[0][0] <= current_time - delay_seconds:
            _, recording = heappop(ledger.pending_recordings)
            if not recording.fraud_flag:
                ledger.balance += recording.amount
            ledger.pending_balance -= recording.amount