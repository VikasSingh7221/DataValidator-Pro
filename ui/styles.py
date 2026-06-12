"""
Premium dark-themed CSS for the Data Validation Tool Streamlit app.
"""


def get_custom_css() -> str:
    return """
    <style>
    /* ── Google Fonts ───────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Root Variables ────────────────────────────────────────── */
    :root {
        --bg-primary: #0E1117;
        --bg-secondary: #1B2838;
        --bg-card: #1E2A3A;
        --bg-hover: #243447;
        --text-primary: #E8ECF1;
        --text-secondary: #8B95A5;
        --text-muted: #5A6577;
        --accent-purple: #6C63FF;
        --accent-teal: #00D4AA;
        --accent-blue: #4A9EFF;
        --accent-pink: #FF6B9D;
        --gradient-1: linear-gradient(135deg, #6C63FF 0%, #00D4AA 100%);
        --gradient-2: linear-gradient(135deg, #FF6B9D 0%, #6C63FF 100%);
        --gradient-3: linear-gradient(135deg, #4A9EFF 0%, #6C63FF 100%);
        --pass-color: #00D4AA;
        --fail-color: #FF4757;
        --warn-color: #FFBE0B;
        --border-color: rgba(108, 99, 255, 0.15);
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
        --radius: 12px;
        --radius-sm: 8px;
        --radius-lg: 16px;
    }

    /* ── Global ────────────────────────────────────────────────── */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Hide Streamlit default chrome */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── Sidebar ───────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1520 0%, #152238 100%) !important;
        border-right: 1px solid var(--border-color);
    }

    [data-testid="stSidebar"] .stRadio label {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500;
        font-size: 0.95rem;
        padding: 8px 12px;
        border-radius: var(--radius-sm);
        transition: all 0.2s ease;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background: var(--bg-hover);
    }

    /* ── Metric Cards ──────────────────────────────────────────── */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius);
        padding: 20px 24px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }

    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-md);
        border-color: var(--accent-purple);
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin: 4px 0;
        font-family: 'JetBrains Mono', monospace;
    }

    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-secondary);
    }

    .metric-delta {
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 4px;
    }

    /* ── Status Badges ─────────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .badge-pass {
        background: rgba(0, 212, 170, 0.15);
        color: var(--pass-color);
        border: 1px solid rgba(0, 212, 170, 0.3);
    }

    .badge-fail {
        background: rgba(255, 71, 87, 0.15);
        color: var(--fail-color);
        border: 1px solid rgba(255, 71, 87, 0.3);
    }

    .badge-warning {
        background: rgba(255, 190, 11, 0.15);
        color: var(--warn-color);
        border: 1px solid rgba(255, 190, 11, 0.3);
    }

    /* ── Glass Cards ───────────────────────────────────────────── */
    .glass-card {
        background: rgba(30, 42, 58, 0.6);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 28px;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        border-color: rgba(108, 99, 255, 0.3);
        box-shadow: var(--shadow-lg);
    }

    /* ── Section Headers ───────────────────────────────────────── */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 24px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--accent-purple);
        display: inline-block;
    }

    /* ── Hero Section ──────────────────────────────────────────── */
    .hero-container {
        text-align: center;
        padding: 40px 20px 30px 20px;
        margin-bottom: 30px;
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6C63FF, #00D4AA, #4A9EFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 8px;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        font-size: 1.1rem;
        color: var(--text-secondary);
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* ── Progress ──────────────────────────────────────────────── */
    .progress-container {
        background: var(--bg-card);
        border-radius: var(--radius);
        padding: 20px;
        border: 1px solid var(--border-color);
        margin: 12px 0;
    }

    .progress-table-item {
        display: flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: var(--radius-sm);
        margin: 4px 0;
        font-size: 0.88rem;
        font-family: 'JetBrains Mono', monospace;
        transition: background 0.2s ease;
    }

    .progress-table-item:hover {
        background: var(--bg-hover);
    }

    /* ── Buttons ───────────────────────────────────────────────── */
    .stButton > button {
        background: var(--gradient-1) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(108, 99, 255, 0.5) !important;
    }

    /* ── Download Button ───────────────────────────────────────── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #00D4AA, #00B894) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(0, 212, 170, 0.3) !important;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 212, 170, 0.5) !important;
    }

    /* ── Data Tables ───────────────────────────────────────────── */
    .stDataFrame {
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius) !important;
    }

    /* ── Tabs ──────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--bg-secondary);
        padding: 4px;
        border-radius: var(--radius);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }

    /* ── Expander ──────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        background: var(--bg-card) !important;
        border-radius: var(--radius-sm) !important;
    }

    /* ── Scrollbar ─────────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--text-muted);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }

    /* ── Animations ────────────────────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    .animate-in {
        animation: fadeInUp 0.5s ease-out forwards;
    }

    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }

    /* ── Connection Card ───────────────────────────────────────── */
    .conn-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius);
        padding: 20px;
        transition: all 0.3s ease;
    }

    .conn-card.connected {
        border-color: var(--pass-color);
        box-shadow: 0 0 20px rgba(0, 212, 170, 0.1);
    }

    .conn-card.disconnected {
        border-color: var(--text-muted);
    }

    /* ── Toast / Log Messages ──────────────────────────────────── */
    .log-entry {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        padding: 4px 8px;
        color: var(--text-secondary);
        border-left: 3px solid var(--accent-purple);
        margin: 2px 0;
    }
    </style>
    """


def inject_css():
    """Inject custom CSS into the Streamlit app."""
    import streamlit as st
    st.markdown(get_custom_css(), unsafe_allow_html=True)
