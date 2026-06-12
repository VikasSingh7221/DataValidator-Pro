"""
Reusable Streamlit UI components — metric cards, badges, and styled elements.
"""

import streamlit as st


def render_metric_card(label: str, value, icon: str = "", color: str = "#6C63FF", delta: str = ""):
    """Render an animated metric card with icon and optional delta."""
    delta_html = ""
    if delta:
        delta_color = "#00D4AA" if "+" not in delta and "↓" not in delta else "#FF4757"
        delta_html = f'<div class="metric-delta" style="color:{delta_color}">{delta}</div>'

    st.markdown(f"""
    <div class="metric-card animate-in">
        <div style="font-size:1.6rem;margin-bottom:4px">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Return HTML for a status badge pill."""
    css_class = {
        "PASS": "badge-pass",
        "FAIL": "badge-fail",
        "WARNING": "badge-warning",
    }.get(status.upper(), "badge-warning")

    icon = {"PASS": "✓", "FAIL": "✗", "WARNING": "⚠"}.get(status.upper(), "?")

    return f'<span class="badge {css_class}">{icon} {status}</span>'


def render_status_badge_st(status: str):
    """Render a status badge directly in Streamlit."""
    st.markdown(render_status_badge(status), unsafe_allow_html=True)


def render_section_header(title: str, icon: str = ""):
    """Render a styled section header."""
    st.markdown(
        f'<div class="section-header">{icon} {title}</div>',
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str):
    """Render the hero / landing section."""
    st.markdown(f"""
    <div class="hero-container animate-in">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def render_glass_card(content_html: str):
    """Render content inside a glass-morphism card."""
    st.markdown(
        f'<div class="glass-card animate-in">{content_html}</div>',
        unsafe_allow_html=True,
    )


def render_connection_status(name: str, is_connected: bool, latency_ms: float = 0):
    """Render a connection status indicator."""
    if is_connected:
        status_dot = "🟢"
        status_text = f"Connected ({latency_ms:.0f}ms)"
        card_class = "connected"
    else:
        status_dot = "🔴"
        status_text = "Disconnected"
        card_class = "disconnected"

    st.markdown(f"""
    <div class="conn-card {card_class}">
        <div style="display:flex;align-items:center;gap:10px">
            <span style="font-size:1.2rem">{status_dot}</span>
            <div>
                <div style="font-weight:600;color:var(--text-primary)">{name}</div>
                <div style="font-size:0.82rem;color:var(--text-secondary)">{status_text}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_progress_log(messages: list):
    """Render a list of log messages with styling."""
    html = ""
    for msg in messages[-20:]:  # Show last 20 messages
        html += f'<div class="log-entry">{msg}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(icon: str, title: str, description: str):
    """Render a centered empty state with icon."""
    st.markdown(f"""
    <div style="text-align:center;padding:60px 20px;color:var(--text-muted)">
        <div style="font-size:3rem;margin-bottom:12px">{icon}</div>
        <div style="font-size:1.2rem;font-weight:600;color:var(--text-secondary);margin-bottom:8px">{title}</div>
        <div style="font-size:0.9rem;max-width:400px;margin:0 auto;line-height:1.6">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def render_stat_row(items: list):
    """Render a row of stat cards. items = [(label, value, icon, color), ...]"""
    cols = st.columns(len(items))
    for col, (label, value, icon, color) in zip(cols, items):
        with col:
            render_metric_card(label, value, icon, color)
