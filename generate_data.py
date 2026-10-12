"""Generate reproducible fictional flight operations records."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path


AIRLINES = ("IndiGo", "Air India", "Emirates", "Lufthansa", "Qatar Airways")
ROUTES = (
    ("DEL", "BOM"), ("BOM", "BLR"), ("DEL", "DXB"), ("DXB", "FRA"),
    ("DOH", "LHR"), ("BLR", "DEL"), ("FRA", "DOH"), ("BOM", "DXB"),
    ("LHR", "DEL"), ("DXB", "DOH"),
)
FIELDNAMES = (
    "flight_id", "airline", "origin", "destination", "flight_date",
    "scheduled_departure", "departure_delay_minutes", "arrival_delay_minutes",
    "flight_status",
)


def generate_records(count=300, seed=42):
    rng = random.Random(seed)
    records = []
    for number in range(1, count + 1):
        origin, destination = rng.choice(ROUTES)
        cancelled = rng.random() < 0.045
        departure_delay = max(0, round(rng.gauss(12, 16)))
        arrival_delay = max(-8, departure_delay + round(rng.gauss(0, 9)))
        if not cancelled and rng.random() < 0.035:
            arrival_delay = ""
        if not cancelled and rng.random() < 0.025:
            departure_delay = ""
        records.append({
            "flight_id": f"FL{number:04d}",
            "airline": rng.choice(AIRLINES),
            "origin": origin,
            "destination": destination,
            "flight_date": (date(2025, 1, 1) + timedelta(days=rng.randrange(365))).isoformat(),
            "scheduled_departure": f"{rng.randrange(24):02d}:{rng.choice((0, 15, 30, 45)):02d}",
            "departure_delay_minutes": "" if cancelled else departure_delay,
            "arrival_delay_minutes": "" if cancelled else arrival_delay,
            "flight_status": "Cancelled" if cancelled else "Delayed" if arrival_delay != "" and arrival_delay > 15 else "On-time",
        })
    return records


def main():
    output = Path(__file__).parent / "data" / "flights.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(generate_records())
    print(f"Wrote 300 synthetic flight records to {output}")


if __name__ == "__main__":
    main()
