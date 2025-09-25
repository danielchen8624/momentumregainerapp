from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Field, Session
from pydantic import BaseModel
import sys

from .db import engine   #  import engine from db.py

print("Running Python from:", sys.executable)

# --- Models ---
class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str

class HighlightedText(BaseModel):
    text: str

# --- Lifespan (startup/shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

# --- Routes ---
@app.post("/add")
def add_message(payload: HighlightedText):
    with Session(engine) as s:
        msg = Message(text=payload.text)
        s.add(msg)
        s.commit()
        s.refresh(msg)
    return {"ok": True, "id": msg.id}

@app.get("/", include_in_schema=False)
def root():
    return {"ok": True, "service": "momentum-api"}
