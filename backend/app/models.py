from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .core.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    no_spend_weekend: Mapped[bool] = mapped_column(Boolean, default=False)
    suggestion_aggressiveness: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"))

    cycles: Mapped[list["IncomeCycle"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class IncomeCycle(Base):
    __tablename__ = "income_cycles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    starting_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    income_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="cycles")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="cycle", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("income_cycles.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    txn_date: Mapped[date] = mapped_column(Date, index=True)
    source: Mapped[str] = mapped_column(String(30), default="manual")
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    jar_contribution: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cycle: Mapped[IncomeCycle] = relationship(back_populates="transactions")
    category: Mapped[Category] = relationship()


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"
    __table_args__ = (UniqueConstraint("user_id", "merchant", name="uq_recurring_user_merchant"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    merchant: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cadence_days: Mapped[int] = mapped_column(Integer, default=30)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class NudgeHistory(Base):
    __tablename__ = "nudge_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    nudge_type: Mapped[str] = mapped_column(String(50), default="overspend")
    message: Mapped[str] = mapped_column(Text)
    overage: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    response: Mapped[str | None] = mapped_column(String(30), nullable=True)
    accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    estimated_days_gained: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BudgetAdjustment(Base):
    __tablename__ = "budget_adjustments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    adjustment_date: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    reason: Mapped[str] = mapped_column(String(120), default="nudge")
    applied: Mapped[bool] = mapped_column(Boolean, default=True)
