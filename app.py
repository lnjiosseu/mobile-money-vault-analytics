from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Mobile Money Vault Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
DATA = ROOT / "data"

CHANNEL_LABELS = {
    "INTERACTIVE_VOICE_RESPONSE": "IVR",
    "SUPPORT": "Live Support",
}
WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@st.cache_data
def load_data():
    hourly = pd.read_csv(DATA / "hourly_support_demand.csv", parse_dates=["event_date"])
    channel = pd.read_csv(DATA / "channel_cost_summary.csv")
    staffing = pd.read_csv(DATA / "staffing_scenario_comparison.csv")
    unlocks = pd.read_csv(DATA / "daily_unlocks_2025.csv", parse_dates=["event_date"])

    numeric_hourly = [
        "hour", "contacts", "handling_minutes", "avg_handling_minutes",
        "estimated_contact_cost_usd", "unique_customers",
    ]
    for col in numeric_hourly:
        hourly[col] = pd.to_numeric(hourly[col], errors="coerce").fillna(0)

    for col in [
        "contacts", "unique_customers", "avg_handling_minutes",
        "total_handling_minutes", "estimated_contact_cost_usd",
        "contact_share_pct", "avg_estimated_cost_per_contact_usd",
    ]:
        channel[col] = pd.to_numeric(channel[col], errors="coerce").fillna(0)

    for col in [
        "total_scheduled_agent_hours", "total_labor_cost_usd",
        "total_estimated_contact_cost_usd", "peak_agents_in_any_hour",
        "avg_agents_per_hour", "target_utilization",
        "labor_cost_difference_vs_base_usd", "labor_cost_difference_vs_base_pct",
    ]:
        staffing[col] = pd.to_numeric(staffing[col], errors="coerce").fillna(0)

    for col in ["total_unlocks", "support_unlocks", "ivr_unlocks", "chatbot_unlocks", "time_unlocks"]:
        unlocks[col] = pd.to_numeric(unlocks[col], errors="coerce").fillna(0)

    hourly["hour"] = hourly["hour"].astype(int)
    hourly["hour_label"] = hourly["hour"].map(lambda x: f"{x:02d}:00")
    return hourly, channel, staffing, unlocks


hourly, channel, staffing, unlocks = load_data()


def money(value):
    return f"${value:,.2f}"


def csv_download(frame):
    """Format downloadable numeric fields for readable CSV exports."""
    export = frame.copy()
    integer_columns = {
        "hour", "contacts", "unique_customers", "total_unlocks",
        "support_unlocks", "ivr_unlocks", "chatbot_unlocks", "time_unlocks",
        "peak_agents_in_any_hour", "total_scheduled_agent_hours",
    }
    for column in export.columns:
        if column in integer_columns:
            export[column] = pd.to_numeric(export[column], errors="coerce").round(0).astype("Int64")
        elif pd.api.types.is_numeric_dtype(export[column]):
            export[column] = pd.to_numeric(export[column], errors="coerce").round(2)
    return export.to_csv(index=False, float_format="%.2f")


def channel_labels(frame):
    result = frame.copy()
    if "support_channel" in result.columns:
        result["channel_label"] = result["support_channel"].map(CHANNEL_LABELS).fillna(result["support_channel"])
    return result


def render_footer():
    st.divider()
    st.caption(
        "Synthetic data for portfolio demonstration only. Cost figures are assumption-based "
        "estimates, not actual company or vendor costs."
    )


def add_daily_rolling_average(frame):
    """Calculate the 7-day average over the complete series before applying display filters."""
    daily = (
        frame.groupby("event_date", as_index=False)["contacts"]
        .sum()
        .sort_values("event_date")
    )
    daily["contacts_7d_avg"] = daily["contacts"].rolling(window=7, min_periods=1).mean()
    return daily


