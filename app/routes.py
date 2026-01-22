from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Routine

router = APIRouter()


# =========================
# Schemas
# =========================

class RoutineCreate(BaseModel):
    title: str


class RoutineOut(BaseModel):
    id: int
    title: str
    done: bool
    created_at: datetime
    last_done_date: Optional[date] = None
    streak: int
    best_streak: int


# =========================
# DB helpers
# =========================

def list_routines(db: Session) -> List[Routine]:
    return db.query(Routine).order_by(Routine.id.asc()).all()


def create_routine(db: Session, title: str) -> Routine:
    r = Routine(title=title)  # last_done_date 기본 None
    # streak/best_streak가 모델에서 default가 없으면 None일 수 있으니,
    # to_out에서 0 처리합니다.
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def toggle_routine_today(db: Session, routine_id: int) -> Routine:
    today = date.today()
    yesterday = today - timedelta(days=1)

    r = db.query(Routine).filter(Routine.id == routine_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")

    # ✅ 이미 오늘 완료 상태면 -> 토글 OFF
    if r.last_done_date == today:
        # streak 되돌리기(간단/안정 MVP 버전)
        if (r.streak or 0) >= 2:
            r.streak = (r.streak or 0) - 1
            r.last_done_date = yesterday
        else:
            r.streak = 0
            r.last_done_date = None

        # best_streak는 과거 최고 기록이므로 건드리지 않음
        db.commit()
        db.refresh(r)
        return r

    # ✅ 오늘 미완료 -> 토글 ON
    if r.last_done_date == yesterday:
        r.streak = (r.streak or 0) + 1
    else:
        r.streak = 1

    r.best_streak = max(r.best_streak or 0, r.streak or 0)
    r.last_done_date = today

    db.commit()
    db.refresh(r)
    return r


def to_out(r: Routine) -> RoutineOut:
    today = date.today()
    last_done = getattr(r, "last_done_date", None)

    return RoutineOut(
        id=r.id,
        title=r.title,
        done=(last_done == today) if last_done else False,
        created_at=r.created_at,
        last_done_date=last_done,
        streak=(r.streak or 0),
        best_streak=(r.best_streak or 0),
    )


# =========================
# Routes
# =========================

@router.get("/health")
def health():
    return {"ok": True}


@router.get("/routines", response_model=List[RoutineOut])
def get_routines(db: Session = Depends(get_db)):
    routines = list_routines(db)
    return [to_out(r) for r in routines]


@router.post("/routines", response_model=RoutineOut)
def post_routine(payload: RoutineCreate, db: Session = Depends(get_db)):
    r = create_routine(db, payload.title)
    return to_out(r)


@router.post("/routines/{routine_id}/toggle", response_model=RoutineOut)
def toggle_routine(routine_id: int, db: Session = Depends(get_db)):
    r = toggle_routine_today(db, routine_id)
    return to_out(r)
