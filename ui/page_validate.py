"""
Validate page — Configure and run validations with live progress tracking.
"""

import streamlit as st
import time
from core.models import ValidationType, ValidationConfig
from core.validators import DataValidator
from core.reports import ReportGenerator
from ui.components import render_section_header, render_empty_state, render_metric_card
from ui.page_settings import load_settings


def render():
    # Load settings
    if "app_settings" not in st.session_state:
        st.session_state["app_settings"] = load_settings()
    settings = st.session_state["app_settings"]

    render_section_header("Run Validation", "🚀")

    # ── Check connections ─────────────────────────────────────────────────
    src_conn = st.session_state.get("source_connection")
    tgt_conn = st.session_state.get("target_connection")

    if not src_conn or not tgt_conn:
        render_empty_state(
            "🔌",
            "Connections required",
            "Please configure and test both Source and Target connections on the Connections page first.",
        )
        return

    src_profile = st.session_state.get("source_profile")
    tgt_profile = st.session_state.get("target_profile")

    # Show connected sources
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="conn-card connected">
            <div style="font-weight:600;color:var(--pass-color)">⬅️ Source</div>
            <div style="font-size:0.85rem;color:var(--text-secondary)">{src_profile.display_label() if src_profile else 'Connected'}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="conn-card connected">
            <div style="font-weight:600;color:var(--pass-color)">➡️ Target</div>
            <div style="font-size:0.85rem;color:var(--text-secondary)">{tgt_profile.display_label() if tgt_profile else 'Connected'}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Configuration Panel ───────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### ⚙️ Validation Configuration")

        # Validation types
        st.markdown("**Select Validation Types:**")
        val_cols = st.columns(4)

        type_selections = {}
        type_map = [
            (ValidationType.ROW_HASH, "🔐 Row Hash", True),
            (ValidationType.ROW_COUNT, "#️⃣ Row Count", True),
            (ValidationType.SCHEMA, "🏗️ Schema Diff", False),
            (ValidationType.NULL_ANALYSIS, "🕳️ Null Analysis", False),
            (ValidationType.DUPLICATE_DETECTION, "👯 Duplicates", False),
            (ValidationType.STATISTICAL_PROFILE, "📊 Statistics", False),
        ]

        for i, (vtype, label, default) in enumerate(type_map):
            with val_cols[i % 4]:
                type_selections[vtype] = st.checkbox(label, value=default, key=f"vt_{vtype.name}")

        selected_types = [vt for vt, sel in type_selections.items() if sel]

        st.markdown("---")

        # Parameters
        param_cols = st.columns(3)
        with param_cols[0]:
            sample_size = st.slider(
                "Sample Size (rows per table)",
                min_value=10, max_value=max(1000, settings["sample_size"]), value=settings["sample_size"], step=10,
                key="sample_size",
            )
        with param_cols[1]:
            row_tolerance = st.slider(
                "Row Count Tolerance (%)",
                min_value=0.0, max_value=max(10.0, settings["row_tolerance"]), value=settings["row_tolerance"], step=0.5,
                key="row_tolerance",
            )
        with param_cols[2]:
            null_threshold = st.slider(
                "Null Diff Threshold (%)",
                min_value=0.0, max_value=max(20.0, settings["null_threshold"]), value=settings["null_threshold"], step=1.0,
                key="null_threshold",
            )

        # Schemas
        schema_cols = st.columns(2)
        with schema_cols[0]:
            source_schema = st.text_input(
                "Source Schema", value=src_profile.schema if src_profile else "public",
                key="src_schema_val",
            )
        with schema_cols[1]:
            target_schema = st.text_input(
                "Target Schema", value=tgt_profile.schema if tgt_profile else "public",
                key="tgt_schema_val",
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table Selection ───────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### 📋 Table Selection")

        table_mode = st.radio(
            "How do you want to select tables?",
            ["Auto-discover common tables", "Select tables from database", "Filter by configured table group", "Manually enter table names", "Custom SQL queries"],
            key="table_mode",
            horizontal=True,
        )

        tables_to_validate = None
        custom_src_query = ""
        custom_tgt_query = ""
        table_pks = {}

        if table_mode == "Select tables from database":
            with st.spinner("🔍 Fetching tables from database..."):
                try:
                    src_tables = set(src_conn.get_table_list(source_schema))
                    tgt_tables = set(tgt_conn.get_table_list(target_schema))
                    common_tables = sorted(list(src_tables & tgt_tables))
                except Exception as e:
                    st.warning(f"Could not retrieve tables automatically: {e}")
                    common_tables = []

            if common_tables:
                tables_to_validate = st.multiselect(
                    "Choose tables to validate:",
                    options=common_tables,
                    default=common_tables,
                    help="Select the exact list of tables you wish to validate."
                )
                st.info(f"📋 {len(tables_to_validate)} of {len(common_tables)} common tables selected.")
            else:
                st.error("❌ No common tables discovered. Please check connection configurations or enter table names manually.")

        elif table_mode == "Filter by configured table group":
            import os
            import re
            import json

            mapping_dir = "tables"
            groups = set()
            if os.path.exists(mapping_dir):
                for f in os.listdir(mapping_dir):
                    if f.endswith(".json"):
                        match = re.match(r"(.+?)(_aggregation)?\.json", f)
                        if match:
                            groups.add(match.group(1))
            
            sorted_groups = sorted(list(groups))
            
            if sorted_groups:
                selected_group = st.selectbox(
                    "Select configured table group:",
                    options=sorted_groups,
                    help="Choose a pre-configured table group. Tables and their primary keys will load automatically."
                )
                
                group_mapping = {}
                loaded_file = ""
                try:
                    agg_file = f"{selected_group}_aggregation.json"
                    std_file = f"{selected_group}.json"
                    files_in_dir = os.listdir(mapping_dir)
                    
                    if agg_file in files_in_dir:
                        loaded_file = agg_file
                    elif std_file in files_in_dir:
                        loaded_file = std_file
                        
                    if loaded_file:
                        file_path = os.path.join(mapping_dir, loaded_file)
                        with open(file_path, "r") as f:
                            group_mapping = json.load(f)
                            
                        tables_to_validate = list(group_mapping.keys())
                        
                        for tbl, pk in group_mapping.items():
                            table_pks[tbl.strip().lower()] = str(pk).strip()
                            
                        st.success(
                            f"✅ Synced group `{selected_group}`: Loaded {len(tables_to_validate)} tables "
                            f"and their primary keys from `{loaded_file}`."
                        )
                        
                        with st.expander("👁️ View tables in this group", expanded=False):
                            st.write(tables_to_validate)
                    else:
                        st.error(f"Could not find configuration file for group '{selected_group}'")
                except Exception as e:
                    st.error(f"Error loading group file: {e}")
            else:
                st.warning("⚠️ No table group configuration files found in `tables/` directory.")

        elif table_mode == "Manually enter table names":
            tables_input = st.text_area(
                "Enter table names (one per line)",
                height=120,
                key="tables_input",
                placeholder="table_name_1\ntable_name_2\ntable_name_3",
            )
            if tables_input.strip():
                tables_to_validate = [t.strip() for t in tables_input.strip().split("\n") if t.strip()]
                st.info(f"📋 {len(tables_to_validate)} tables specified")

        elif table_mode == "Custom SQL queries":
            sql_cols = st.columns(2)
            with sql_cols[0]:
                custom_src_query = st.text_area(
                    "Source Query", height=150, key="custom_src_q",
                    placeholder="SELECT * FROM schema.table ORDER BY id LIMIT 100",
                )
            with sql_cols[1]:
                custom_tgt_query = st.text_area(
                    "Target Query", height=150, key="custom_tgt_q",
                    placeholder="SELECT * FROM schema.table ORDER BY id LIMIT 100",
                )
        else:
            st.info("🔍 Tables present in both source and target will be auto-discovered.")

        # Optional: PK mapping
        with st.expander("🔑 Primary Key Mapping (optional)"):
            st.markdown("Define primary keys for row sorting during hash comparison.")
            
            # Dynamic loading of PK mapping configurations from tables/ directory
            import os
            import json
            
            mapping_dir = "tables"
            json_files = []
            if os.path.exists(mapping_dir):
                json_files = [f for f in os.listdir(mapping_dir) if f.endswith(".json")]
            
            selected_file = st.selectbox(
                "📂 Sync primary keys from a local configuration file:",
                options=["-- None / Manual Input --"] + sorted(json_files),
                key="pk_mapping_file"
            )
            
            # Read selected mapping file
            if selected_file != "-- None / Manual Input --":
                try:
                    file_path = os.path.join(mapping_dir, selected_file)
                    with open(file_path, "r") as f:
                        file_mapping = json.load(f)
                    # Merge into table_pks
                    for tbl, pk in file_mapping.items():
                        table_pks[tbl.strip().lower()] = str(pk).strip()
                    st.success(f"✅ Synced {len(file_mapping)} primary key mappings from `{selected_file}`.")
                except Exception as e:
                    st.error(f"Error loading PK mapping file: {e}")
            
            # Manual PK input (optional, overrides file mappings)
            st.markdown("**Manual PK Overrides / Additions:**")
            pk_input = st.text_area(
                "Format: `table_name: pk_column1, pk_column2` (one per line)",
                height=100,
                key="pk_mapping",
                placeholder="users: user_id\norders: order_id, customer_id",
            )
            if pk_input.strip():
                for line in pk_input.strip().split("\n"):
                    if ":" in line:
                        tbl, pk = line.split(":", 1)
                        table_pks[tbl.strip().lower()] = pk.strip()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Run Button ────────────────────────────────────────────────────────
    if st.button("🚀 Start Validation", use_container_width=True, type="primary"):
        if not selected_types:
            st.error("Please select at least one validation type.")
            return

        _run_validation(
            src_conn, tgt_conn,
            source_schema=source_schema,
            target_schema=target_schema,
            selected_types=selected_types,
            sample_size=sample_size,
            row_tolerance=row_tolerance,
            null_threshold=null_threshold,
            tables=tables_to_validate,
            table_pks=table_pks,
            custom_src_query=custom_src_query,
            custom_tgt_query=custom_tgt_query,
            src_label=src_profile.display_label() if src_profile else "Source",
            tgt_label=tgt_profile.display_label() if tgt_profile else "Target",
        )


def _run_validation(
    src_conn, tgt_conn,
    source_schema, target_schema,
    selected_types, sample_size,
    row_tolerance, null_threshold,
    tables, table_pks,
    custom_src_query, custom_tgt_query,
    src_label, tgt_label,
):
    """Execute validation with live interactive progress."""
    # Load current normalization settings
    settings = st.session_state.get("app_settings", load_settings())

    config = ValidationConfig(
        validation_types=selected_types,
        sample_size=sample_size,
        row_count_tolerance_pct=row_tolerance,
        null_diff_threshold_pct=null_threshold,
        case_sensitive=settings.get("case_sensitive", False),
        normalize_whitespace=settings.get("normalize_whitespace", True),
        numeric_precision=settings.get("numeric_precision", 6),
        tables=tables,
        table_pks=table_pks,
        source_schema=source_schema,
        target_schema=target_schema,
        custom_source_query=custom_src_query,
        custom_target_query=custom_tgt_query,
    )

    validator = DataValidator(src_conn, tgt_conn, config)

    # ── Progress UI ───────────────────────────────────────────────────────
    st.markdown("---")
    render_section_header("Validation Progress", "⏳")

    # Create progress containers
    progress_bar = st.progress(0, text="Initializing...")
    status_text = st.empty()
    metrics_row = st.columns(4)
    completed_metric = metrics_row[0].empty()
    passed_metric = metrics_row[1].empty()
    failed_metric = metrics_row[2].empty()
    elapsed_metric = metrics_row[3].empty()

    # Live log
    log_container = st.expander("📜 Live Validation Log", expanded=True)
    log_placeholder = log_container.empty()
    log_messages = []

    # Tracking
    results_tracker = {"completed": 0, "passed": 0, "failed": 0, "warned": 0}
    start_time = time.time()

    def update_metrics():
        elapsed = time.time() - start_time
        completed_metric.metric("✅ Completed", results_tracker["completed"])
        passed_metric.metric("🟢 Passed", results_tracker["passed"])
        failed_metric.metric("🔴 Failed", results_tracker["failed"])
        elapsed_metric.metric("⏱️ Elapsed", f"{elapsed:.1f}s")

    def on_progress(current, total, table_name, message):
        pct = current / total if total > 0 else 0
        progress_bar.progress(
            pct,
            text=f"Table {current}/{total} — {table_name}",
        )
        status_text.markdown(
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.88rem;'
            f'color:var(--text-secondary);padding:8px 0">{message}</div>',
            unsafe_allow_html=True,
        )
        log_messages.append(f"`[{current}/{total}]` {message}")
        log_placeholder.markdown("\n\n".join(log_messages[-30:]))

    def on_table_complete(table_name, result):
        results_tracker["completed"] += 1
        if result.status == "PASS":
            results_tracker["passed"] += 1
        elif result.status == "FAIL":
            results_tracker["failed"] += 1
        else:
            results_tracker["warned"] += 1
        update_metrics()

    # ── Execute ───────────────────────────────────────────────────────────
    if custom_src_query and custom_tgt_query:
        # Custom query mode
        status_text.markdown("Running custom queries...")
        try:
            src_df = src_conn.execute_query(custom_src_query)
            tgt_df = tgt_conn.execute_query(custom_tgt_query)
            result = validator.validate_custom_query(src_df, tgt_df, "Custom_Query")
            results_tracker["completed"] = 1
            if result.status == "PASS":
                results_tracker["passed"] = 1
            else:
                results_tracker["failed"] = 1
            progress_bar.progress(1.0, text="Complete!")
            update_metrics()
            results = {"Custom_Query": result}
        except Exception as e:
            st.error(f"Query execution failed: {e}")
            return
    else:
        results = validator.validate_all_tables(
            on_progress=on_progress,
            on_table_complete=on_table_complete,
        )

    # ── Completion ────────────────────────────────────────────────────────
    total_time = time.time() - start_time
    progress_bar.progress(1.0, text=f"✅ Validation complete! ({total_time:.1f}s)")

    # Generate report
    report_gen = ReportGenerator(
        table_summaries=validator.table_summaries,
        detailed_results=validator.validation_results,
        source_label=src_label,
        target_label=tgt_label,
    )

    # Store results in session state
    run_summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tables": len(results),
        "passed": results_tracker["passed"],
        "failed": results_tracker["failed"],
        "warned": results_tracker["warned"],
        "pass_rate": (results_tracker["passed"] / len(results) * 100) if results else 0,
        "duration": round(total_time, 2),
        "summaries": validator.table_summaries,
        "results": validator.validation_results,
        "report_gen": report_gen,
        "src_label": src_label,
        "tgt_label": tgt_label,
    }

    st.session_state["last_validation"] = run_summary
    if "validation_history" not in st.session_state:
        st.session_state["validation_history"] = []
    st.session_state["validation_history"].append(run_summary)

    # ── Summary Cards ─────────────────────────────────────────────────────
    st.markdown("---")
    render_section_header("Validation Complete", "🎉")

    stats = report_gen.get_statistics()
    summary_cols = st.columns(5)
    with summary_cols[0]:
        render_metric_card("Tables", stats["total_tables"], "📋", "#4A9EFF")
    with summary_cols[1]:
        render_metric_card("Passed", stats["passed_tables"], "✅", "#00D4AA")
    with summary_cols[2]:
        render_metric_card("Failed", stats["failed_tables"], "❌", "#FF4757")
    with summary_cols[3]:
        render_metric_card("Pass Rate", f"{stats['pass_rate']:.1f}%", "🎯",
                           "#00D4AA" if stats["pass_rate"] >= 90 else "#FF4757")
    with summary_cols[4]:
        render_metric_card("Duration", f"{total_time:.1f}s", "⏱️", "#6C63FF")

    # ── Download ZIP ──────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    try:
        zip_bytes = report_gen.generate_zip_bundle()
        st.download_button(
            label="📦 Download Full Report (ZIP)",
            data=zip_bytes,
            file_name=f"validation_report_{report_gen.timestamp}.zip",
            mime="application/zip",
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"Could not generate ZIP: {e}")

    st.info("💡 Go to the **Results** page for detailed interactive exploration of the validation results.")
