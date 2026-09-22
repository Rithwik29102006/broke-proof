from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models import Category, NudgeHistory, Transaction, User
from ..schemas import ConfirmTransactionRequest, ManualTransactionRequest, ParsedTransaction, SmsParseRequest
from ..services.categorizer import categorize
from ..services.ocr import extract_text
from ..services.parser import parse_transaction_text
from ..services.spending import (
    detect_recurring_expenses,
    discretionary_daily_rate,
    get_active_cycle,
    jar_contribution,
    money,
    safe_to_spend_today,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _category(db: Session, name: str) -> Category:
    cat = db.scalar(select(Category).where(Category.name == name))
    if not cat:
        cat = db.scalar(select(Category).where(Category.name == "Other"))
    if not cat:
        raise HTTPException(500, "Categories are not initialized")
    return cat


def _serialize_nudge(nudge: NudgeHistory | None):
    if not nudge:
        return None
    return {
        "id": nudge.id,
        "message": nudge.message,
        "overage": float(nudge.overage),
        "options": ["log_anyway", "auto_trim"],
    }


def _commit_transaction(db: Session, user: User, amount: Decimal, merchant: str | None, category_name: str, note: str | None, txn_date: date, source: str, source_text: str | None):
    cycle = get_active_cycle(db, user.id, txn_date)
    if not cycle:
        raise HTTPException(400, "No active income cycle covers this transaction date")

    safe_before = safe_to_spend_today(db, user, cycle, txn_date)
    cat = _category(db, category_name)
    txn = Transaction(
        user_id=user.id,
        cycle_id=cycle.id,
        category_id=cat.id,
        amount=money(amount),
        merchant=merchant,
        note=note,
        txn_date=txn_date,
        source=source,
        source_text=source_text,
        jar_contribution=jar_contribution(amount),
        is_recurring=cat.is_fixed,
    )
    db.add(txn)
    db.flush()

    nudge = None
    if money(amount) > safe_before:
        overage = money(amount) - safe_before
        pct = int(round(float(overage / max(safe_before, Decimal("0.01")) * 100)))
        gentle = float(user.suggestion_aggressiveness or 1) < 0.85
        framing = "Want to gently trim tomorrow" if gentle else "Auto-trim tomorrow"
        nudge = NudgeHistory(
            user_id=user.id,
            transaction_id=txn.id,
            nudge_type="overspend",
            message=f"This purchase is {pct}% over today's remaining safe-to-spend amount. {framing} by ₹{overage}?",
            overage=overage,
        )
        db.add(nudge)
        db.flush()

    detect_recurring_expenses(db, user.id)
    db.commit()
    db.refresh(txn)
    if nudge:
        db.refresh(nudge)
    return txn, nudge


@router.post("/manual")
def add_manual(payload: ManualTransactionRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    merchant = payload.merchant.strip() if payload.merchant else None
    category_name = payload.category
    if not category_name and merchant:
        last_same_merchant = db.scalar(
            select(Transaction)
            .where(Transaction.user_id == user.id, Transaction.merchant == merchant)
            .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
            .limit(1)
        )
        if last_same_merchant:
            category_name = last_same_merchant.category.name
    category_name = category_name or categorize(merchant, payload.note)
    txn, nudge = _commit_transaction(
        db, user, payload.amount, merchant, category_name, payload.note, payload.txn_date or date.today(), "manual", None
    )
    return {"transaction_id": txn.id, "jar_contribution": float(txn.jar_contribution), "nudge": _serialize_nudge(nudge)}


@router.post("/parse-sms", response_model=list[ParsedTransaction])
async def parse_sms(payload: SmsParseRequest, user: User = Depends(get_current_user)):
    chunks = [x.strip() for x in payload.text.split("\n\n") if x.strip()]
    results = []
    for chunk in chunks:
        parsed = await parse_transaction_text(chunk, source="sms")
        if parsed:
            results.append(ParsedTransaction(**parsed))
    if not results:
        raise HTTPException(422, "Could not confidently extract a transaction. Please use manual entry or configure the LLM fallback.")
    return results


@router.post("/parse-screenshot", response_model=ParsedTransaction)
async def parse_screenshot(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(415, "Upload an image file")
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, "Image is too large (max 8 MB)")
    try:
        text = extract_text(data)
    except Exception as exc:
        raise HTTPException(422, "OCR could not read this image") from exc
    if not text:
        raise HTTPException(422, "No text was detected in the image")
    parsed = await parse_transaction_text(text, source="screenshot")
    if not parsed:
        raise HTTPException(422, "Text was detected, but a transaction could not be extracted")
    return ParsedTransaction(**parsed)


@router.post("/confirm")
def confirm_parsed(payload: ConfirmTransactionRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    txn, nudge = _commit_transaction(
        db,
        user,
        payload.amount,
        payload.merchant,
        payload.category,
        None,
        payload.txn_date,
        payload.source,
        payload.raw_text,
    )
    return {"transaction_id": txn.id, "jar_contribution": float(txn.jar_contribution), "nudge": _serialize_nudge(nudge)}


@router.get("")
def list_transactions(limit: int = 50, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 200)
    rows = list(
        db.scalars(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.txn_date.desc(), Transaction.id.desc())
            .limit(limit)
        )
    )
    return [
        {
            "id": t.id,
            "amount": float(t.amount),
            "merchant": t.merchant or "Unknown",
            "category": t.category.name,
            "date": t.txn_date.isoformat(),
            "source": t.source,
            "jar_contribution": float(t.jar_contribution),
            "is_recurring": t.is_recurring,
        }
        for t in rows
    ]
