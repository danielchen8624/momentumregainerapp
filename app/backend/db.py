# app/backend/db.py
from pathlib import Path
from platformdirs import user_data_dir  # pip install platformdirs
from sqlmodel import create_engine

APP_NAME = "Momentum"
APP_AUTHOR = "Momentum"  # org or your name


data_dir = Path(user_data_dir("Momentum", "Daniel Xu Yuxuan Chen"))
data_dir.mkdir(parents=True, exist_ok=True)


DB_PATH = data_dir / "data.db"          # e.g. macOS: ~/Library/Application Support/Momentum/data.db
engine = create_engine(f"sqlite:///{DB_PATH}") 

print("DB in use:", DB_PATH)
