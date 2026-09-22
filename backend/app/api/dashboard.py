from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models import RecurringExpense, Transaction, User
from ..services.spending import (
    category_breakdown,
    cycle_snapshot,
    discretionary_daily_rate,
    get_active_cycle,
    learn_stats,
    projected_broke_date,
    safe_to_spend_today,
)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    cycle = get_active_cycle(db, user.id, today)
    if not cycle:
        raise HTTPException(404, "No active income cycle")
    snap = cycle_snapshot(db, cycle, today)
    broke_date, rate = projected_broke_date(db, user, cycle, today)
    safe = safe_to_spend_today(db, user, cycle, today)
    recent = list(
        db.scalars(
            select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.txn_date.desc(), Transaction.id.desc()).limit(6)
        )
    )
    subscriptions = list(db.scalars(select(RecurringExpense).where(RecurringExpense.user_id == user.id, RecurringExpense.active.is_(True))))
    at_risk = broke_date is not None and broke_date < cycle.end_date
    return {
        "user": {"name": user.name, "email": user.email},
        "cycle": {
            "start": cycle.start_date.isoformat(),
            "end": cycle.end_date.isoformat(),
            "days_remaining": snap["days_remaining"],
            "starting_balance": float(cycle.starting_balance),
        },
        "current_balance": float(snap["spendable"]),
        "spent": float(snap["spent"]),
        "jar_balance": float(snap["jar"]),
        "safe_to_spend_today": float(safe),
        "discretionary_daily_rate": float(rate),
        "broke_date": broke_date.isoformat() if broke_date else None,
        "status": "at_risk" if at_risk else "on_track",
        "no_spend_weekend": user.no_spend_weekend,
        "learn": {**learn_stats(db, user.id), "suggestion_aggressiveness": float(user.suggestion_aggressiveness or 1.0)},
        "category_breakdown": category_breakdown(snap["transactions"]),
        "recent_transactions": [
            {
                "id": t.id,
                "amount": float(t.amount),
                "merchant": t.merchant or "Unknown",
                "category": t.category.name,
                "date": t.txn_date.isoformat(),
                "source": t.source,
            }
            for t in recent
        ],
        "subscriptions": [
            {
                "id": s.id,
                "merchant": s.merchant,
                "amount": float(s.amount),
                "cadence_days": s.cadence_days,
                "next_due_date": s.next_due_date.isoformat() if s.next_due_date else None,
                "confidence": s.confidence,
            }
            for s in subscriptions
        ],
    }
