from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db, list_routines, create_routine, complete_routine

router = APIRouter()


class RoutineCreate(BaseModel):
    title: str


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/routines")
def get_routines(db: Session = Depends(get_db)):
    today = date.today()  # 테스트용(어제)

    routines = list_routines(db)

    return [
        {
            "id": r.id,
            "title": r.title,
            "done": r.last_done_date == today,
            "created_at": r.created_at,
            "last_done_date": r.last_done_date,
        }
        for r in routines
    ]


@router.post("/routines")
def post_routine(payload: RoutineCreate, db: Session = Depends(get_db)):
    r = create_routine(db, payload.title)
    return {
        "id": r.id,
        "title": r.title,
        "done": False,
        "created_at": r.created_at,
        "last_done_date": r.last_done_date,
    }


@router.post("/routines/{routine_id}/complete")
def post_complete(routine_id: int, db: Session = Depends(get_db)):
    today = date.today()
    try:
        r = complete_routine(db, routine_id, today)
    except ValueError as e:
        if str(e) == "NOT_FOUND":
            raise HTTPException(status_code=404, detail="routine not found")
        if str(e) == "ALREADY_DONE":
            raise HTTPException(status_code=400, detail="already completed today")
        raise

    return {
        "id": r.id,
        "title": r.title,
        "done": True,
        "created_at": r.created_at,
        "last_done_date": r.last_done_date,
    }
