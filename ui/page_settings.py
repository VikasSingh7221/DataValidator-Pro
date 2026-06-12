"""
Settings page — configure default tolerance thresholds, value normalization rules,
and export preferences.
"""

import streamlit as st
import json
import os
from ui.components import render_section_header, render_glass_card

SETTINGS_FILE = "config/settings.json"


def load_settings():
    """Load settings from local JSON file or default value."""
    defaults = {
        "sample_size": 100,
        "row_tolerance": 0.0,
        "null_threshold": 5.0,
        "case_sensitive": False,
        "normalize_whitespace": True,
        "numeric_precision": 6,
        "show_interactive_plots": True,
        "theme": "Dark",
    }
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    try:
        with open(SETTINGS_FILE, "r") as f:
            user_settings = json.load(f)
            # Merge defaults to ensure all keys exist
            defaults.update(user_settings)
            return defaults
    except Exception:
        return defaults


def save_settings(settings):
    """Save settings to local JSON file."""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False


def render():
    render_section_header("Application Settings", "⚙️")

    # Load settings into session state if not initialized
    if "app_settings" not in st.session_state:
        st.session_state["app_settings"] = load_settings()

    settings = st.session_state["app_settings"]

    st.markdown(
        '<div style="color:var(--text-secondary);margin-bottom:24px">'
        "Adjust defaults and normalizer behaviors. Settings are saved locally and "
        "apply to all new validation runs."
        "</div>",
        unsafe_allow_html=True,
    )

    # Forms container
    with st.form("settings_form", border=True):
        st.markdown("#### 🚀 Validation Run Defaults")
        col1, col2, col3 = st.columns(3)
        with col1:
            sample_size = st.number_input(
                "Default Sample Size",
                min_value=5, max_value=10000, value=settings["sample_size"], step=5,
                help="Number of rows to sample and validate using row-hashing per table"
            )
        with col2:
            row_tolerance = st.number_input(
                "Row Count Tolerance (%)",
                min_value=0.0, max_value=100.0, value=settings["row_tolerance"], step=0.1,
                help="Acceptable percentage difference between source and target table row counts"
            )
        with col3:
            null_threshold = st.number_input(
                "Null Diff Threshold (%)",
                min_value=0.0, max_value=100.0, value=settings["null_threshold"], step=0.5,
                help="Acceptable difference percentage of null values in target vs source"
            )

        st.markdown("---")

        st.markdown("#### 🔠 Value Normalization Rules")
        col_norm1, col_norm2 = st.columns(2)
        with col_norm1:
            case_sensitive = st.checkbox(
                "Case-Sensitive String Comparison",
                value=settings["case_sensitive"],
                help="If enabled, 'Value' and 'value' will count as mismatches during hashing"
            )
            normalize_whitespace = st.checkbox(
                "Normalize Whitespace & Strip Strings",
                value=settings["normalize_whitespace"],
                help="Removes leading/trailing spaces and converts double spaces to single spaces"
            )
        with col_norm2:
            numeric_precision = st.slider(
                "Decimal Precision for Floats",
                min_value=0, max_value=12, value=settings["numeric_precision"],
                help="Rounds floating-point numbers to this precision before comparison"
            )

        st.markdown("---")

        st.markdown("#### 🖥️ UI & Interface Preferences")
        col_ui1, col_ui2 = st.columns(2)
        with col_ui1:
            show_interactive_plots = st.checkbox(
                "Show Interactive Charts (Plotly)",
                value=settings["show_interactive_plots"],
                help="Display Plotly charts in results dashboard"
            )
        with col_ui2:
            theme = st.selectbox(
                "Preferred Theme Style",
                options=["Dark", "Light (System Default)"],
                index=0 if settings["theme"] == "Dark" else 1
            )

        # Submit button
        submit = st.form_submit_button("💾 Save Settings", use_container_width=True)

        if submit:
            updated = {
                "sample_size": sample_size,
                "row_tolerance": row_tolerance,
                "null_threshold": null_threshold,
                "case_sensitive": case_sensitive,
                "normalize_whitespace": normalize_whitespace,
                "numeric_precision": numeric_precision,
                "show_interactive_plots": show_interactive_plots,
                "theme": theme,
            }
            st.session_state["app_settings"] = updated
            if save_settings(updated):
                st.success("✅ Settings saved successfully! These defaults will be loaded on next runs.")
            else:
                st.error("❌ Failed to save settings to disk.")


