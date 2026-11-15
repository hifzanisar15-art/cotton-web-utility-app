
import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(
    page_title="Cotton Web Utility App",
    page_icon="🏭",
    layout="wide"
)

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

# Report date defaults to yesterday
report_date = st.date_input(
    "Select Report Date",
    value=date.today() - timedelta(days=1)
)

st.info(f"📅 Selected Report Date: {report_date.strftime('%d-%m-%Y')}")

st.divider()

# Unit 3 Upload
st.subheader("Unit 3 - CW-03")

file_unit3 = st.file_uploader(
    "Upload Unit 3 Excel File",
    type=["xlsx", "xls"],
    key="unit3"
)

if file_unit3 is not None:
    try:
        df_unit3 = pd.read_excel(file_unit3)

        st.success(
            f"Unit 3 report uploaded for {report_date.strftime('%d-%m-%Y')}"
        )

        st.write("Unit 3 Data Preview:")
        st.dataframe(df_unit3, use_container_width=True)

    except Exception as e:
        st.error(f"Error reading Unit 3 file: {e}")

st.divider()

# Unit 4 Upload
st.subheader("Unit 4 - CW-04")

file_unit4 = st.file_uploader(
    "Upload Unit 4 Excel File",
    type=["xlsx", "xls"],
    key="unit4"
)

if file_unit4 is not None:
    try:
        df_unit4 = pd.read_excel(file_unit4)

        st.success(
            f"Unit 4 report uploaded for {report_date.strftime('%d-%m-%Y')}"
        )

        st.write("Unit 4 Data Preview:")
        st.dataframe(df_unit4, use_container_width=True)

    except Exception as e:
        st.error(f"Error reading Unit 4 file: {e}")

st.success("Cotton Web Utility App is Running!")

