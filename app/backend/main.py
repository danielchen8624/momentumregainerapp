from fastapi import FastAPI
from sqlmodel import SQLModel, Field, create_engine, Session
import sys
from pydantic import BaseModel
import os


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
print("Running Python from:", sys.executable)

class Message(SQLModel, table=True): #inhertis from SQLModel and table=True to tell SQLModel this is a table for the database
    id: int | None = Field(default=None, primary_key=True)
    text: str

class HighlightedText(BaseModel): #basemodel makes sure that anytime something trues to use this class, the data passed are in the right format. eg: without it, if you tried to pass a boolean into text, it will raise an error
    text: str

app = FastAPI() #event listener blueprint. uvicorn turns it alive

@app.on_event("startup")
def startup():
    SQLModel.metadata.create_all(engine) #looos through every class that uses SQLModel and creates the database tables for it if they don't exist

@app.post("/add")
def add_message(payload: HighlightedText):
   
    with Session(engine) as s:
        s.add(Message(text=payload.text)) #add the highlighted text to the database
        s.commit()
    return {"ok": True}

