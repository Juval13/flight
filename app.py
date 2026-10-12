"""Streamlit dashboard for synthetic flight operations data."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import (
    airline_delays, calculate_kpis, load_flights, monthly_trends,
    status_distribution, top_routes,
)


st.set_page_config(page_title="Flight Operations Analytics", page_icon="✈", layout="wide")
st.markdown("""<style>
    .block-container {max-width: 1260px; padding-top: 2.2rem; padding-bottom: 3rem}
    h1, h2, h3 {color: #102b4e}
    [data-testid="stMetric"] {background: #f2f7fc; border: 1px solid #dce9f5;
        border-radius: 10px; padding: 1rem 1.2rem}
    [data-testid="stMetricLabel"] {color: #52677c}
    [data-testid="stMetricValue"] {color: #0c477d}
    div[data-testid="stPlotlyChart"] {border: 1px solid #e5edf5; border-radius: 10px;
        padding: .25rem; background: white}
</style>""", unsafe_allow_html=True)


@st.cache_data
def sample_data():
    return load_flights(Path(__file__).parent / "data" / "flights.csv")


def style_chart(fig, height=340):
    fig.update_layout(
        height=height, margin=dict(l=20, r=20, t=35, b=20),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial, sans-serif", color="#28445f"),
        colorway=["#1769aa", "#69a9d8", "#d48b42"],
        showlegend=False,
    )
    return fig


st.title("Flight Operations Analytics")
st.caption("Analyze flight performance, delays, and operational trends.")
st.info("Sample data contains 300 synthetic, fictional flight records. It is not actual airline operational data.", icon="ℹ️")

with st.sidebar:
    st.header("Data & filters")
    upload = st.file_uploader("Upload flight CSV", type="csv", help="Use the columns listed in the README.")

try:
    flights = load_flights(upload) if upload is not None else sample_data()
except ValueError as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    if upload is not None:
        st.success(f"Loaded {len(flights)} valid flight records.")
    if flights.empty:
        st.warning("No valid records are available in this dataset.")
        st.stop()
    airlines = ["All airlines"] + sorted(flights["airline"].dropna().unique().tolist())
    statuses = ["All statuses", "On-time", "Delayed", "Cancelled"]
    if st.button("Reset filters", width="stretch"):
        for key in ("airline_filter", "status_filter", "date_filter"):
            st.session_state.pop(key, None)
        st.rerun()
    airline = st.selectbox("Airline", airlines, key="airline_filter")
    date_range = st.date_input(
        "Flight date range",
        value=(flights["flight_date"].min().date(), flights["flight_date"].max().date()),
        min_value=flights["flight_date"].min().date(),
        max_value=flights["flight_date"].max().date(),
        key="date_filter",
    )
    status = st.selectbox("Flight status", statuses, key="status_filter")

filtered = flights.copy()
if airline != "All airlines":
    filtered = filtered[filtered["airline"] == airline]
if len(date_range) == 2:
    start, end = date_range
    filtered = filtered[filtered["flight_date"].dt.date.between(start, end)]
if status != "All statuses":
    if status == "Cancelled":
        filtered = filtered[filtered["flight_status"] == "Cancelled"]
    elif status == "Delayed":
        filtered = filtered[(filtered["flight_status"] != "Cancelled") & (filtered["arrival_delay_minutes"] > 15)]
    else:
        filtered = filtered[(filtered["flight_status"] != "Cancelled") & (filtered["arrival_delay_minutes"] <= 15)]

if len(date_range) != 2:
    st.warning("Select both a start and end date to apply the date filter.")

metrics = calculate_kpis(filtered)
cards = st.columns(4)
cards[0].metric("Total Flights", f"{metrics['total_flights']:,}", help="All records in the current filter, including cancellations.")
cards[1].metric("On-Time Performance", f"{metrics['on_time_performance']:.1f}%", help="Completed flights arriving within 15 minutes, divided by completed flights with a recorded arrival delay.")
cards[2].metric("Avg Arrival Delay", f"{metrics['average_arrival_delay']:.1f} min", help="Mean arrival delay for completed flights with a recorded arrival delay. Early arrivals have negative values.")
cards[3].metric("Cancelled Flights", f"{metrics['cancelled_flights']:,}", help="Flights marked Cancelled in the current filter.")

st.subheader("Operational overview")
if filtered.empty:
    st.info("No flights match these filters. Adjust the filters to see charts and records.")
else:
    left, right = st.columns(2)
    delays = airline_delays(filtered)
    with left:
        st.markdown("**Average Arrival Delay by Airline**")
        fig = px.bar(delays, x="airline", y="arrival_delay_minutes", color_discrete_sequence=["#1769aa"])
        fig.update_xaxes(title=None, tickangle=-20)
        fig.update_yaxes(title="Minutes", gridcolor="#e8eff6")
        st.plotly_chart(style_chart(fig), width="stretch")
    with right:
        st.markdown("**Flight Status Distribution**")
        counts = status_distribution(filtered)
        fig = px.pie(values=counts.values, names=counts.index, hole=0.62,
                     color=counts.index, color_discrete_map={"On-time": "#1769aa", "Delayed": "#e2a251", "Cancelled": "#bd5b62"})
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.15, x=0.1))
        st.plotly_chart(style_chart(fig), width="stretch")
    left, right = st.columns(2)
    with left:
        st.markdown("**Monthly Flight Trends**")
        trend = monthly_trends(filtered)
        fig = px.line(trend, x="month", y="flights", markers=True, color_discrete_sequence=["#1769aa"])
        fig.update_xaxes(title=None, tickformat="%b %Y")
        fig.update_yaxes(title="Flights", rangemode="tozero", gridcolor="#e8eff6")
        st.plotly_chart(style_chart(fig), width="stretch")
    with right:
        st.markdown("**Top Routes by Flight Volume**")
        routes = top_routes(filtered).sort_values("flights")
        fig = px.bar(routes, x="flights", y="route", orientation="h", color_discrete_sequence=["#1769aa"])
        fig.update_xaxes(title="Flights", gridcolor="#e8eff6")
        fig.update_yaxes(title=None)
        st.plotly_chart(style_chart(fig), width="stretch")

st.subheader("Flight records")
search = st.text_input("Search flight ID, airline, or route", placeholder="Search records…")
records = filtered.copy()
if search:
    searchable = records[["flight_id", "airline", "origin", "destination"]].fillna("").astype(str)
    records = records[searchable.apply(lambda column: column.str.contains(search, case=False, regex=False)).any(axis=1)]
st.caption(f"Showing {len(records):,} of {len(filtered):,} filtered records")
display = records.rename(columns={
    "flight_id": "Flight ID", "airline": "Airline", "origin": "Origin",
    "destination": "Destination", "flight_date": "Date",
    "departure_delay_minutes": "Departure Delay", "arrival_delay_minutes": "Arrival Delay",
    "flight_status": "Status",
})[["Flight ID", "Airline", "Origin", "Destination", "Date", "Departure Delay", "Arrival Delay", "Status"]]
st.dataframe(display, width="stretch", hide_index=True)
export = records.copy()
export["flight_date"] = export["flight_date"].dt.strftime("%Y-%m-%d")
st.download_button("Download filtered records CSV", export.to_csv(index=False).encode("utf-8"),
                   "filtered_flights.csv", "text/csv", disabled=records.empty)
