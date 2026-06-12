"""
Connections page — Configure Source & Target data sources.
"""

import streamlit as st
import pandas as pd
import os
from core.models import DataSourceType, ConnectionProfile
from core.connections import create_connection, CSVDataSource
from ui.components import render_section_header, render_connection_status


DB_TYPE_OPTIONS = [
    DataSourceType.POSTGRESQL,
    DataSourceType.MYSQL,
    DataSourceType.SNOWFLAKE,
    DataSourceType.REDSHIFT,
    DataSourceType.SQLITE,
    DataSourceType.CSV_FILE,
]

DB_ICONS = {
    DataSourceType.POSTGRESQL: "🐘",
    DataSourceType.MYSQL: "🐬",
    DataSourceType.SNOWFLAKE: "❄️",
    DataSourceType.REDSHIFT: "🔴",
    DataSourceType.SQLITE: "💾",
    DataSourceType.CSV_FILE: "📄",
}

DEFAULT_PORTS = {
    DataSourceType.POSTGRESQL: 5432,
    DataSourceType.MYSQL: 3306,
    DataSourceType.REDSHIFT: 5439,
    DataSourceType.SNOWFLAKE: 443,
    DataSourceType.SQLITE: 0,
    DataSourceType.CSV_FILE: 0,
}


def _render_connection_form(key_prefix: str, label: str) -> ConnectionProfile:
    """Render a dynamic connection form based on selected DB type."""
    st.markdown(f"#### {label}")

    db_type = st.selectbox(
        "Database Type",
        options=DB_TYPE_OPTIONS,
        format_func=lambda x: f"{DB_ICONS[x]}  {x.value}",
        key=f"{key_prefix}_db_type",
    )

    profile = ConnectionProfile(
        name=f"{label}",
        source_type=db_type,
    )

    if db_type == DataSourceType.CSV_FILE:
        uploaded = st.file_uploader(
            "Upload CSV / Excel file",
            type=["csv", "tsv", "xlsx", "xls"],
            key=f"{key_prefix}_file",
        )
        if uploaded:
            profile.file_path = uploaded.name
            # Store the uploaded file object in session state
            st.session_state[f"{key_prefix}_uploaded_file"] = uploaded
            st.session_state[f"{key_prefix}_uploaded_name"] = uploaded.name

    elif db_type == DataSourceType.SNOWFLAKE:
        col1, col2 = st.columns(2)
        with col1:
            profile.account = st.text_input("Account", key=f"{key_prefix}_account",
                                            placeholder="org-account")
            profile.user = st.text_input("User", key=f"{key_prefix}_user")
            profile.warehouse = st.text_input("Warehouse", key=f"{key_prefix}_warehouse")
        with col2:
            profile.database = st.text_input("Database", key=f"{key_prefix}_database")
            profile.schema = st.text_input("Schema", value="PUBLIC", key=f"{key_prefix}_schema")
            profile.role = st.text_input("Role (optional)", key=f"{key_prefix}_role")

        auth_mode = st.radio(
            "Authentication",
            ["Password", "SSO (External Browser)", "MFA"],
            key=f"{key_prefix}_auth",
            horizontal=True,
        )
        if auth_mode == "Password":
            profile.password = st.text_input("Password", type="password", key=f"{key_prefix}_pass")
        elif auth_mode == "SSO (External Browser)":
            profile.use_sso = True
        else:
            profile.password = st.text_input("Password", type="password", key=f"{key_prefix}_pass")
            profile.use_mfa = True

    elif db_type == DataSourceType.SQLITE:
        profile.database = st.text_input(
            "Database file path",
            key=f"{key_prefix}_db_path",
            placeholder="/path/to/database.db",
        )
        profile.schema = "main"

    else:
        # PostgreSQL, MySQL, Redshift
        col1, col2 = st.columns(2)
        with col1:
            profile.host = st.text_input("Host", key=f"{key_prefix}_host",
                                         placeholder="localhost")
            profile.port = st.number_input(
                "Port", value=DEFAULT_PORTS.get(db_type, 5432),
                key=f"{key_prefix}_port",
            )
            profile.database = st.text_input("Database", key=f"{key_prefix}_database")
        with col2:
            profile.schema = st.text_input("Schema", value="public", key=f"{key_prefix}_schema")
            profile.user = st.text_input("User", key=f"{key_prefix}_user")
            profile.password = st.text_input("Password", type="password", key=f"{key_prefix}_pass")

    return profile


