from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING
from statistics import mean
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..models import BudgetAdjustment, Category, IncomeCycle, NudgeHistory, RecurringExpense, Transaction, User
from .categorizer import FIXED_CATEGORIES

TEN = Decimal("10")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def jar_contribution(amount: Decimal) -> Decimal:
    amount = money(amount)
    target = (amount / TEN).to_integral_value(rounding=ROUND_CEILING) * TEN
    return money(target - amount)


def get_active_cycle(db: Session, user_id: int, today: date | None = None) -> IncomeCycle | None:
    today = today or date.today()
    return db.scalar(
        select(IncomeCycle)
        .where(IncomeCycle.user_id == user_id, IncomeCycle.start_date <= today, IncomeCycle.end_date >= today)
        .order_by(IncomeCycle.start_date.desc())
    )


def cycle_transactions(db: Session, cycle_id: int) -> list[Transaction]:
    return list(db.scalars(select(Transaction).where(Transaction.cycle_id == cycle_id).order_by(Transaction.txn_date.asc(), Transaction.id.asc())))


def cycle_snapshot(db: Session, cycle: IncomeCycle, today: date | None = None) -> dict:
    today = today or date.today()
    txns = cycle_transactions(db, cycle.id)
    spent = sum((money(t.amount) for t in txns), Decimal("0"))
    jar = sum((money(t.jar_contribution) for t in txns), Decimal("0"))
    spendable = max(Decimal("0"), money(cycle.starting_balance) - spent - jar)
    days_remaining = max(1, (cycle.end_date - today).days + 1)
    base_safe = money(spendable / Decimal(days_remaining))
    return {
        "transactions": txns,
        "spent": money(spent),
        "jar": money(jar),
        "spendable": money(spendable),
        "days_remaining": days_remaining,
        "base_safe_per_day": base_safe,
    }


def discretionary_daily_rate(db: Session, cycle: IncomeCycle, today: date | None = None) -> Decimal:
    today = today or date.today()
    txns = cycle_transactions(db, cycle.id)
    discretionary = [t for t in txns if not t.is_recurring and t.category.name not in FIXED_CATEGORIES]
    if not discretionary:
        return Decimal("0.00")

    elapsed_full = max(1, (today - cycle.start_date).days + 1)
    recent_start = max(cycle.start_date, today - timedelta(days=6))
    elapsed_recent = max(1, (today - recent_start).days + 1)
    recent_total = sum((money(t.amount) for t in discretionary if t.txn_date >= recent_start), Decimal("0"))
    full_total = sum((money(t.amount) for t in discretionary), Decimal("0"))
    recent_avg = recent_total / Decimal(elapsed_recent)
    full_avg = full_total / Decimal(elapsed_full)
    return money(Decimal("0.6") * recent_avg + Decimal("0.4") * full_avg)


def projected_broke_date(db: Session, user: User, cycle: IncomeCycle, today: date | None = None) -> tuple[date | None, Decimal]:
    today = today or date.today()
    snap = cycle_snapshot(db, cycle, today)
    balance = snap["spendable"]
    rate = discretionary_daily_rate(db, cycle, today)

    recurring = list(db.scalars(select(RecurringExpense).where(RecurringExpense.user_id == user.id, RecurringExpense.active.is_(True))))
    due_map: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in recurring:
        due = item.next_due_date
        if not due:
            continue
        while due <= cycle.end_date:
            if due >= today:
                due_map[due] += money(item.amount)
            due += timedelta(days=max(1, item.cadence_days))

    # If there is no discretionary rate and no scheduled recurring debit, there is no predicted broke date in the cycle.
    if rate <= 0 and not due_map:
        return None, rate

    cursor = today
    hard_stop = cycle.end_date + timedelta(days=365)
    while cursor <= hard_stop:
        if cursor in due_map:
            balance -= due_map[cursor]
        if balance <= 0:
            return cursor, rate
        balance -= rate
        if balance <= 0:
            return cursor, rate
        cursor += timedelta(days=1)
    return None, rate


