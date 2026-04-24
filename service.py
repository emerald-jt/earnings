from fastapi import FastAPI
from earning_service import EarningService
from memory import InMemoryStore
from models import RecordingEndRequest, WithdrawRequest, WithdrawResponse, BalanceResponse

app = FastAPI()
store = InMemoryStore()
earning = EarningService(store, delay_seconds=60)

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.post("/recording/end")
def end_recording(req: RecordingEndRequest):
    earning.end_recording(req)
    return {"status": "ok"}

@app.get("/balance/{user_id}", response_model=BalanceResponse)
def get_balance(user_id: str):
    return earning.get_balance(user_id)

@app.post("/withdraw", response_model=WithdrawResponse)
def withdraw(req: WithdrawRequest):
    return earning.withdraw(req)