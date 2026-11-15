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

