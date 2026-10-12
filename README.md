# Flight Data Analytics Dashboard

A small Streamlit project for exploring fictional flight operations data. It demonstrates CSV validation, data cleaning, summary metrics, filtering, and interactive charts with Pandas and Plotly.

## Problem statement

Flight records are easier to discuss when operational volume, delays, and cancellations can be viewed together. This dashboard turns a simple CSV into a compact overview suitable for a data analyst portfolio.

## Features

- Four summary metrics and four charts that respond to airline, date, and status filters
- Searchable records table and filtered CSV download
- CSV upload with required-column checks and clear errors
- Reproducible generator for 300 synthetic records

## Stack

Python 3.11+, Streamlit, Pandas, Plotly, and Pytest.

## Dashboard screenshot

Add a screenshot here after running the app locally.

## Run locally

From this directory, create and activate a Python 3.11+ virtual environment, then run:

```bash
pip install -r requirements.txt
python generate_data.py
streamlit run app.py
```

Run tests with `pytest -q`.

## Dataset and metrics

`data/flights.csv` contains **synthetic, fictional** records. It is not actual airline operational data. The generator uses seed `42` and includes flights from IndiGo, Air India, Emirates, Lufthansa, and Qatar Airways across several routes and dates in 2025. Required upload columns are `flight_id`, `airline`, `origin`, `destination`, `flight_date`, `scheduled_departure`, `departure_delay_minutes`, `arrival_delay_minutes`, and `flight_status`. Dates use `YYYY-MM-DD`; times use `HH:MM`; statuses are `On-time`, `Delayed`, or `Cancelled`.

On-time performance is the share of completed flights with a recorded arrival delay of **15 minutes or less**. Average arrival delay uses the same measured flights; cancellations and missing arrival delays are excluded from both calculations. Total flights and route/month counts include cancellations. Missing numeric delays remain blank. Records missing essential identity, route, date, time, or status are dropped; duplicate flight IDs keep the first record.

In the generated sample, there are **300 flights**, **16 cancellations**, **56.1% on-time performance** across 280 flights with measured arrivals, and **14.8 minutes average arrival delay**. The busiest route is **BOM → DXB** with 39 flights. These figures are examples from synthetic data, not airline findings.

## Limitations and possible improvements

The data is fictional and has no arrival timestamps, aircraft details, or disruption causes. A future version could add those fields, richer data quality reporting, and comparisons across periods while keeping the same simple CSV workflow.
