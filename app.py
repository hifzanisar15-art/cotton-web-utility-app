import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from io import BytesIO
from datetime import date, datetime

st.set_page_config(
    page_title="Cotton Web Utility App",
    page_icon="🏭",
    layout="wide"
)

DB_NAME = "cotton_web_reports.db"


# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            report_date TEXT,
            unit TEXT,
            filename TEXT,
            file_data BLOB,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (report_date, unit)
        )
    """)
         # Daily extracted values for graphing
    conn.execute("""
        CREATE TABLE IF NOT EXISTS utility_daily (
            report_date TEXT,
            unit TEXT,
            electricity_main REAL,
            electricity_backup REAL,
            gas_ft3 REAL,
            gas_mmbtu REAL,
            steam_kg REAL,
            water_liter REAL,
            boiler_diesel_liter REAL,
            generator_diesel_liter REAL,
            filename TEXT,
            PRIMARY KEY (report_date, unit)
        )
    """)
    conn.commit()
    conn.close()


def save_report(report_date, unit, filename, file_data, metrics):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        INSERT OR REPLACE INTO reports
        (report_date, unit, filename, file_data)
        VALUES (?, ?, ?, ?)
    """, (report_date, unit, filename, file_data))
    conn.execute("""
        INSERT OR REPLACE INTO utility_daily
        (report_date, unit, electricity_main, electricity_backup,
         gas_ft3, gas_mmbtu, steam_kg, water_liter,
         boiler_diesel_liter, generator_diesel_liter, filename)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_date, unit,
        metrics.get("electricity_main"),
        metrics.get("electricity_backup"),
        metrics.get("gas_ft3"),
        metrics.get("gas_mmbtu"),
        metrics.get("steam_kg"),
        metrics.get("water_liter"),
        metrics.get("boiler_diesel_liter"),
        metrics.get("generator_diesel_liter"),
        filename
    ))
    conn.commit()
    conn.close()


def get_reports():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT report_date, unit, filename, uploaded_at
        FROM reports
        ORDER BY report_date DESC, unit
    """, conn)
    conn.close()
    return df


def get_report(report_date, unit):
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute("""
        SELECT filename, file_data FROM reports
        WHERE report_date = ? AND unit = ?
    """, (report_date, unit)).fetchone()
    conn.close()
    return result


