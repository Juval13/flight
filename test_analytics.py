import io

import pandas as pd
import pytest

from analytics import (
    airline_delays, calculate_kpis, clean_flights, load_flights,
    monthly_trends, status_distribution, top_routes,
)


def sample():
    return pd.DataFrame({
        "flight_id": ["F1", "F2", "F3", "F4"],
        "airline": ["A", "A", "B", "B"],
        "origin": ["DEL", "DEL", "BOM", "BOM"],
        "destination": ["BOM", "BOM", "DEL", "DEL"],
        "flight_date": ["2025-01-01"] * 4,
        "scheduled_departure": ["10:00"] * 4,
        "departure_delay_minutes": [0, 20, None, 30],
        "arrival_delay_minutes": [0, 20, None, None],
        "flight_status": ["On-time", "Delayed", "Cancelled", "On-time"],
    })


def test_kpis_ignore_cancelled_and_missing_arrivals():
    kpis = calculate_kpis(clean_flights(sample()))
    assert kpis["total_flights"] == 4
    assert kpis["cancelled_flights"] == 1
    assert kpis["measured_flights"] == 2
    assert kpis["on_time_performance"] == 50.0
    assert kpis["average_arrival_delay"] == 10.0


def test_empty_data():
    empty = clean_flights(sample().iloc[0:0])
    assert calculate_kpis(empty)["on_time_performance"] == 0.0
    assert calculate_kpis(empty)["average_arrival_delay"] == 0.0
    assert monthly_trends(empty).empty
    assert top_routes(empty).empty


def test_invalid_columns():
    with pytest.raises(ValueError, match="Missing required columns"):
        load_flights(io.StringIO("flight_id,airline\nF1,A"))


def test_missing_values_and_bad_rows():
    data = sample()
    data["arrival_delay_minutes"] = data["arrival_delay_minutes"].astype(object)
    data.loc[0, "flight_date"] = "not a date"
    data.loc[1, "arrival_delay_minutes"] = "bad"
    cleaned = clean_flights(data)
    assert len(cleaned) == 3
    assert pd.isna(cleaned.loc[0, "arrival_delay_minutes"])
    assert pd.isna(cleaned.loc[1, "arrival_delay_minutes"])


def test_groupings_and_status_threshold():
    flights = clean_flights(sample())
    assert status_distribution(flights).to_dict() == {"On-time": 1, "Delayed": 1, "Cancelled": 1}
    assert airline_delays(flights).set_index("airline").loc["A", "arrival_delay_minutes"] == 10
    assert monthly_trends(flights)["flights"].tolist() == [4]
    assert top_routes(flights).iloc[0]["flights"] == 2


def test_invalid_csv_content():
    with pytest.raises(ValueError, match="valid CSV"):
        load_flights(io.BytesIO(b"\xff\xfe"))