def safe_to_spend_today(db: Session, user: User, cycle: IncomeCycle, today: date | None = None) -> Decimal:
    today = today or date.today()
    snap = cycle_snapshot(db, cycle, today)
    safe = snap["base_safe_per_day"]

    adjustment_total = db.scalar(
        select(func.coalesce(func.sum(BudgetAdjustment.amount), 0)).where(
            BudgetAdjustment.user_id == user.id,
            BudgetAdjustment.adjustment_date == today,
            BudgetAdjustment.applied.is_(True),
        )
    )
    safe = max(Decimal("0"), safe - money(adjustment_total))

    if user.no_spend_weekend and today.weekday() in (4, 5, 6):
        from ..core.config import get_settings
        cap = money(get_settings().no_spend_weekend_daily_cap)
        safe = min(safe, cap)
    return money(safe)


def category_breakdown(txns: list[Transaction]) -> list[dict]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for txn in txns:
        totals[txn.category.name] += money(txn.amount)
    return [
        {"category": category, "amount": float(money(amount))}
        for category, amount in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    ]


def detect_recurring_expenses(db: Session, user_id: int) -> list[RecurringExpense]:
    txns = list(db.scalars(select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.txn_date.asc())))
    by_merchant: dict[str, list[Transaction]] = defaultdict(list)
    for txn in txns:
        if txn.merchant:
            by_merchant[txn.merchant.strip().lower()].append(txn)

    detected: list[RecurringExpense] = []
    for normalized, items in by_merchant.items():
        if len(items) < 2:
            continue
        gaps = [(items[i].txn_date - items[i - 1].txn_date).days for i in range(1, len(items))]
        amounts = [float(items[i].amount) for i in range(len(items))]
        avg_gap = mean(gaps)
        avg_amount = mean(amounts)
        amount_spread = (max(amounts) - min(amounts)) / max(avg_amount, 1)

        monthly = 25 <= avg_gap <= 35
        weekly = 6 <= avg_gap <= 8
        fixed_category = any(t.category.name in FIXED_CATEGORIES for t in items)
        if not ((monthly or weekly) and amount_spread <= 0.15) and not fixed_category:
            continue

        cadence = 7 if weekly else 30
        confidence = 92 if (monthly or weekly) and amount_spread <= 0.10 else 75
        merchant = items[-1].merchant or normalized
        existing = db.scalar(select(RecurringExpense).where(RecurringExpense.user_id == user_id, RecurringExpense.merchant == merchant))
        next_due = items[-1].txn_date + timedelta(days=cadence)
        if existing:
            existing.amount = money(avg_amount)
            existing.cadence_days = cadence
            existing.next_due_date = next_due
            existing.confidence = confidence
            existing.active = True
            obj = existing
        else:
            obj = RecurringExpense(
                user_id=user_id,
                merchant=merchant,
                amount=money(avg_amount),
                cadence_days=cadence,
                next_due_date=next_due,
                confidence=confidence,
                active=True,
            )
            db.add(obj)
        for t in items:
            t.is_recurring = True
        detected.append(obj)
    db.flush()
    return detected


def learn_stats(db: Session, user_id: int) -> dict:
    nudges = list(db.scalars(select(NudgeHistory).where(NudgeHistory.user_id == user_id)))
    responded = [n for n in nudges if n.accepted is not None]
    accepted = [n for n in responded if n.accepted]
    acceptance_rate = (len(accepted) / len(responded) * 100) if responded else 0
    days_gained = sum(n.estimated_days_gained for n in accepted)
    return {
        "accepted": len(accepted),
        "responded": len(responded),
        "acceptance_rate": round(acceptance_rate, 1),
        "days_gained": int(days_gained),
    }


def estimate_days_gained(overage: Decimal, rate: Decimal) -> int:
    if rate <= 0:
        return 0
    return max(1, min(7, int(math.ceil(float(money(overage) / rate)))))
