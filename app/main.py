from fastapi import FastAPI
from .routes import router
from .db import init_db

app = FastAPI()

init_db()  # 서버 시작 시 SQLite DB + 테이블 생성

app.include_router(router)
