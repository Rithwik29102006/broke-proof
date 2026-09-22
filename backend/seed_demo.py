from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.main import init_db
from app.models import IncomeCycle, Transaction, User, Category
from app.services.categorizer import categorize
from app.services.spending import jar_contribution, detect_recurring_expenses

init_db()
today = date.today()
with SessionLocal() as db:
    user = db.scalar(select(User).where(User.email == "demo@brokeproof.app"))
    if not user:
        user = User(name="Aarav", email="demo@brokeproof.app", password_hash=hash_password("demo12345"))
        db.add(user)
        db.flush()
        cycle = IncomeCycle(user_id=user.id, start_date=today - timedelta(days=10), end_date=today + timedelta(days=20), starting_balance=Decimal("15000"), income_label="Monthly allowance")
        db.add(cycle)
        db.flush()
        samples = [
            (10, "Hostel Rent", 4500, "Rent"),
            (9, "Swiggy", 280, "Food"),
            (8, "Metro", 80, "Transport"),
            (7, "Blinkit", 640, "Groceries"),
            (6, "Netflix", 199, "Subscription"),
            (5, "Swiggy", 360, "Food"),
            (4, "Amazon", 899, "Shopping"),
            (3, "Cafe", 220, "Food"),
            (2, "Uber", 175, "Transport"),
            (1, "Swiggy", 310, "Food"),
        ]
        for days_ago, merchant, amount, cat_name in samples:
            cat = db.scalar(select(Category).where(Category.name == cat_name))
            db.add(Transaction(user_id=user.id, cycle_id=cycle.id, category_id=cat.id, amount=amount, merchant=merchant, txn_date=today - timedelta(days=days_ago), source="manual", jar_contribution=jar_contribution(Decimal(str(amount))), is_recurring=cat.is_fixed))
        db.flush()
        detect_recurring_expenses(db, user.id)
        db.commit()
        print("Seeded demo user: demo@brokeproof.app / demo12345")
    else:
        print("Demo user already exists")
