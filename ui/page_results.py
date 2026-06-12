"""
Results explorer page — interactive summary charts, table status overview,
and detailed column/row level validation drill-down.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from core.models import ValidationStatus
from ui.components import render_section_header, render_empty_state, render_metric_card, render_status_badge


def render():
    render_section_header("Validation Results", "📊")

    # ── Check for validation results ──────────────────────────────────────
    run_summary = st.session_state.get("last_validation")
    if not run_summary:
        render_empty_state(
            "📈",
            "No results available",
            "Please configure and run a validation on the Validate page first to view detailed results.",
        )
        return

    # Extract summary info
    timestamp = run_summary["timestamp"]
    total_tables = run_summary["total_tables"]
    passed = run_summary["passed"]
    failed = run_summary["failed"]
    warned = run_summary["warned"]
    pass_rate = run_summary["pass_rate"]
    duration = run_summary["duration"]
    summaries = run_summary["summaries"]
    results = run_summary["results"]
    report_gen = run_summary["report_gen"]
    src_label = run_summary["src_label"]
    tgt_label = run_summary["tgt_label"]

    # ── Header Meta ───────────────────────────────────────────────────────
    st.markdown(
        f'<div style="color:var(--text-secondary);margin-bottom:24px">'
        f"Validation run completed at <strong>{timestamp}</strong> | "
        f"Sources: <strong>{src_label}</strong> ↔ <strong>{tgt_label}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Overview Dashboard Row ────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("##### 📈 Run Performance")
        m_cols = st.columns(3)
        with m_cols[0]:
            render_metric_card("Total Tables", total_tables, "📋", "#4A9EFF")
        with m_cols[1]:
            render_metric_card("Pass Rate", f"{pass_rate:.1f}%", "🎯",
                               "#00D4AA" if pass_rate >= 90 else "#FFBE0B" if pass_rate >= 70 else "#FF4757")
        with m_cols[2]:
            render_metric_card("Duration", f"{duration:.1f}s", "⏱️", "#6C63FF")

        st.markdown("<br>", unsafe_allow_html=True)
        m_cols_2 = st.columns(3)
        with m_cols_2[0]:
            render_metric_card("Passed Tables", passed, "🟢", "#00D4AA")
        with m_cols_2[1]:
            render_metric_card("Warnings", warned, "🟡", "#FFBE0B")
        with m_cols_2[2]:
            render_metric_card("Failed Tables", failed, "🔴", "#FF4757")

    with col2:
        st.markdown("##### 🎯 Status Distribution")
        # Render a clean Plotly Donut Chart
        status_data = pd.DataFrame({
            "Status": ["Passed", "Warnings", "Failed"],
            "Count": [passed, warned, failed]
        })
        # Filter out 0 counts to prevent empty pie slices
        status_data = status_data[status_data["Count"] > 0]

        if not status_data.empty:
            fig = px.pie(
                status_data,
                values="Count",
                names="Status",
                color="Status",
                color_discrete_map={
                    "Passed": "#00D4AA",
                    "Warnings": "#FFBE0B",
                    "Failed": "#FF4757"
                },
                hole=0.6,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E8ECF1",
                margin=dict(t=0, b=0, l=0, r=0),
                height=210,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No tables to display in status distribution.")

    st.markdown("---")

    # ── Summary Table ─────────────────────────────────────────────────────
    st.markdown("### 📋 Table Validation Summaries")
    
    summary_df = report_gen.get_summary_dataframe()
    
    # Custom CSS-based grid styling for st.dataframe
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Validation status of the table",
                width="small",
            ),
            "Pass Rate": st.column_config.TextColumn(
                "Pass Rate",
                width="small",
            ),
            "Row Diff %": st.column_config.TextColumn(
                "Row Diff %",
                width="small",
            )
        }
    )

    # ── Drill-down analysis ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔍 Detailed Table Investigation")

    table_options = [s.table_name for s in summaries]
    selected_table = st.selectbox(
        "Select a table to drill down into its validation details:",
        options=table_options,
        key="selected_drill_table"
    )

    if selected_table:
        # Get TableValidation summary record
        table_summary = next((s for s in summaries if s.table_name == selected_table), None)
        
        if table_summary:
            st.markdown(f"#### Results for `{selected_table}`")
            
            # Show per-table stats cards
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                st.metric("Status", table_summary.status)
            with sc2:
                st.metric("Source Rows", f"{table_summary.row_count_source:,}")
            with sc3:
                st.metric("Target Rows", f"{table_summary.row_count_target:,}")
            with sc4:
                st.metric("Row Difference", f"{table_summary.row_count_source - table_summary.row_count_target:,} ({table_summary.row_count_diff_pct}%)")

            # Filter detailed results
            table_results = [r for r in results if r.table_name == selected_table]
            
            # Tabs for different verification areas
            tab_summary, tab_checks, tab_mismatches = st.tabs([
                "📋 Overview & Summary", 
                "✓ Individual Check Results", 
                "🚨 Failures & Warnings"
            ])

            with tab_summary:
                st.markdown(f"**Validations Run:** {', '.join(table_summary.validation_types_run)}")
                st.markdown(f"**Duration:** {table_summary.duration_seconds:.2f} seconds")
                st.markdown(f"**Sampled Rows:** {table_summary.sampled_rows:,}")
                st.markdown(f"**Details Log:**")
                st.code(table_summary.details)

            with tab_checks:
                if table_results:
                    checks_df = pd.DataFrame([{
                        "Type": r.validation_type,
                        "Status": r.status,
                        "Column": r.column_name if r.column_name else "Table-Level",
                        "Source Value": str(r.source_value),
                        "Target Value": str(r.target_value),
                        "Difference": str(r.difference) if r.difference is not None else "—",
                        "Details": r.details
                    } for r in table_results])
                    
                    st.dataframe(
                        checks_df,
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No individual check records found for this table.")

            with tab_mismatches:
                failures = [r for r in table_results if r.status in ["FAIL", "WARNING"]]
                if failures:
                    fail_df = pd.DataFrame([{
                        "Type": r.validation_type,
                        "Status": r.status,
                        "Column": r.column_name if r.column_name else "Table-Level",
                        "Source Value": str(r.source_value),
                        "Target Value": str(r.target_value),
                        "Difference": str(r.difference) if r.difference is not None else "—",
                        "Details": r.details
                    } for r in failures])
                    
                    st.dataframe(
                        fail_df,
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.success("🎉 No failures or warnings found for this table!")

    # ── Downloads Footer ──────────────────────────────────────────────────
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("### 📥 Download Reports")
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        try:
            zip_bytes = report_gen.generate_zip_bundle()
            st.download_button(
                label="📦 Download Full ZIP (Excel & Table CSVs)",
                data=zip_bytes,
                file_name=f"validation_report_{report_gen.timestamp}.zip",
                mime="application/zip",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Could not generate ZIP report: {e}")
            
    with col_d2:
        try:
            excel_bytes = report_gen._generate_excel_bytes()
            st.download_button(
                label="📊 Download Excel Summary (Multi-sheet)",
                data=excel_bytes,
                file_name=f"validation_summary_{report_gen.timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Could not generate Excel report: {e}")

    with col_d3:
        try:
            import os
            if os.path.exists("row_hash_validation.log"):
                with open("row_hash_validation.log", "r") as f:
                    log_content = f.read()
                st.download_button(
                    label="📜 Download Execution Log (.log)",
                    data=log_content,
                    file_name="row_hash_validation.log",
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                st.button("📜 Execution Log (Empty)", disabled=True, use_container_width=True)
        except Exception as e:
            st.error(f"Could not read log file: {e}")