def _test_connection(profile: ConnectionProfile, key_prefix: str):
    """Test a connection and display result."""
    try:
        if profile.source_type == DataSourceType.CSV_FILE:
            uploaded = st.session_state.get(f"{key_prefix}_uploaded_file")
            if uploaded is None:
                st.error("Please upload a file first")
                return False

            conn = CSVDataSource(profile)
            # Read the uploaded file into a DataFrame
            uploaded.seek(0)
            if uploaded.name.endswith((".csv", ".tsv")):
                sep = "\t" if uploaded.name.endswith(".tsv") else ","
                df = pd.read_csv(uploaded, sep=sep)
            else:
                df = pd.read_excel(uploaded)

            name = os.path.splitext(uploaded.name)[0]
            conn.load_dataframe(name, df)
            conn.profile.is_connected = True
            conn.profile.latency_ms = 0

            st.session_state[f"{key_prefix}_connection"] = conn
            st.session_state[f"{key_prefix}_profile"] = profile
            st.success(f"✅ Loaded {len(df):,} rows × {len(df.columns)} columns from `{uploaded.name}`")
            return True
        else:
            conn = create_connection(profile)
            result = conn.test_connection()

            if result["success"]:
                st.session_state[f"{key_prefix}_connection"] = conn
                st.session_state[f"{key_prefix}_profile"] = profile
                st.success(f"✅ Connected! Latency: {result['latency_ms']:.0f}ms")
                return True
            else:
                st.error(f"❌ Connection failed: {result['error']}")
                return False

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False


