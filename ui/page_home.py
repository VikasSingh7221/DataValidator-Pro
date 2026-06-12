"""
Home / Landing page — Dashboard overview.
"""

import streamlit as st
from ui.components import render_hero, render_metric_card, render_section_header, render_empty_state


def render():
    render_hero(
        "DataValidator Pro",
        "A powerful, general-purpose data validation engine. "
        "Compare any two data sources — databases, CSV files, or custom queries — "
        "with row-hash matching, schema diffs, null analysis, and more."
    )

    # ── Quick Actions ─────────────────────────────────────────────────────
    render_section_header("Quick Start", "🚀")

    cols = st.columns(3)

    with cols[0]:
        st.markdown("""
        <div class="glass-card" style="text-align:center;min-height:180px">
            <div style="font-size:2.5rem;margin-bottom:10px">🔌</div>
            <div style="font-size:1.05rem;font-weight:700;color:var(--text-primary);margin-bottom:6px">
                Database Validation
            </div>
            <div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5">
                Connect to PostgreSQL, MySQL, Snowflake, Redshift, or SQLite and validate tables across sources.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown("""
        <div class="glass-card" style="text-align:center;min-height:180px">
            <div style="font-size:2.5rem;margin-bottom:10px">📄</div>
            <div style="font-size:1.05rem;font-weight:700;color:var(--text-primary);margin-bottom:6px">
                File Comparison
            </div>
            <div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5">
                Upload CSV or Excel files and compare data side-by-side with detailed diff reports.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown("""
        <div class="glass-card" style="text-align:center;min-height:180px">
            <div style="font-size:2.5rem;margin-bottom:10px">📊</div>
            <div style="font-size:1.05rem;font-weight:700;color:var(--text-primary);margin-bottom:6px">
                Custom SQL
            </div>
            <div style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5">
                Write custom queries for source and target, and validate the results with full hash comparison.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Session Stats ─────────────────────────────────────────────────────
    render_section_header("Session Overview", "📈")

    history = st.session_state.get("validation_history", [])

    if history:
        total_runs = len(history)
        total_tables = sum(r.get("total_tables", 0) for r in history)
        avg_pass = sum(r.get("pass_rate", 0) for r in history) / total_runs if total_runs > 0 else 0
        last_run = history[-1].get("timestamp", "—")

        cols = st.columns(4)
        with cols[0]:
            render_metric_card("Total Runs", total_runs, "🔄", "#6C63FF")
        with cols[1]:
            render_metric_card("Tables Validated", total_tables, "📋", "#4A9EFF")
        with cols[2]:
            render_metric_card("Avg Pass Rate", f"{avg_pass:.1f}%", "🎯", "#00D4AA")
        with cols[3]:
            render_metric_card("Last Run", last_run, "🕐", "#FF6B9D")
    else:
        render_empty_state(
            "🧪",
            "No validations yet",
            "Navigate to the Connections page to set up your data sources, "
            "then run your first validation."
        )

    # ── Supported Sources ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_header("Supported Data Sources", "🗄️")

    sources = [
        ("🐘", "PostgreSQL", "Full support via psycopg2"),
        ("❄️", "Snowflake", "Native connector with SSO/MFA"),
        ("🔴", "Redshift", "Via psycopg2 (PostgreSQL wire protocol)"),
        ("🐬", "MySQL", "Via mysql-connector-python"),
        ("💾", "SQLite", "Local file databases"),
        ("📄", "CSV / Excel", "Upload and compare files directly"),
    ]

    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(sources):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border-color);
                        border-radius:var(--radius-sm);padding:14px;margin-bottom:10px;
                        transition:all 0.2s ease">
                <span style="font-size:1.3rem">{icon}</span>
                <span style="font-weight:600;margin-left:8px;color:var(--text-primary)">{name}</span>
                <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Validation Types ──────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_header("Validation Types", "🧪")

    validations = [
        ("🔐", "Row Hash", "MD5 hash per-row comparison with configurable sample size"),
        ("#️⃣", "Row Count", "Exact or tolerance-based row count matching"),
        ("🏗️", "Schema Diff", "Column names, types, and nullable flags comparison"),
        ("🕳️", "Null Analysis", "Null percentage comparison per column with thresholds"),
        ("👯", "Duplicates", "Duplicate row detection by primary key"),
        ("📊", "Statistics", "Min, max, mean, distinct count per column"),
        ("✏️", "Custom SQL", "User-defined query pair comparison"),
    ]

    cols = st.columns(4)
    for i, (icon, name, desc) in enumerate(validations):
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border-color);
                        border-radius:var(--radius-sm);padding:14px;margin-bottom:10px;
                        min-height:100px;transition:all 0.2s ease">
                <div style="font-size:1.3rem;margin-bottom:6px">{icon}</div>
                <div style="font-weight:600;font-size:0.9rem;color:var(--text-primary)">{name}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:4px;line-height:1.4">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
