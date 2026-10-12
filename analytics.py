"""Data validation and calculations for the flight dashboard."""

import pandas as pd


REQUIRED_COLUMNS = (
    "flight_id", "airline", "origin", "destination", "flight_date",
    "scheduled_departure", "departure_delay_minutes", "arrival_delay_minutes",
    "flight_status",
)
STATUSES = ("On-time", "Delayed", "Cancelled")


def validate_columns(data):
    missing = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))


def load_flights(source):
    try:
        data = pd.read_csv(source)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError, OSError, ValueError) as exc:
        raise ValueError("Could not read this file as a valid CSV.") from exc
    validate_columns(data)
    return clean_flights(data)


def clean_flights(data):
    validate_columns(data)
    flights = data.copy()
    for column in ("flight_id", "airline", "origin", "destination", "flight_status"):
        flights[column] = flights[column].astype("string").str.strip()
        flights[column] = flights[column].replace("", pd.NA)
    flights["flight_date"] = pd.to_datetime(flights["flight_date"], format="%Y-%m-%d", errors="coerce")
    flights["scheduled_departure"] = pd.to_datetime(
        flights["scheduled_departure"].astype("string"), format="%H:%M", errors="coerce"
    ).dt.strftime("%H:%M")
    for column in ("departure_delay_minutes", "arrival_delay_minutes"):
        flights[column] = pd.to_numeric(flights[column], errors="coerce")

    # A flight without its identity, route, date, time, or status cannot be analyzed reliably.
    flights = flights.dropna(subset=(
        "flight_id", "airline", "origin", "destination", "flight_date",
        "scheduled_departure", "flight_status",
    ))
    flights = flights[flights["flight_status"].isin(STATUSES)].copy()
    flights = flights.drop_duplicates(subset="flight_id", keep="first")
    flights.loc[flights["flight_status"] == "Cancelled", [
        "departure_delay_minutes", "arrival_delay_minutes"
    ]] = float("nan")
    flights["flight_date"] = flights["flight_date"].dt.normalize()
    return flights.reset_index(drop=True)


def calculate_kpis(flights):
    completed = flights[flights["flight_status"] != "Cancelled"]
    measured = completed[completed["arrival_delay_minutes"].notna()]
    return {
        "total_flights": len(flights),
        "on_time_performance": round(
            100 * (measured["arrival_delay_minutes"] <= 15).mean(), 1
        ) if len(measured) else 0.0,
        "average_arrival_delay": round(measured["arrival_delay_minutes"].mean(), 1)
        if len(measured) else 0.0,
        "cancelled_flights": int((flights["flight_status"] == "Cancelled").sum()),
        "measured_flights": len(measured),
    }


def airline_delays(flights):
    completed = flights[flights["flight_status"] != "Cancelled"]
    return (completed.groupby("airline", as_index=False)["arrival_delay_minutes"]
            .mean().dropna().sort_values("arrival_delay_minutes", ascending=False))


def status_distribution(flights):
    completed = flights[flights["flight_status"] != "Cancelled"]
    counts = pd.Series({
        "On-time": int((completed["arrival_delay_minutes"] <= 15).sum()),
        "Delayed": int((completed["arrival_delay_minutes"] > 15).sum()),
        "Cancelled": int((flights["flight_status"] == "Cancelled").sum()),
    })
    return counts


def monthly_trends(flights):
    if flights.empty:
        return pd.DataFrame(columns=["month", "flights"])
    return (flights.assign(month=flights["flight_date"].dt.to_period("M").dt.to_timestamp())
            .groupby("month", as_index=False).size().rename(columns={"size": "flights"}))


def top_routes(flights, limit=5):
    if flights.empty:
        return pd.DataFrame(columns=["route", "flights"])
    return (flights.assign(route=flights["origin"] + " → " + flights["destination"])
            .groupby("route", as_index=False).size().rename(columns={"size": "flights"})
            .sort_values(["flights", "route"], ascending=[False, True]).head(limit))
