"""
History page — view and manage past validation runs,
re-examine detailed reports, and view historical trend charts.
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
from dataclasses import asdict
from core.models import TableValidation, ValidationResult, ValidationConfig
from core.reports import ReportGenerator
from ui.components import render_section_header, render_empty_state, render_metric_card

HISTORY_FILE = "config/validation_history.json"


def load_history_from_file():
    """Load history list from a local JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            
        # Reconstruct structured data where possible
        reconstructed = []
        for run in data:
            # Reconstruct summaries
            summaries = []
            for s in run.get("summaries", []):
                summaries.append(TableValidation(**s))
                
            # Reconstruct detailed results
            results = []
            for r in run.get("results", []):
                results.append(ValidationResult(**r))
                
            # Reconstruct ReportGenerator
            report_gen = ReportGenerator(
                table_summaries=summaries,
                detailed_results=results,
                source_label=run.get("src_label", "Source"),
                target_label=run.get("tgt_label", "Target"),
            )
            
            run_summary = {
                "timestamp": run.get("timestamp"),
                "total_tables": run.get("total_tables"),
                "passed": run.get("passed"),
                "failed": run.get("failed"),
                "warned": run.get("warned"),
                "pass_rate": run.get("pass_rate"),
                "duration": run.get("duration"),
                "summaries": summaries,
                "results": results,
                "report_gen": report_gen,
                "src_label": run.get("src_label"),
                "tgt_label": run.get("tgt_label"),
            }
            reconstructed.append(run_summary)
        return reconstructed
    except Exception as e:
        st.warning(f"Failed to load history from file: {e}")
        return []


def save_history_to_file(history):
    """Save history list to a local JSON file."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    try:
        serialized = []
        for run in history:
            serialized_run = {
                "timestamp": run["timestamp"],
                "total_tables": run["total_tables"],
                "passed": run["passed"],
                "failed": run["failed"],
                "warned": run["warned"],
                "pass_rate": run["pass_rate"],
                "duration": run["duration"],
                "src_label": run["src_label"],
                "tgt_label": run["tgt_label"],
                "summaries": [asdict(s) for s in run["summaries"]],
                "results": [asdict(r) for r in run["results"]],
            }
            serialized.append(serialized_run)
            
        with open(HISTORY_FILE, "w") as f:
            json.dump(serialized, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save history: {e}")


def render():
    render_section_header("Validation History", "📜")

    # Sync session state with history file
    if "validation_history" not in st.session_state:
        st.session_state["validation_history"] = load_history_from_file()

    history = st.session_state["validation_history"]

    if not history:
        render_empty_state(
            "📜",
            "No runs in history",
            "Your completed validations will be logged here automatically. Run a validation to get started!",
        )
        return

    # ── History Trends ────────────────────────────────────────────────────
    st.markdown("### 📈 Quality Trends")
    
    # Create DataFrame for trend plotting
    trend_data = []
    for idx, run in enumerate(history):
        trend_data.append({
            "Run Index": idx + 1,
            "Timestamp": run["timestamp"],
            "Pass Rate (%)": run["pass_rate"],
            "Tables": run["total_tables"],
        })
    df_trend = pd.DataFrame(trend_data)

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Pass Rate Trend over Time**")
        fig_line = px.line(
            df_trend, 
            x="Timestamp", 
            y="Pass Rate (%)", 
            markers=True,
            color_discrete_sequence=["#00D4AA"]
        )
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E8ECF1",
            margin=dict(t=10, b=10, l=10, r=10),
            height=200,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(108, 99, 255, 0.1)", range=[0, 105]),
        )
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
        
    with col2:
        st.markdown("**Validated Tables count per Run**")
        fig_bar = px.bar(
            df_trend, 
            x="Timestamp", 
            y="Tables",
            color_discrete_sequence=["#6C63FF"]
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E8ECF1",
            margin=dict(t=10, b=10, l=10, r=10),
            height=200,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(108, 99, 255, 0.1)"),
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Past Runs list")

    # ── History Table list ────────────────────────────────────────────────
    for i, run in enumerate(reversed(history)):
        # Calculate real index in list since we reversed the display order
        real_idx = len(history) - 1 - i
        
        status_color = "#00D4AA" if run["pass_rate"] >= 90 else "#FFBE0B" if run["pass_rate"] >= 70 else "#FF4757"
        
        with st.container(border=True):
            cols = st.columns([2, 3, 2, 2])
            
            with cols[0]:
                st.markdown(f"**🕒 {run['timestamp']}**")
                st.markdown(f'<span style="color:var(--text-secondary);font-size:0.8rem">Run ID: #{real_idx + 1}</span>', unsafe_allow_html=True)
                
            with cols[1]:
                st.markdown(f"**Sources:**")
                st.markdown(f"`{run['src_label']}` ↔ `{run['tgt_label']}`")
                
            with cols[2]:
                st.markdown(f"**Stats:**")
                st.markdown(f"Tables: **{run['total_tables']}** | Duration: **{run['duration']}s**")
                
            with cols[3]:
                st.markdown(f'<div style="text-align:right">Pass Rate: <strong style="color:{status_color};font-size:1.15rem">{run["pass_rate"]:.1f}%</strong></div>', unsafe_allow_html=True)
                
                # Buttons row
                btn_cols = st.columns(2)
                with btn_cols[0]:
                    if st.button("🔍 Load", key=f"load_{real_idx}", use_container_width=True):
                        st.session_state["last_validation"] = run
                        st.success(f"Loaded run from {run['timestamp']} to Results!")
                        st.balloons()
                with btn_cols[1]:
                    if st.button("🗑️ Delete", key=f"del_{real_idx}", use_container_width=True):
                        # Delete from history
                        history.pop(real_idx)
                        st.session_state["validation_history"] = history
                        save_history_to_file(history)
                        st.rerun()

    # Clear all history
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧹 Clear All Validation History", type="secondary", use_container_width=True):
        st.session_state["validation_history"] = []
        save_history_to_file([])
        st.rerun()
