from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models import BudgetAdjustment, NudgeHistory, User
from ..schemas import NudgeResponseRequest, WeekendModeRequest
from ..services.spending import discretionary_daily_rate, estimate_days_gained, get_active_cycle, learn_stats

router = APIRouter(prefix="/controller", tags=["controller"])


@router.post("/no-spend-weekend")
def set_weekend_mode(payload: WeekendModeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.no_spend_weekend = payload.enabled
    db.commit()
    return {"enabled": user.no_spend_weekend}


@router.post("/nudges/{nudge_id}/respond")
def respond_to_nudge(nudge_id: int, payload: NudgeResponseRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    nudge = db.scalar(select(NudgeHistory).where(NudgeHistory.id == nudge_id, NudgeHistory.user_id == user.id))
    if not nudge:
        raise HTTPException(404, "Nudge not found")
    if nudge.accepted is not None:
        raise HTTPException(409, "Nudge already answered")

    nudge.accepted = payload.accepted
    nudge.response = payload.action
    nudge.responded_at = datetime.utcnow()
    current_aggression = float(user.suggestion_aggressiveness or 1.0)
    if payload.accepted:
        user.suggestion_aggressiveness = min(1.20, current_aggression + 0.05)
    else:
        user.suggestion_aggressiveness = max(0.50, current_aggression - 0.10)

    if payload.accepted and payload.action == "auto_trim":
        cycle = get_active_cycle(db, user.id)
        rate = discretionary_daily_rate(db, cycle) if cycle else 0
        nudge.estimated_days_gained = estimate_days_gained(nudge.overage, rate)
        db.add(
            BudgetAdjustment(
                user_id=user.id,
                adjustment_date=date.today() + timedelta(days=1),
                amount=nudge.overage,
                reason=f"Auto-trim from nudge {nudge.id}",
            )
        )
    db.commit()
    return {"ok": True, "learn": learn_stats(db, user.id)}


@router.get("/learn-stats")
def get_learn_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learn_stats(db, user.id)