with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Dashboard page",
        ["Executive Overview", "Demand Analysis", "Channel Economics", "Staffing Scenarios"],
    )
    st.divider()
    st.caption("The date filter applies to daily/hourly activity on the Executive Overview and Demand Analysis pages.")
    min_date = hourly["event_date"].min().date()
    max_date = hourly["event_date"].max().date()
    selected_dates = st.date_input(
        "Analysis period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = selected_dates

if start_date > end_date:
    start_date, end_date = end_date, start_date

filtered_hourly = hourly[
    hourly["event_date"].dt.date.between(start_date, end_date)
].copy()
filtered_unlocks = unlocks[
    unlocks["event_date"].dt.date.between(start_date, end_date)
].copy()

daily_all = add_daily_rolling_average(hourly)
daily = daily_all[daily_all["event_date"].dt.date.between(start_date, end_date)].copy()

st.title("Mobile Money Vault Analytics")
st.caption("Support demand, channel economics, and staffing scenarios | Synthetic portfolio dataset")

if page == "Executive Overview":
    st.subheader("Executive Overview")

    contacts = filtered_hourly["contacts"].sum()
    handling_minutes = filtered_hourly["handling_minutes"].sum()
    estimated_cost = filtered_hourly["estimated_contact_cost_usd"].sum()
    total_unlocks = filtered_unlocks["total_unlocks"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Support contacts", f"{contacts:,.0f}")
    c2.metric("Handling hours", f"{handling_minutes / 60:,.1f}")
    c3.metric("Estimated contact cost", money(estimated_cost))
    c4.metric("Vault unlocks", f"{total_unlocks:,.0f}")

    left, right = st.columns(2)
    with left:
        fig = px.line(
            daily, x="event_date", y=["contacts", "contacts_7d_avg"],
            title="Daily support contacts and 7-day average",
            labels={"event_date": "", "value": "Contacts", "variable": "Series"},
        )
        fig.for_each_trace(
            lambda trace: trace.update(
                name="Daily contacts" if trace.name == "contacts" else "7-day moving average"
            )
        )
        fig.update_layout(legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        monthly = filtered_unlocks.assign(
            month=filtered_unlocks["event_date"].dt.to_period("M").astype(str)
        ).groupby("month", as_index=False)["total_unlocks"].sum()
        fig = px.bar(
            monthly, x="month", y="total_unlocks",
            title="Vault unlocks by month",
            labels={"month": "", "total_unlocks": "Unlocks"},
            text_auto=",",
        )
        fig.update_layout(xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    channel_display = channel_labels(channel)
    fig = px.pie(
        channel_display, names="channel_label", values="contacts",
        title="Annual support contact mix", hole=0.48,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info(
        "The channel mix uses the full-year 2025 summary. The date filter does not change this annual channel summary."
    )

    if not daily.empty:
        avg_daily = daily["contacts"].mean()
        peak_day = daily.loc[daily["contacts"].idxmax()]
        st.markdown(
            f"**What this suggests.** During the selected period, support averaged "
            f"**{avg_daily:,.1f} contacts per day**. The busiest day was "
            f"**{peak_day['event_date']:%b %d, %Y}**, with **{peak_day['contacts']:,.0f} contacts**."
        )

    st.download_button(
        "Download selected-period daily support data",
        data=csv_download(daily).encode("utf-8"),
        file_name="selected_period_daily_support.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download selected-period vault unlock data",
        data=csv_download(filtered_unlocks).encode("utf-8"),
        file_name="selected_period_vault_unlocks.csv",
        mime="text/csv",
    )


elif page == "Demand Analysis":
    st.subheader("Demand Analysis")
    contacts = filtered_hourly["contacts"].sum()
    active_days = filtered_hourly["event_date"].nunique()
    avg_per_day = contacts / active_days if active_days else 0
    peak_row = (
        filtered_hourly.groupby("hour", as_index=False)["contacts"]
        .sum().sort_values("contacts", ascending=False).head(1)
    )
    peak_hour = f'{int(peak_row.iloc[0]["hour"]):02d}:00' if not peak_row.empty else "N/A"

    c1, c2, c3 = st.columns(3)
    c1.metric("Contacts in selected period", f"{contacts:,.0f}")
    c2.metric("Average contacts per day", f"{avg_per_day:,.1f}")
    c3.metric("Busiest hour", peak_hour)

    hourly_profile = (
        filtered_hourly.groupby(["hour", "hour_label"], as_index=False)["contacts"]
        .sum().sort_values("hour")
    )
    fig = px.bar(
        hourly_profile, x="hour_label", y="contacts",
        title="Support contacts by hour of day",
        labels={"hour_label": "Hour", "contacts": "Contacts"},
        text_auto=",",
    )
    st.plotly_chart(fig, use_container_width=True)

    daily_for_weekday = filtered_hourly.groupby(
        ["event_date", "weekday"], as_index=False
    )["contacts"].sum()
    weekday = daily_for_weekday.groupby("weekday", as_index=False)["contacts"].mean()
    weekday["weekday"] = pd.Categorical(
        weekday["weekday"], categories=WEEKDAY_ORDER, ordered=True
    )
    weekday = weekday.sort_values("weekday")

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            weekday, x="weekday", y="contacts",
            title="Average daily contacts by weekday",
            labels={"weekday": "", "contacts": "Average contacts"},
            text_auto=".1f",
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.line(
            daily, x="event_date", y=["contacts", "contacts_7d_avg"],
            title="Daily support contacts and 7-day average",
            labels={"event_date": "", "value": "Contacts", "variable": "Series"},
        )
        fig.for_each_trace(
            lambda trace: trace.update(
                name="Daily contacts" if trace.name == "contacts" else "7-day moving average"
            )
        )
        fig.update_layout(legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)

    heat = filtered_hourly.pivot_table(
        index="weekday", columns="hour", values="contacts",
        aggfunc="sum", fill_value=0,
    ).reindex(WEEKDAY_ORDER)
    fig = px.imshow(
        heat, aspect="auto", color_continuous_scale="Blues",
        labels=dict(x="Hour of day", y="Weekday", color="Contacts"),
        title="Demand heatmap: weekday by hour",
    )
    st.plotly_chart(fig, use_container_width=True)

    if not hourly_profile.empty:
        peak_contacts = int(hourly_profile["contacts"].max())
        st.markdown(
            f"**Operational interpretation.** The highest-volume hour in the selected period "
            f"was **{peak_hour}**, with **{peak_contacts:,} contacts** across the selected dates. "
            "This profile can inform when additional support capacity may be needed. "
            "It does not, by itself, establish queue wait times or a required staffing schedule."
        )

    st.download_button(
        "Download selected-period hourly support data",
        data=csv_download(filtered_hourly).encode("utf-8"),
        file_name="selected_period_hourly_support.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download selected-period daily support data",
        data=csv_download(daily).encode("utf-8"),
        file_name="selected_period_daily_support.csv",
        mime="text/csv",
    )


elif page == "Channel Economics":
    st.subheader("Channel Economics")
    channel_display = channel_labels(channel)
    total_contacts = channel_display["contacts"].sum()
    total_contact_cost = channel_display["estimated_contact_cost_usd"].sum()
    total_minutes = channel_display["total_handling_minutes"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Annual contacts", f"{total_contacts:,.0f}")
    c2.metric("Estimated contact cost", money(total_contact_cost))
    c3.metric("Handling hours", f"{total_minutes / 60:,.1f}")

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            channel_display, x="channel_label", y="contacts",
            title="Annual contacts by channel", text_auto=",",
            labels={"channel_label": "Channel", "contacts": "Contacts"},
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(
            channel_display, x="channel_label", y="estimated_contact_cost_usd",
            title="Estimated contact cost by channel", text_auto="$,.2f",
            labels={"channel_label": "Channel", "estimated_contact_cost_usd": "Estimated cost (USD)"},
        )
        fig.update_yaxes(tickprefix="$", separatethousands=True)
        st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        channel_display, x="channel_label", y="avg_handling_minutes",
        title="Average handling minutes per contact", text_auto=".2f",
        labels={"channel_label": "Channel", "avg_handling_minutes": "Minutes"},
    )
    st.plotly_chart(fig, use_container_width=True)

    display = channel_display.rename(columns={
        "channel_label": "Channel",
        "contacts": "Contacts",
        "unique_customers": "Unique customers",
        "avg_handling_minutes": "Avg handling minutes",
        "total_handling_minutes": "Total handling minutes",
        "estimated_contact_cost_usd": "Estimated contact cost (USD)",
        "contact_share_pct": "Contact share (%)",
        "avg_estimated_cost_per_contact_usd": "Avg estimated cost/contact (USD)",
    })
    display = display.drop(columns=["support_channel"], errors="ignore")
    st.dataframe(
        display.style.format({
            "Contacts": "{:,.0f}",
            "Unique customers": "{:,.0f}",
            "Avg handling minutes": "{:,.2f}",
            "Total handling minutes": "{:,.2f}",
            "Estimated contact cost (USD)": "${:,.2f}",
            "Contact share (%)": "{:,.1f}%",
            "Avg estimated cost/contact (USD)": "${:,.2f}",
        }),
        use_container_width=True, hide_index=True,
    )

    support_row = channel_display[channel_display["support_channel"] == "SUPPORT"]
    if not support_row.empty and total_contact_cost > 0:
        support_cost_share = (
            support_row.iloc[0]["estimated_contact_cost_usd"] / total_contact_cost * 100
        )
        st.info(
            f"Under the project's synthetic cost assumptions, Live Support accounts for "
            f"**{support_cost_share:.1f}%** of estimated channel contact costs, despite "
            "representing just under half of contacts."
        )

    st.caption(
        "Contact costs are modeled channel-level estimates. They are not combined with staffing "
        "labor costs because the project assumptions do not establish whether the cost components overlap."
    )
    st.download_button(
        "Download annual channel economics",
        data=csv_download(channel_display).encode("utf-8"),
        file_name="annual_channel_economics.csv",
        mime="text/csv",
    )


elif page == "Staffing Scenarios":
    st.subheader("Staffing Scenarios")
    st.warning(
        "These are hourly capacity estimates based on assumed productive time and labor cost. "
        "They are not shift rosters or queueing simulations, and they do not establish wait times, "
        "abandonment, or service-level attainment."
    )

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            staffing, x="scenario", y="total_scheduled_agent_hours",
            title="Estimated scheduled agent-hours", text_auto=",",
            labels={"scenario": "Scenario", "total_scheduled_agent_hours": "Agent-hours"},
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(
            staffing, x="scenario", y="total_labor_cost_usd",
            title="Estimated labor cost by scenario", text_auto="$,.0f",
            labels={"scenario": "Scenario", "total_labor_cost_usd": "Estimated labor cost (USD)"},
        )
        fig.update_yaxes(tickprefix="$", separatethousands=True)
        st.plotly_chart(fig, use_container_width=True)

    display = staffing.rename(columns={
        "scenario": "Scenario",
        "total_scheduled_agent_hours": "Scheduled agent-hours",
        "total_labor_cost_usd": "Estimated labor cost (USD)",
        "total_estimated_contact_cost_usd": "Estimated contact cost (USD), separate",
        "peak_agents_in_any_hour": "Peak agents in an hour",
        "avg_agents_per_hour": "Average agents per hour",
        "target_utilization": "Assumed utilization",
        "labor_cost_difference_vs_base_usd": "Labor cost difference vs base (USD)",
        "labor_cost_difference_vs_base_pct": "Labor cost difference vs base (%)",
    })
    st.dataframe(
        display.style.format({
            "Scheduled agent-hours": "{:,.0f}",
            "Estimated labor cost (USD)": "${:,.2f}",
            "Estimated contact cost (USD), separate": "${:,.2f}",
            "Peak agents in an hour": "{:,.0f}",
            "Average agents per hour": "{:,.2f}",
            "Assumed utilization": "{:.0%}",
            "Labor cost difference vs base (USD)": "${:,.2f}",
            "Labor cost difference vs base (%)": "{:+.2f}%",
        }),
        use_container_width=True, hide_index=True,
    )
    st.caption(
        "The scenarios are alternatives. Do not add their rows together. Higher utilization reduces "
        "modeled labor cost under this formula, but could increase workload pressure. Contact costs "
        "and staffing labor costs remain separate estimates and are not summed."
    )
    st.download_button(
        "Download staffing scenario comparison",
        data=csv_download(staffing).encode("utf-8"),
        file_name="staffing_scenario_comparison.csv",
        mime="text/csv",
    )

render_footer()
