import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import date

st.set_page_config(
    page_title="Cotton Web Utility App",
    page_icon="🏭",
    layout="wide"
)

DB_NAME = "cotton_web_reports.db"


# Create database and table
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
    conn.commit()
    conn.close()


# Save report
def save_report(report_date, unit, filename, file_data):
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        INSERT OR REPLACE INTO reports
        (report_date, unit, filename, file_data)
        VALUES (?, ?, ?, ?)
    """, (report_date, unit, filename, file_data))

    conn.commit()
    conn.close()


# Get saved reports
def get_reports():
    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query("""
        SELECT report_date, unit, filename, uploaded_at
        FROM reports
        ORDER BY report_date DESC
    """, conn)

    conn.close()
    return df


# Get report file
def get_report(report_date, unit):
    conn = sqlite3.connect(DB_NAME)

    result = conn.execute("""
        SELECT filename, file_data
        FROM reports
        WHERE report_date = ? AND unit = ?
    """, (report_date, unit)).fetchone()

    conn.close()
    return result


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

report_date = st.date_input(
    "Select Report Date",
    value=date.today()
)

report_date_text = report_date.strftime("%Y-%m-%d")

st.info(
    f"📅 Selected Report Date: {report_date.strftime('%d-%m-%Y')}"
)

# Unit 3
st.subheader("Unit 3 - CW-03")

file_unit3 = st.file_uploader(
    "Upload Unit 3 Excel File",
    type=["xlsx", "xls"],
    key="unit3"
)

if file_unit3 is not None:

    st.write("Unit 3 Data Preview:")

    try:
        df_unit3 = pd.read_excel(
            BytesIO(file_unit3.getvalue()),
            header=None
        )

        st.dataframe(df_unit3, use_container_width=True)

        if st.button("💾 Save Unit 3 Report"):

            save_report(
                report_date_text,
                "CW-03",
                file_unit3.name,
                file_unit3.getvalue()
            )

            st.success(
                f"Unit 3 report saved for {report_date.strftime('%d-%m-%Y')}!"
            )

    except Exception as e:
        st.error(f"Error reading Unit 3 Excel file: {e}")

st.divider()

# Unit 4
st.subheader("Unit 4 - CW-04")

file_unit4 = st.file_uploader(
    "Upload Unit 4 Excel File",
    type=["xlsx", "xls"],
    key="unit4"
)

if file_unit4 is not None:

    st.write("Unit 4 Data Preview:")

    try:
        df_unit4 = pd.read_excel(
            BytesIO(file_unit4.getvalue()),
            header=None
        )

        st.dataframe(df_unit4, use_container_width=True)

        if st.button("💾 Save Unit 4 Report"):

            save_report(
                report_date_text,
                "CW-04",
                file_unit4.name,
                file_unit4.getvalue()
            )

            st.success(
                f"Unit 4 report saved for {report_date.strftime('%d-%m-%Y')}!"
            )

    except Exception as e:
        st.error(f"Error reading Unit 4 Excel file: {e}")

st.divider()

# Previously saved reports
st.header("📚 Previously Saved Reports")

saved_reports = get_reports()

if not saved_reports.empty:

    st.dataframe(
        saved_reports,
        use_container_width=True,
        hide_index=True
    )

    report_options = [
        f"{row['report_date']} | {row['unit']} | {row['filename']}"
        for _, row in saved_reports.iterrows()
    ]

    selected_report = st.selectbox(
        "Select a saved report to download",
        report_options
    )

    if st.button("📥 Download Selected Report"):

        selected_index = report_options.index(selected_report)
        selected_row = saved_reports.iloc[selected_index]

        result = get_report(
            selected_row["report_date"],
            selected_row["unit"]
        )

        if result:
            filename, file_data = result

            st.download_button(
                label="Download Excel File",
                data=file_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.warning("No reports have been saved yet.")

st.success("Cotton Web Utility App is Running!")
