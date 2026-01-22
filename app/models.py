from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime
from .database import Base


class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)

    # ✅ 생성 시각(서버에서 자동)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # ✅ 마지막 완료 날짜(하루 1회)
    last_done_date = Column(Date, nullable=True)

    # ✅ streak 관련
    streak = Column(Integer, nullable=False, default=0)
    best_streak = Column(Integer, nullable=False, default=0)
