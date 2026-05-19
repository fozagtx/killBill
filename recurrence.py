"""Deterministic preprocessing: cluster bank-statement rows into recurring charges.

This is plain Python (not LLM) because pattern-matching dates and amounts is a
solved problem and we don't want to burn tokens on it. The LLM's job in the
later Jac layer is *judgment* (kill / keep / downgrade) on top of these clusters.
"""
from __future__ import annotations

import csv
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


# -------------------- normalization --------------------

_STRIP_PATTERNS = [
    re.compile(r"\b\d{3,}\b"),                      # store numbers
    re.compile(r"#\s*\w+"),                         # #1198
    re.compile(r"\*[A-Z0-9]{4,}"),                  # *MK4LJ
    re.compile(r"\s+POS\b", re.I),
    re.compile(r"\b(PURCHASE|PMT|PAYMENT|RECURRING|AUTOPAY|AUTH)\b", re.I),
]


def normalize_merchant(raw: str) -> str:
    s = raw.strip().upper()
    for p in _STRIP_PATTERNS:
        s = p.sub("", s)
    s = re.sub(r"[^A-Z0-9\.\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Keep up to first 3 words to merge variants like "STARBUCKS 4421" and "STARBUCKS DT NY"
    parts = s.split(" ")
    return " ".join(parts[:3]) if parts else s


# -------------------- data types --------------------

@dataclass
class Transaction:
    txn_date: date
    description: str
    amount: float                # negative = debit
    merchant: str = ""           # normalized

    @classmethod
    def from_row(cls, row: dict) -> "Transaction":
        d = datetime.strptime(row["date"], "%Y-%m-%d").date()
        amt = float(row["amount"])
        desc = row["description"]
        return cls(txn_date=d, description=desc, amount=amt, merchant=normalize_merchant(desc))


@dataclass
class ChargeCluster:
    """A group of transactions that look like the same recurring charge."""
    merchant_normalized: str
    raw_descriptions: list[str] = field(default_factory=list)
    dates: list[date] = field(default_factory=list)
    amounts: list[float] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.amounts)

    @property
    def median_amount(self) -> float:
        return float(statistics.median(self.amounts))

    @property
    def total_paid(self) -> float:
        return float(sum(self.amounts))

    @property
    def first_date(self) -> date:
        return min(self.dates)

    @property
    def last_date(self) -> date:
        return max(self.dates)

    @property
    def avg_gap_days(self) -> float:
        if len(self.dates) < 2:
            return 0.0
        ds = sorted(self.dates)
        gaps = [(ds[i + 1] - ds[i]).days for i in range(len(ds) - 1)]
        return sum(gaps) / len(gaps)

    @property
    def cadence_label(self) -> str:
        g = self.avg_gap_days
        if 25 <= g <= 35:
            return "monthly"
        if 6 <= g <= 9:
            return "weekly"
        if 13 <= g <= 16:
            return "biweekly"
        if 85 <= g <= 100:
            return "quarterly"
        if 360 <= g <= 380:
            return "annual"
        return "irregular"

    @property
    def is_recurring(self) -> bool:
        return self.count >= 3 and self.cadence_label != "irregular"

    def to_dict(self) -> dict:
        return {
            "merchant_normalized": self.merchant_normalized,
            "raw_descriptions": list(set(self.raw_descriptions))[:3],
            "count": self.count,
            "median_amount": round(self.median_amount, 2),
            "total_paid": round(self.total_paid, 2),
            "first_date": self.first_date.isoformat(),
            "last_date": self.last_date.isoformat(),
            "avg_gap_days": round(self.avg_gap_days, 1),
            "cadence_label": self.cadence_label,
        }


# -------------------- ingest + cluster --------------------

def load_transactions(csv_path: str | Path) -> list[Transaction]:
    p = Path(csv_path)
    out: list[Transaction] = []
    with p.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                out.append(Transaction.from_row(row))
            except Exception:
                continue
    return out


def cluster_recurring(
    transactions: Iterable[Transaction],
    amount_tolerance_pct: float = 0.10,
) -> list[ChargeCluster]:
    """Group debits by (normalized merchant, similar amount).

    A new cluster is created if the amount differs from existing cluster medians
    by more than `amount_tolerance_pct` — this keeps Netflix at $14.99 separate
    from a one-off Netflix gift card at $30.
    """
    by_merchant: dict[str, list[ChargeCluster]] = defaultdict(list)
    for t in transactions:
        if t.amount >= 0:
            continue  # ignore credits
        key = t.merchant
        bucket = by_merchant[key]
        placed = False
        for cl in bucket:
            ref = cl.median_amount
            if ref == 0:
                continue
            if abs(t.amount - ref) / abs(ref) <= amount_tolerance_pct:
                cl.amounts.append(t.amount)
                cl.dates.append(t.txn_date)
                cl.raw_descriptions.append(t.description)
                placed = True
                break
        if not placed:
            bucket.append(
                ChargeCluster(
                    merchant_normalized=key,
                    raw_descriptions=[t.description],
                    dates=[t.txn_date],
                    amounts=[t.amount],
                )
            )

    out: list[ChargeCluster] = []
    for clusters in by_merchant.values():
        out.extend(clusters)
    # Sort: recurring first, then by absolute monthly cost
    out.sort(key=lambda c: (not c.is_recurring, -abs(c.median_amount * (30 / max(c.avg_gap_days, 1)))))
    return out


def find_recurring(csv_path: str | Path) -> list[dict]:
    """Top-level helper used by the Jac layer. Returns plain dicts."""
    txns = load_transactions(csv_path)
    clusters = cluster_recurring(txns)
    return [c.to_dict() for c in clusters if c.is_recurring]


def transaction_count(csv_path: str | Path) -> int:
    return len(load_transactions(csv_path))


if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "samples/statement_001.csv"
    recs = find_recurring(path)
    print(json.dumps(recs, indent=2))
    print(f"\nFound {len(recs)} recurring charges in {transaction_count(path)} transactions.")
