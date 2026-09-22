from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal
import httpx
from ..core.config import get_settings
from .categorizer import categorize

settings = get_settings()

AMOUNT_PATTERNS = [
    re.compile(r"(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.\d{1,2})?)", re.I),
    re.compile(r"(?:debited|spent|paid)\s+(?:by\s+)?(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.\d{1,2})?)", re.I),
]

DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b"),
    re.compile(r"\b(\d{1,2})[- ]([A-Za-z]{3,9})[- ](\d{2,4})\b"),
]

MERCHANT_PATTERNS = [
    re.compile(r"\b(?:at|to)\s+(?:vpa\s+)?([A-Za-z0-9._@&\- ]+?)(?:\.|,|\s+on\s+|\s+ref\b|$)", re.I),
    re.compile(r"\bmerchant\s*[:\-]\s*([A-Za-z0-9._@&\- ]+)", re.I),
]


def _parse_date(text: str) -> date:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        parts = match.groups()
        if parts[1].isalpha():
            raw = "-".join(parts)
            for fmt in ("%d-%b-%y", "%d-%b-%Y", "%d-%B-%y", "%d-%B-%Y"):
                try:
                    return datetime.strptime(raw, fmt).date()
                except ValueError:
                    pass
        else:
            day, month, year = map(int, parts)
            if year < 100:
                year += 2000
            try:
                return date(year, month, day)
            except ValueError:
                pass
    return date.today()


def _clean_merchant(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" .,-")
    value = re.sub(r"^VPA\s+", "", value, flags=re.I)
    return value[:255] or "Unknown merchant"


def parse_sms_regex(text: str) -> dict | None:
    amount = None
    for pattern in AMOUNT_PATTERNS:
        match = pattern.search(text)
        if match:
            amount = Decimal(match.group(1).replace(",", ""))
            break
    if amount is None:
        return None

    merchant = None
    for pattern in MERCHANT_PATTERNS:
        match = pattern.search(text)
        if match:
            merchant = _clean_merchant(match.group(1))
            break
    if merchant is None:
        # Fall back to a likely all-caps merchant token after common spend verbs.
        upper = re.search(r"\b(?:at|to)\s+([A-Z][A-Z0-9 &._@\-]{2,30})", text)
        merchant = _clean_merchant(upper.group(1)) if upper else "Unknown merchant"

    txn_date = _parse_date(text)
    category = categorize(merchant, text)
    return {
        "amount": amount,
        "merchant": merchant,
        "category": category,
        "txn_date": txn_date,
        "source": "sms",
        "raw_text": text,
        "parser": "regex",
        "confidence": 0.92 if merchant != "Unknown merchant" else 0.75,
    }


async def parse_with_llm(text: str, source: str = "sms") -> dict | None:
    if not (settings.llm_api_url and settings.llm_api_key and settings.llm_model):
        return None
    prompt = (
        "Extract one debit/payment transaction from the text. Return JSON only with keys "
        "amount (number), merchant (string), date (YYYY-MM-DD), type (debit/payment/other). "
        "If uncertain, return null for the uncertain field. Text: " + text
    )
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": "You extract structured payment transaction data. Output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(settings.llm_api_url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        content = body["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content)
        data = json.loads(content)
        if not data.get("amount"):
            return None
        merchant = _clean_merchant(str(data.get("merchant") or "Unknown merchant"))
        try:
            txn_date = datetime.strptime(str(data.get("date")), "%Y-%m-%d").date()
        except Exception:
            txn_date = date.today()
        return {
            "amount": Decimal(str(data["amount"])),
            "merchant": merchant,
            "category": categorize(merchant, text),
            "txn_date": txn_date,
            "source": source,
            "raw_text": text,
            "parser": "llm",
            "confidence": 0.8,
        }
    except Exception:
        return None


async def parse_transaction_text(text: str, source: str = "sms") -> dict | None:
    parsed = parse_sms_regex(text)
    if parsed:
        parsed["source"] = source
        return parsed
    return await parse_with_llm(text, source=source)
