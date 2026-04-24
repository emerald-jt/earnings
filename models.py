from pydantic import BaseModel, Field

class RecordingEndRequest(BaseModel):
    recording_id: str = Field(min_length=1)
    start_at: int
    end_at: int
    participants: list[str] = Field(min_length=1)

class WithdrawRequest(BaseModel):
    user_id: str = Field(min_length=1)
    withdraw_amount: float = Field(gt=0)

class WithdrawResponse(BaseModel):
    user_id: str
    withdrawn_amount: str
    remaining_balance: str

class BalanceResponse(BaseModel):
    user_id: str
    balance: str

