"""Generate a realistic 12-month bank statement CSV for the demo.

Plants deliberate "kill" candidates:
  - Duplicate streaming (Netflix Premium + Hulu, never watched Hulu-flavored merchants)
  - Planet Fitness charged 8 months with zero adjacent gym/wellness spend
  - Adobe Creative Cloud at $54.99/mo even though Canva Pro ($12.99/mo) also charged
  - NYT charged for the full year but only 2 NYT-Cooking type spends
  - Audible at $14.95/mo with no Amazon books or audiobook adjacencies
Keep candidates:
  - Spotify (lots of Spotify-adjacent music behavior would be expected; we keep it cheap)
  - Verizon, Geico (real utilities/insurance)
  - iCloud (cheap, ubiquitous)
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(7)

OUT = Path(__file__).resolve().parent.parent / "samples" / "statement_001.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

START = date(2025, 5, 1)
MONTHS = 12

rows = []  # (date, description, amount)  amount negative = debit

# --- Recurring subscriptions / bills ---
# (label_in_statement, monthly_amount, start_month_offset, end_month_offset_exclusive, jitter_days)
recurring = [
    ("NETFLIX.COM",              -22.99, 0, 12, 0),   # Premium tier
    ("Hulu*HULU",                -17.99, 0, 12, 1),   # Duplicate streaming, never used
    ("SPOTIFY USA",              -11.99, 0, 12, 0),
    ("Adobe Creative Cloud",     -54.99, 0, 12, 1),   # Expensive
    ("CANVA* MONTHLY",           -12.99, 0, 12, 1),   # Overlaps with Adobe
    ("NYTimes*All Access",       -17.00, 0, 12, 1),
    ("AUDIBLE*MEMBERSHIP",       -14.95, 0, 12, 1),
    ("Planet Fitness Black",     -24.99, 0, 8,  1),   # 8 months, abandoned
    ("VERIZON WIRELESS",         -85.00, 0, 12, 2),   # Real utility
    ("GEICO AUTO PAY",          -132.40, 0, 12, 2),   # Real insurance
    ("APPLE.COM/BILL iCloud+",    -2.99, 0, 12, 0),   # Cheap, keep
    ("CHATGPT PLUS",             -20.00, 3, 12, 1),   # Added recently
]

for label, amt, mo_start, mo_end, jitter in recurring:
    # pick a "day of month" anchor
    anchor_day = random.randint(1, 27)
    for m in range(mo_start, mo_end):
        d = date(START.year + (START.month + m - 1) // 12,
                 ((START.month + m - 1) % 12) + 1,
                 anchor_day)
        if jitter:
            d = d + timedelta(days=random.randint(-jitter, jitter))
        # add some price drift on a couple
        a = amt + (random.choice([-0.0, 0.0, 0.0]) if amt < -20 else 0.0)
        rows.append((d, label, round(a, 2)))

# --- One-time / variable spend ---
merchants_variable = [
    ("STARBUCKS #4421",       (-4, -9)),
    ("UBER TRIP",             (-8, -28)),
    ("WHOLE FOODS MARKET",   (-22, -120)),
    ("AMAZON.COM*MK4LJ",     (-12, -85)),
    ("SHELL OIL 12345",      (-30, -65)),
    ("TARGET T-1198",        (-15, -140)),
    ("CHIPOTLE 0987",         (-9, -18)),
    ("DOORDASH*RAMEN",       (-18, -42)),
    ("CVS/PHARMACY",          (-6, -55)),
    ("APPLE.COM/BILL",       (-0.99, -9.99)),  # one-off app purchases
    ("LYFT *RIDE",            (-7, -24)),
    ("TRADER JOE'S #112",    (-25, -90)),
    ("DELTA AIR LINES",     (-180, -480)),
    ("AIRBNB * HMQRX",      (-120, -320)),
    ("HOME DEPOT #6710",     (-22, -160)),
]

# Incoming paychecks
for m in range(MONTHS):
    pay_date = date(START.year + (START.month + m - 1) // 12,
                    ((START.month + m - 1) % 12) + 1,
                    15)
    rows.append((pay_date, "ACME CORP PAYROLL", round(3850.00 + random.uniform(-50, 50), 2)))

# Generate ~12-18 variable transactions per month
for m in range(MONTHS):
    n = random.randint(12, 18)
    for _ in range(n):
        merchant, (lo, hi) = random.choice(merchants_variable)
        d = date(START.year + (START.month + m - 1) // 12,
                 ((START.month + m - 1) % 12) + 1,
                 random.randint(1, 28))
        amt = round(random.uniform(lo, hi), 2)
        rows.append((d, merchant, amt))

# Sort by date
rows.sort(key=lambda r: r[0])

with OUT.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "description", "amount"])
    for d, desc, amt in rows:
        w.writerow([d.isoformat(), desc, f"{amt:.2f}"])

print(f"Wrote {len(rows)} rows to {OUT}")
