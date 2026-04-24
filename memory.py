
from dataclasses import dataclass, field

@dataclass
class Recording:
    recording_id: str
    start_at: int
    end_at: int
    participants: list[str]

@dataclass
class UserLedger:
    user_id: str
    balance: int
    pending_balance: int
    pending_recordings: list[tuple[int, UserRecording]] = field(default_factory=list)
    previous_recordings: list[UserRecording] = field(default_factory=list)

@dataclass
class UserRecording:
    start_at: int
    end_at: int
    amount: int
    recording_id: str
    fraud_flag: bool = False

class InMemoryStore:
    def __init__(self) -> None:
        self.recordings: dict[str, Recording] = {}
        self.user_ledgers: dict[str, UserLedger] = {}
