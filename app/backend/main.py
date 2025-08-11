from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select
import time, json, uuid, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "momentum.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

class Item(SQLModel, table=True): #make a new class called Item that inherits from SQLModel, table=True means it will be a table in the database
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    group_id: str = "default"
    kind: str
    title: Optional[str] = ""
    app_id: Optional[str] = ""
    locator_json: str
    updated_at: int = Field(default_factory=lambda: int(time.time()))

class CaptureItem(BaseModel): #blueprint/shape of capture request. defines the "base" model for incoming capture requests. each capture will have this structure
    kind: str                 # "web" | "vscode" | "youtube" | etc.
    title: Optional[str] = ""
    app_id: Optional[str] = ""
    group_id: Optional[str] = "default"
    locator: Any

app = FastAPI(title="Momentum API", version="0.1.0")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/capture/item")
def capture_item(item: CaptureItem):
    with Session(engine) as s: # opens a new session to interact with the database
        row = Item(
            group_id=item.group_id or "default",
            kind=item.kind,
            title=item.title or "",
            app_id=item.app_id or "",
            locator_json=json.dumps(item.locator),
        )
        s.add(row)
        s.commit()
        return {"ok": True, "id": row.id}

@app.get("/items/recent")
def list_recent(limit: int = 10, group_id: str = "default"):
    with Session(engine) as s:
        stmt = select(Item).where(Item.group_id == group_id).order_by(Item.updated_at.desc()).limit(limit)
        rows = s.exec(stmt).all()
        return [
            {
                "id": r.id,
                "kind": r.kind,
                "title": r.title,
                "app_id": r.app_id,
                "locator": json.loads(r.locator_json), #all of the things i want to store, like tldr summary, highlights, scroll pos, etc will be stuffed here. to get it, i need to call this thing again
                "updated_at": r.updated_at,
            } for r in rows
        ]
