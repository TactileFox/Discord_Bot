import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database.database import connect_to_db, disconnect_db
from api import guild_controller, message_controller, user_controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db(os.getenv('CONNECTION_STRING'))
    yield
    await disconnect_db()


app = FastAPI(lifespan=lifespan)
app.include_router(guild_controller.router)
app.include_router(message_controller.router)
app.include_router(user_controller.router)
