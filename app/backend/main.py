from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Field, create_engine, Session
import sys
from pydantic import BaseModel
import os

# --- DB setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
print("Running Python from:", sys.executable)

# --- Models ---
class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str

class HighlightedText(BaseModel):
    text: str

# only run once when the app starts (new on_startup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    SQLModel.metadata.create_all(engine)
    yield
    # Shutdown (optional). put cleanup here if needed

app = FastAPI(lifespan=lifespan)

# --- Routes ---
@app.post("/add")
def add_message(payload: HighlightedText):
    with Session(engine) as s:
        msg = Message(text=payload.text)
        s.add(msg)
        s.commit()
        s.refresh(msg)  # grab the auto-generated id
    return {"ok": True, "id": msg.id}

# (Optional) quick health check so / doesn't 404
@app.get("/", include_in_schema=False)
def root():
    return {"ok": True, "service": "momentum-api"}
