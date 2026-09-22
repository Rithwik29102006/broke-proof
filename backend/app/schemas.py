from datetime import date
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    starting_balance: Decimal = Field(gt=0)
    cycle_start: date
    cycle_end: date

    @field_validator("cycle_end")
    @classmethod
    def validate_cycle_end(cls, value, info):
        start = info.data.get("cycle_start")
        if start and value <= start:
            raise ValueError("cycle_end must be after cycle_start")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ManualTransactionRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    merchant: str | None = Field(default=None, max_length=255)
    category: str | None = None
    note: str | None = Field(default=None, max_length=500)
    txn_date: date | None = None


class SmsParseRequest(BaseModel):
    text: str = Field(min_length=3, max_length=10000)


class ParsedTransaction(BaseModel):
    amount: Decimal
    merchant: str
    category: str
    txn_date: date
    source: str
    raw_text: str | None = None
    parser: str = "regex"
    confidence: float = 0.9


class ConfirmTransactionRequest(ParsedTransaction):
    pass


class NudgeResponseRequest(BaseModel):
    accepted: bool
    action: str = Field(pattern="^(log_anyway|auto_trim)$")


class WeekendModeRequest(BaseModel):
    enabled: bool
