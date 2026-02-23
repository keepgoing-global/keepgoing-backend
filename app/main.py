from fastapi import FastAPI
from .routes import router as routes_router
from .character_routes import router as character_router
from .db import init_db

app = FastAPI()

init_db()

app.include_router(routes_router)
app.include_router(character_router)
