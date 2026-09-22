"""Cron-friendly maintenance task.

This does not write derived balance values (the API computes those live); it refreshes recurring-expense
classification so future deductions stay current even on days when the user does not open the app.
"""
from sqlalchemy import select
from app.core.database import SessionLocal
from app.main import init_db
from app.models import User
from app.services.spending import detect_recurring_expenses, get_active_cycle, projected_broke_date


def main():
    init_db()
    with SessionLocal() as db:
        for user in db.scalars(select(User)):
            detect_recurring_expenses(db, user.id)
            cycle = get_active_cycle(db, user.id)
            if cycle:
                projected_broke_date(db, user, cycle)
        db.commit()
    print("Broke-Proof daily recompute complete")


if __name__ == "__main__":
    main()