def render():
    render_section_header("Data Source Connections", "🔌")
    st.markdown(
        '<div style="color:var(--text-secondary);margin-bottom:24px">'
        "Configure your source and target data sources. "
        "Connect to databases or upload files for comparison."
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Connection Status Overview ────────────────────────────────────────
    col_s, col_t = st.columns(2)
    with col_s:
        src_profile = st.session_state.get("source_profile")
        if src_profile and src_profile.is_connected:
            render_connection_status(
                f"Source: {src_profile.display_label()}",
                True, src_profile.latency_ms,
            )
        else:
            render_connection_status("Source", False)

    with col_t:
        tgt_profile = st.session_state.get("target_profile")
        if tgt_profile and tgt_profile.is_connected:
            render_connection_status(
                f"Target: {tgt_profile.display_label()}",
                True, tgt_profile.latency_ms,
            )
        else:
            render_connection_status("Target", False)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Connection Forms ──────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            src_profile = _render_connection_form("source", "⬅️ Source")
            if st.button("🔗 Test Source Connection", key="test_source", use_container_width=True):
                _test_connection(src_profile, "source")

    with col2:
        with st.container(border=True):
            tgt_profile = _render_connection_form("target", "➡️ Target")
            if st.button("🔗 Test Target Connection", key="test_target", use_container_width=True):
                _test_connection(tgt_profile, "target")

    # ── Shortcut: Both CSVs ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("💡 Quick Compare: Upload Two CSV Files", expanded=False):
        st.markdown("Upload a source and target CSV to instantly compare them without configuring connections.")
        qc1, qc2 = st.columns(2)
        with qc1:
            qf_src = st.file_uploader("Source CSV", type=["csv", "xlsx"], key="quick_src")
        with qc2:
            qf_tgt = st.file_uploader("Target CSV", type=["csv", "xlsx"], key="quick_tgt")

        if qf_src and qf_tgt:
            if st.button("⚡ Load Both Files", key="quick_load", use_container_width=True):
                try:
                    # Source
                    qf_src.seek(0)
                    src_df = pd.read_csv(qf_src) if qf_src.name.endswith(".csv") else pd.read_excel(qf_src)
                    src_p = ConnectionProfile(name="Source File", source_type=DataSourceType.CSV_FILE,
                                              file_path=qf_src.name)
                    src_conn = CSVDataSource(src_p)
                    src_conn.load_dataframe(os.path.splitext(qf_src.name)[0], src_df)
                    src_p.is_connected = True

                    # Target
                    qf_tgt.seek(0)
                    tgt_df = pd.read_csv(qf_tgt) if qf_tgt.name.endswith(".csv") else pd.read_excel(qf_tgt)
                    tgt_p = ConnectionProfile(name="Target File", source_type=DataSourceType.CSV_FILE,
                                              file_path=qf_tgt.name)
                    tgt_conn = CSVDataSource(tgt_p)
                    tgt_conn.load_dataframe(os.path.splitext(qf_tgt.name)[0], tgt_df)
                    tgt_p.is_connected = True

                    st.session_state["source_connection"] = src_conn
                    st.session_state["source_profile"] = src_p
                    st.session_state["target_connection"] = tgt_conn
                    st.session_state["target_profile"] = tgt_p

                    st.success(
                        f"✅ Loaded Source: {len(src_df):,} rows | "
                        f"Target: {len(tgt_df):,} rows — Go to **Validate** to run!"
                    )
                except Exception as e:
                    st.error(f"Error loading files: {e}")

    # ── Demo Sandbox Mode ──────────────────────────────────────────────────
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("### 🧪 Demo / Sandbox Mode")
    st.markdown(
        '<div style="color:var(--text-secondary);margin-bottom:12px">'
        "Don't have active database credentials? Click below to instantly generate "
        "and auto-load two local SQLite databases configured with tables, schema, "
        "and deliberate data mismatches for testing the complete validation flow."
        "</div>",
        unsafe_allow_html=True
    )
    if st.button("⚡ Generate & Load Demo SQLite Databases", use_container_width=True):
        try:
            _generate_demo_databases()
            
            # Setup session state profiles & connections
            from core.connections import SQLiteConnection
            
            src_p = ConnectionProfile(
                name="Demo Source (SQLite)",
                source_type=DataSourceType.SQLITE,
                database="demo_source.db",
                schema="main",
            )
            src_conn = SQLiteConnection(src_p)
            src_conn.connect()
            
            tgt_p = ConnectionProfile(
                name="Demo Target (SQLite)",
                source_type=DataSourceType.SQLITE,
                database="demo_target.db",
                schema="main",
            )
            tgt_conn = SQLiteConnection(tgt_p)
            tgt_conn.connect()
            
            st.session_state["source_connection"] = src_conn
            st.session_state["source_profile"] = src_p
            st.session_state["target_connection"] = tgt_conn
            st.session_state["target_profile"] = tgt_p
            
            st.success(
                "🎉 Demo databases successfully generated and loaded!\n\n"
                "1. Local DB files created: `demo_source.db` & `demo_target.db`.\n\n"
                "2. Dynamic PK mapping created: `tables/demo_aggregation.json`.\n\n"
                "3. Connections loaded in session state. Go to the **Run Validation** page, select the **Filter by configured table group** option, choose group **demo**, and hit start!"
            )
            st.balloons()
        except Exception as e:
            st.error(f"Error setting up demo sandbox: {e}")


def _generate_demo_databases():
    """Generate two demo SQLite databases with deliberate mismatches and auto-configure them."""
    import sqlite3
    import json
    
    src_db = "demo_source.db"
    tgt_db = "demo_target.db"
    
    # ── 1. Setup Source Database ──────────────────────────────────────────
    conn_src = sqlite3.connect(src_db)
    cursor_src = conn_src.cursor()
    
    cursor_src.execute("DROP TABLE IF EXISTS users")
    cursor_src.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            age INTEGER,
            salary REAL
        )
    """)
    users_data = [
        (1, 'Vikas Singh', 'vikas@example.com', 29, 50000.0),
        (2, 'Alice Smith', 'alice@example.com', 25, 62000.0),
        (3, 'Bob Johnson', 'bob@example.com', 35, 75000.0),
        (4, 'Charlie Brown', 'charlie@example.com', 42, 80000.0),
        (5, 'Diana Prince', 'diana@example.com', 31, 95000.0)
    ]
    cursor_src.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", users_data)
    
    cursor_src.execute("DROP TABLE IF EXISTS orders")
    cursor_src.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            status TEXT
        )
    """)
    orders_data = [
        (101, 1, 250.50, 'COMPLETED'),
        (102, 2, 99.99, 'PENDING'),
        (103, 3, 1500.00, 'COMPLETED'),
        (104, 4, 45.00, 'FAILED'),
        (105, 5, 300.00, 'COMPLETED')
    ]
    cursor_src.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders_data)
    
    conn_src.commit()
    conn_src.close()
    
    # ── 2. Setup Target Database (with deliberate differences) ──────────────
    conn_tgt = sqlite3.connect(tgt_db)
    cursor_tgt = conn_tgt.cursor()
    
    cursor_tgt.execute("DROP TABLE IF EXISTS users")
    cursor_tgt.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            age INTEGER,
            salary REAL
        )
    """)
    users_tgt_data = [
        (1, 'Vikas Singh', 'vikas@example.com', 29, 50000.0),
        (2, 'Alice Smith', 'alice@example.com', 25, 62000.0),
        (3, 'Bob Johnson', 'bob@example.com', 35, 75000.0),
        (4, 'Charlie Brown', 'charlie@example.com', 42, 80000.0),
        (5, 'Diana Prince', 'diana@example.org', 31, 95000.0)  # Email difference (.org vs .com)
    ]
    cursor_tgt.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", users_tgt_data)
    
    cursor_tgt.execute("DROP TABLE IF EXISTS orders")
    cursor_tgt.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            status TEXT
        )
    """)
    orders_tgt_data = [
        (101, 1, 250.50, 'COMPLETED'),
        (102, 2, 99.99, 'PENDING'),
        (103, 3, 1500.00, 'COMPLETED'),
        (104, 4, 45.00, 'COMPLETED'),  # Status mismatch ('COMPLETED' vs 'FAILED')
        (105, 5, 300.00, 'COMPLETED'),
        (106, 1, 120.00, 'COMPLETED')   # Extra row (Row count mismatch)
    ]
    cursor_tgt.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders_tgt_data)
    
    conn_tgt.commit()
    conn_tgt.close()
    
    # ── 3. Write demo_aggregation.json for PK syncing ─────────────────────────
    os.makedirs("tables", exist_ok=True)
    demo_pk_mapping = {
        "users": "id",
        "orders": "order_id"
    }
    with open("tables/demo_aggregation.json", "w") as f:
        json.dump(demo_pk_mapping, f, indent=2)