def get_daily_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT * FROM utility_daily
        ORDER BY report_date ASC, unit
    """, conn)
conn.close()
    if not df.empty:
        df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
        df = df.dropna(subset=["report_date"])
    return df


# ---------------- EXCEL DATA EXTRACTION ----------------
def to_number(value):
    """Convert an Excel cell to number, returning None for non-numeric cells."""
    if pd.isna(value):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def find_usage_value(df, label_text, usage_col=2):
    """
    Finds a row by its Description text and returns Usage value.
    This matches the structure in CW-03 Sheet4 and CW-04 Sheet1.
    """
    if df is None or df.empty:
        return None

 for _, row in df.iterrows():
        description = " ".join(str(x) for x in row.tolist() if not pd.isna(x))
        if label_text.lower() in description.lower():
            if len(row) > usage_col:
                return to_number(row.iloc[usage_col])
    return None


def extract_metrics(file_bytes, unit):
    """
    Reads daily utility figures from the report's daily consumption table.
    CW-03 uses Sheet4; CW-04 uses Sheet1.
    """
    excel = pd.ExcelFile(BytesIO(file_bytes))

    if unit == "CW-03":
        sheet_name = "Sheet4" if "Sheet4" in excel.sheet_names else excel.sheet_names[0]
    else:
        sheet_name = "Sheet1" if "Sheet1" in excel.sheet_names else excel.sheet_names[0]

    df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name, header=None)

    metrics = {
        "electricity_main": None,
        "electricity_backup": None,
        "gas_ft3": None,
        "gas_mmbtu": None,
        "steam_kg": None,
        "water_liter": None,
         "boiler_diesel_liter": None,
        "generator_diesel_liter": None
    }

    if unit == "CW-03":
        metrics["electricity_main"] = find_usage_value(df, "Meter Electrical Units")
        metrics["gas_ft3"] = find_usage_value(df, "Main Gas Consumption reading in unit")
        metrics["gas_mmbtu"] = find_usage_value(df, "Main Gas Consumption reading in MMBTU")
        metrics["steam_kg"] = find_usage_value(df, "Total Steam Production")
        metrics["water_liter"] = find_usage_value(df, "Total Water Consumption")
        metrics["boiler_diesel_liter"] = find_usage_value(df, "Diesel use for Boiler")
        metrics["generator_diesel_liter"] = find_usage_value(df, "Diesel use for Generator")
    else:
        metrics["electricity_main"] = find_usage_value(df, "Main Electrical Wapda Units")
        metrics["electricity_backup"] = find_usage_value(df, "Back-up meter Electrical Units")
        metrics["gas_ft3"] = find_usage_value(df, "Main Gas Consumption reading in unit")
        metrics["gas_mmbtu"] = find_usage_value(df, "Main Gas Consumption reading in MMBTU")
        metrics["steam_kg"] = find_usage_value(df, "Total Steam Production")
        metrics["water_liter"] = find_usage_value(df, "Total Water Consumption")
        metrics["boiler_diesel_liter"] = find_usage_value(df, "Diesel use for Boiler")
        metrics["generator_diesel_liter"] = find_usage_value(df, "Diesel use for Generator")

    return metrics


# ---------------- APP UI ----------------
init_db()

st.title("🏭 Cotton Web Utility Consumption App")
st.subheader("Daily Utility Monitoring Dashboard")
st.write("Welcome to Cotton Web Utility Monitoring System")

col1, col2 = st.columns(2)
with col1:
    st.info("🏢 Unit 3 - CW-03")
with col2:
    st.info("🏢 Unit 4 - CW-04")

st.divider()
st.header("📂 Upload Daily Excel Reports")

report_date = st.date_input("Select Report Date", value=date.today())
report_date_text = report_date.strftime("%Y-%m-%d")
st.info(f"📅 Selected Report Date: {report_date.strftime('%d-%m-%Y')}")

# Unit 3 upload
st.subheader("Unit 3 - CW-03")
file_unit3 = st.file_uploader(
    "Upload Unit 3 Excel File",
    type=["xlsx", "xls"],
    key="unit3"
)

if file_unit3 is not None:
    try:
              bytes3 = file_unit3.getvalue()
        df_unit3 = pd.read_excel(BytesIO(bytes3), sheet_name="Sheet4", header=None)
        st.write("Unit 3 Data Preview:")
        st.dataframe(df_unit3, use_container_width=True)

        if st.button("💾 Save Unit 3 Report"):
            metrics3 = extract_metrics(bytes3, "CW-03")
            save_report(report_date_text, "CW-03", file_unit3.name, bytes3, metrics3)
            st.success(f"Unit 3 report saved for {report_date.strftime('%d-%m-%Y')}!")
            st.write("Extracted values:", metrics3)
    except Exception as e:
        st.error(f"Error reading Unit 3 Excel file: {e}")

st.divider()

# Unit 4 upload
st.subheader("Unit 4 - CW-04")
file_unit4 = st.file_uploader(
    "Upload Unit 4 Excel File",
    type=["xlsx", "xls"],
    key="unit4"
)

if file_unit4 is not None:
    try:
        bytes4 = file_unit4.getvalue()
        df_unit4 = pd.read_excel(BytesIO(bytes4), sheet_name="Sheet1", header=None)
        st.write("Unit 4 Data Preview:")
        st.dataframe(df_unit4, use_container_width=True)

             if st.button("💾 Save Unit 4 Report"):
            metrics4 = extract_metrics(bytes4, "CW-04")
            save_report(report_date_text, "CW-04", file_unit4.name, bytes4, metrics4)
            st.success(f"Unit 4 report saved for {report_date.strftime('%d-%m-%Y')}!")
            st.write("Extracted values:", metrics4)
    except Exception as e:
        st.error(f"Error reading Unit 4 Excel file: {e}")

st.divider()

# ---------------- GRAPHS & ANALYTICS ----------------
st.header("📊 Utility Consumption Analytics")
daily_data = get_daily_data()

if daily_data.empty:
    st.warning("Graphs ke liye abhi database mein extracted daily data nahi hai. Reports upload karke Save Report button dabao.")
else:
    # Filters
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        units_available = sorted(daily_data["unit"].dropna().unique().tolist())
        selected_units = st.multiselect(
            "Select Unit(s)",
            options=units_available,
            default=units_available
        )
    with filter_col2:
        date_range = st.date_input(
            "Select date range for analytics",
             value=(daily_data["report_date"].min().date(),
                   daily_data["report_date"].max().date())
        )

    if selected_units and isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = daily_data[
            (daily_data["unit"].isin(selected_units)) &
            (daily_data["report_date"].dt.date >= start_date) &
            (daily_data["report_date"].dt.date <= end_date)
        ].copy()

        metric_labels = {
            "electricity_main": "Main Electricity (kWh/Units)",
            "electricity_backup": "Backup Electricity (kWh/Units)",
            "gas_ft3": "Gas (FT³)",
            "gas_mmbtu": "Gas (MMBTU)",
            "steam_kg": "Steam Production (KG)",
            "water_liter": "Water Consumption (Liter)",
            "boiler_diesel_liter": "Diesel for Boiler (Liter)",
            "generator_diesel_liter": "Diesel for Generator (Liter)"
        }

        metric = st.selectbox(
            "Select utility to plot",
            options=list(metric_labels.keys()),
            format_func=lambda x: metric_labels[x]
        )

        plot_data = filtered.dropna(subset=[metric]).copy()
        if plot_data.empty:
            st.info("Selected utility ke liye is date range mein data available nahi hai.")
        else:
            plot_data["Date"] = plot_data["report_date"].dt.strftime("%d-%b-%Y")
            fig_daily = px.line(
                plot_data,
                x="report_date",
                y=metric,
                color="unit",
                markers=True,
                title=f"Daily {metric_labels[metric]} — Unit Comparison"
            )
            fig_daily.update_layout(
                xaxis_title="Report Date",
                yaxis_title=metric_labels[metric],
                legend_title="Unit"
            )
            st.plotly_chart(fig_daily, use_container_width=True)

 # Monthly totals / averages (aggregated from daily records)
            plot_data["Month"] = plot_data["report_date"].dt.to_period("M").astype(str)
            monthly = plot_data.groupby(["Month", "unit"], as_index=False)[metric].sum()
            fig_monthly = px.bar(
                monthly,
                x="Month",
                y=metric,
                color="unit",
                barmode="group",
                title=f"Monthly {metric_labels[metric]} — Sum of Daily Reports"
            )
            fig_monthly.update_layout(xaxis_title="Month", yaxis_title=metric_labels[metric])
            st.plotly_chart(fig_monthly, use_container_width=True)

            # Yearly total
            plot_data["Year"] = plot_data["report_date"].dt.year.astype(str)
            yearly = plot_data.groupby(["Year", "unit"], as_index=False)[metric].sum()
            fig_yearly = px.bar(
                yearly,
                x="Year",
                y=metric,
                color="unit",
                barmode="group",
                title=f"Yearly {metric_labels[metric]} — Sum of Daily Reports"
            )
            fig_yearly.update_layout(xaxis_title="Year", yaxis_title=metric_labels[metric])
            st.plotly_chart(fig_yearly, use_container_width=True)

            st.subheader("📋 Filtered Daily Records")
                 st.dataframe(
                filtered.sort_values("report_date", ascending=False),
                use_container_width=True,
                hide_index=True
            )

st.divider()

# ---------------- SAVED REPORTS ----------------
st.header("📚 Previously Saved Reports")
saved_reports = get_reports()

if not saved_reports.empty:
    st.dataframe(saved_reports, use_container_width=True, hide_index=True)

    report_options = [
        f"{row['report_date']} | {row['unit']} | {row['filename']}"
        for _, row in saved_reports.iterrows()
    ]

    selected_report = st.selectbox("Select a saved report to download", report_options)
    selected_index = report_options.index(selected_report)
    selected_row = saved_reports.iloc[selected_index]

    result = get_report(selected_row["report_date"], selected_row["unit"])
    if result:
        filename, file_data = result
        st.download_button(
            label="📥 Download Selected Report",
            data=file_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.warning("No reports have been saved yet.")

st.success("Cotton Web Utility App is Running!")
