from __future__ import annotations

KEYWORDS = {
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "dominos", "mcd", "starbucks", "food"],
    "Groceries": ["blinkit", "zepto", "instamart", "grocery", "supermarket", "dmart", "bigbasket"],
    "Transport": ["uber", "ola", "rapido", "metro", "irctc", "fuel", "petrol", "diesel"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "shopping"],
    "Entertainment": ["bookmyshow", "netflix", "spotify", "prime video", "hotstar", "movie"],
    "Subscription": ["subscription", "netflix", "spotify", "youtube premium", "icloud", "google one"],
    "Rent": ["rent", "landlord", "housing"],
    "Tuition": ["tuition", "college", "university", "fees"],
    "Utilities": ["electricity", "water", "gas bill", "broadband", "wifi", "mobile recharge"],
}

FIXED_CATEGORIES = {"Rent", "Subscription", "Tuition", "Utilities"}
DEFAULT_CATEGORIES = ["Food", "Groceries", "Transport", "Shopping", "Entertainment", "Subscription", "Rent", "Tuition", "Utilities", "Health", "Education", "Other"]


def categorize(merchant: str | None, text: str | None = None) -> str:
    haystack = " ".join(x for x in [merchant or "", text or ""] if x).lower()
    for category, words in KEYWORDS.items():
        if any(word in haystack for word in words):
            return category
    return "Other"
