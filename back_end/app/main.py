from fastapi import FastAPI
from app.database.database import connect_to_db, disconnect_db

app = FastAPI()

