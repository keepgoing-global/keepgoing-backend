# app/db.py
from datetime import date, datetime
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = "sqlite:///./keepgoing.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_done_date = Column(Date, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def list_routines(db: Session) -> List[Routine]:
    return db.query(Routine).order_by(Routine.id.asc()).all()


def create_routine(db: Session, title: str) -> Routine:
    r = Routine(title=title)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def complete_routine(db: Session, routine_id: int, today: date) -> Routine:
    r = db.query(Routine).filter(Routine.id == routine_id).first()
    if not r:
        raise ValueError("NOT_FOUND")
    if r.last_done_date == today:
        raise ValueError("ALREADY_DONE")
    r.last_done_date = today
    db.commit()
    db.refresh(r)
    return r

