"""
DataValidator Pro — Streamlit entry point.
Routes to different pages and manages global layout/styling.
"""

import streamlit as st

# MUST be the first streamlit call
st.set_page_config(
    page_title="DataValidator Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

import logging

# Set up logging to a local log file, ensuring we don't duplicate handlers during hot-reloads
root_logger = logging.getLogger()
if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
    file_handler = logging.FileHandler("row_hash_validation.log")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)

from ui.styles import inject_css
from ui.components import render_connection_status
import ui.page_home as page_home
import ui.page_connections as page_connections
import ui.page_validate as page_validate
import ui.page_results as page_results
import ui.page_history as page_history
import ui.page_settings as page_settings


def main():
    # Inject premium styles
    inject_css()

    # Sidebar Header
    st.sidebar.markdown(
        '<div style="text-align:center;padding:10px 0 20px 0">'
        '<span style="font-size:1.8rem;font-weight:800;background:var(--gradient-1);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        'background-clip:text">DataValidator Pro</span>'
        '<div style="font-size:0.75rem;color:var(--text-secondary);margin-top:4px">'
        "Enterprise Data Quality Suite"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Sidebar Navigation
    pages = {
        "🏠  Home / Overview": page_home,
        "🔌  Data Connections": page_connections,
        "🚀  Run Validation": page_validate,
        "📊  Results Dashboard": page_results,
        "📜  Validation History": page_history,
        "⚙️  Settings": page_settings,
    }

    selected_page_name = st.sidebar.radio(
        "Navigation",
        options=list(pages.keys()),
        label_visibility="collapsed",
    )

    # Render Active Page
    st.sidebar.markdown("<br><hr>", unsafe_allow_html=True)
    st.sidebar.markdown('<div class="metric-label" style="margin-bottom:12px">Connection Status</div>', unsafe_allow_html=True)

    # Connection Indicators in Sidebar
    src_profile = st.session_state.get("source_profile")
    tgt_profile = st.session_state.get("target_profile")

    if src_profile and src_profile.is_connected:
        st.sidebar.markdown(
            f'<div style="font-size:0.8rem;color:var(--pass-color);display:flex;align-items:center;gap:6px">'
            f"🟢 Source: {src_profile.source_type.value}"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            '<div style="font-size:0.8rem;color:var(--text-muted);display:flex;align-items:center;gap:6px">'
            "🔴 Source: Disconnected"
            "</div>",
            unsafe_allow_html=True
        )

    if tgt_profile and tgt_profile.is_connected:
        st.sidebar.markdown(
            f'<div style="font-size:0.8rem;color:var(--pass-color);display:flex;align-items:center;gap:6px;margin-top:6px">'
            f"🟢 Target: {tgt_profile.source_type.value}"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            '<div style="font-size:0.8rem;color:var(--text-muted);display:flex;align-items:center;gap:6px;margin-top:6px">'
            "🔴 Target: Disconnected"
            "</div>",
            unsafe_allow_html=True
        )

    # Info banner at bottom of sidebar
    st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div style="text-align:center;font-size:0.75rem;color:var(--text-muted)">'
        "v1.0.0 | Developed by Vikas Singh"
        "</div>",
        unsafe_allow_html=True
    )

    # Route to selected page
    active_page = pages[selected_page_name]
    active_page.render()


if __name__ == "__main__":
    main()
