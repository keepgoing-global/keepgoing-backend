from .database import SessionLocal, Base, engine
from . import models  # 모델 로드(테이블 생성에 필요)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

