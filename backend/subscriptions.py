"""Subscription tier definitions and quota helpers (all amounts in CHF)."""
from datetime import datetime, timezone

# Fixed tier definitions – DO NOT mutate from frontend
TIERS = {
    "tier_1": {
        "id": "tier_1",
        "name": "Starter",
        "price": 0.0,
        "currency": "chf",
        "interval": "year",
        "max_postings": 5,
        "period": "year",
        "features": ["5 Inserate pro Jahr", "KI-Matching", "Bewerber-Übersicht"],
    },
    "tier_2": {
        "id": "tier_2",
        "name": "Plus",
        "price": 30.0,
        "currency": "chf",
        "interval": "month",
        "max_postings": 5,
        "period": "month",
        "features": ["5 Inserate pro Monat", "KI-Matching", "Bewerber-Pipeline", "E-Mail-Support"],
    },
    "tier_3": {
        "id": "tier_3",
        "name": "Pro",
        "price": 100.0,
        "currency": "chf",
        "interval": "month",
        "max_postings": 15,
        "period": "month",
        "features": ["15 Inserate pro Monat", "KI-Matching", "Priorisierter Support", "Stellen-Boost"],
    },
    "tier_4": {
        "id": "tier_4",
        "name": "Enterprise",
        "price": 250.0,
        "currency": "chf",
        "interval": "month",
        "max_postings": -1,  # unlimited
        "period": "month",
        "features": ["Unbegrenzte Inserate", "Premium Support", "Stellen-Boost", "Branding"],
    },
}


def period_key(period: str) -> str:
    """Return a comparable key for the current period (year or month)."""
    now = datetime.now(timezone.utc)
    if period == "year":
        return now.strftime("%Y")
    return now.strftime("%Y-%m")


def default_subscription(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "tier_id": "tier_1",
        "current_period_key": period_key("year"),
        "postings_used": 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def quota_status(sub: dict) -> dict:
    """Reset usage if period rolled over; return current view."""
    tier = TIERS[sub["tier_id"]]
    cur_key = period_key(tier["period"])
    if sub.get("current_period_key") != cur_key:
        sub["current_period_key"] = cur_key
        sub["postings_used"] = 0
    used = sub.get("postings_used", 0)
    return {
        "tier": tier,
        "current_period_key": cur_key,
        "postings_used": used,
        "remaining": "unlimited" if tier["max_postings"] == -1 else max(0, tier["max_postings"] - used),
        "can_post": tier["max_postings"] == -1 or used < tier["max_postings"],
    }
