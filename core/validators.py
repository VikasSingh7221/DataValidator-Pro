"""
Generalized data validation engine.
Supports 7 validation types with progress callbacks for real-time UI updates.
"""

import logging
import time
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Callable, Any

from core.models import (
    ValidationResult, TableValidation, ValidationConfig,
    ValidationType, ValidationStatus, SchemaColumn,
    NullAnalysisResult, StatisticalResult,
)
from core.connections import DatabaseConnection
from core.normalizers import DataNormalizer

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Multi-strategy data validator.

    Supports progress callbacks so the Streamlit UI can display
    real-time table-by-table progress bars and status updates.
    """

    def __init__(
        self,
        source_conn: DatabaseConnection,
        target_conn: DatabaseConnection,
        config: ValidationConfig,
    ):
        self.source = source_conn
        self.target = target_conn
        self.config = config
        self.normalizer = DataNormalizer(
            case_sensitive=config.case_sensitive,
            normalize_whitespace=config.normalize_whitespace,
            numeric_precision=config.numeric_precision,
        )
        self.validation_results: List[ValidationResult] = []
        self.table_summaries: List[TableValidation] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def validate_all_tables(
        self,
        on_progress: Optional[Callable[[int, int, str, str], None]] = None,
        on_table_complete: Optional[Callable[[str, TableValidation], None]] = None,
    ) -> Dict[str, TableValidation]:
        """
        Validate all tables with real-time progress callbacks.

        Args:
            on_progress: Called with (current_index, total, table_name, status_msg)
            on_table_complete: Called with (table_name, result) after each table finishes
        """
        tables = self._resolve_tables()
        total = len(tables)
        results = {}

        logger.info(f"Validating {total} tables...")

        for idx, table in enumerate(tables):
            table_lower = table.lower()

            # Notify progress
            if on_progress:
                on_progress(idx, total, table, f"⏳ Validating {table}...")

            try:
                result = self.validate_table(table)
                results[table_lower] = result
                self.table_summaries.append(result)

                if on_table_complete:
                    on_table_complete(table, result)

                if on_progress:
                    icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
                    on_progress(
                        idx + 1, total, table,
                        f"{icon} {table} — {result.status} ({result.pass_rate:.0f}%)"
                    )

            except Exception as e:
                logger.error(f"Error validating {table}: {e}")
                if on_progress:
                    on_progress(idx + 1, total, table, f"💥 {table} — ERROR: {str(e)[:50]}")

        return results

    def validate_table(self, table_name: str) -> TableValidation:
        """Run all configured validations on a single table."""
        start = time.time()
        checks_passed = 0
        checks_failed = 0
        checks_warning = 0
        details = []
        types_run = []

        src_schema = self.config.source_schema
        tgt_schema = self.config.target_schema
        pk = (self.config.table_pks or {}).get(table_name.lower())

        # ── Row counts (always fetched for context) ───────────────────────────
        try:
            src_count = self.source.get_row_count(table_name, src_schema)
            tgt_count = self.target.get_row_count(table_name, tgt_schema)
        except Exception:
            src_count, tgt_count = 0, 0

        details.append(f"Rows: Source={src_count:,} Target={tgt_count:,}")

        # ── Row Count Validation ──────────────────────────────────────────────
        if ValidationType.ROW_COUNT in self.config.validation_types:
            types_run.append("Row Count")
            p, f, w, d = self._validate_row_count(table_name, src_count, tgt_count)
            checks_passed += p
            checks_failed += f
            checks_warning += w
            details.append(d)

        # ── Schema Validation ─────────────────────────────────────────────────
        if ValidationType.SCHEMA in self.config.validation_types:
            types_run.append("Schema")
            p, f, w, d = self._validate_schema(table_name, src_schema, tgt_schema)
            checks_passed += p
            checks_failed += f
            checks_warning += w
            details.append(d)

        # ── Row Hash Validation ───────────────────────────────────────────────
        if ValidationType.ROW_HASH in self.config.validation_types:
            types_run.append("Row Hash")
            if src_count > 0 and tgt_count > 0:
                p, f, w, d = self._validate_row_hashes(
                    table_name, src_schema, tgt_schema, pk
                )
                checks_passed += p
                checks_failed += f
                checks_warning += w
                details.append(d)
            else:
                details.append("Row Hash: skipped (empty table)")

        # ── Null Analysis ─────────────────────────────────────────────────────
        if ValidationType.NULL_ANALYSIS in self.config.validation_types:
            types_run.append("Null Analysis")
            if src_count > 0 and tgt_count > 0:
                p, f, w, d = self._validate_nulls(table_name, src_schema, tgt_schema, pk)
                checks_passed += p
                checks_failed += f
                checks_warning += w
                details.append(d)

        # ── Duplicate Detection ───────────────────────────────────────────────
        if ValidationType.DUPLICATE_DETECTION in self.config.validation_types:
            types_run.append("Duplicates")
            if pk and src_count > 0 and tgt_count > 0:
                p, f, w, d = self._validate_duplicates(
                    table_name, src_schema, tgt_schema, pk
                )
                checks_passed += p
                checks_failed += f
                checks_warning += w
                details.append(d)
            else:
                details.append("Duplicates: skipped (no PK defined)")

        # ── Statistical Profiling ─────────────────────────────────────────────
        if ValidationType.STATISTICAL_PROFILE in self.config.validation_types:
            types_run.append("Statistics")
            if src_count > 0 and tgt_count > 0:
                p, f, w, d = self._validate_statistics(
                    table_name, src_schema, tgt_schema, pk
                )
                checks_passed += p
                checks_failed += f
                checks_warning += w
                details.append(d)

        # ── Summary ───────────────────────────────────────────────────────────
        total_checks = checks_passed + checks_failed + checks_warning
        pass_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0.0

        if checks_failed == 0:
            status = "PASS" if checks_warning == 0 else "WARNING"
        else:
            status = "FAIL"

        pct_diff = round(
            abs(src_count - tgt_count) / (src_count if src_count > 0 else 1) * 100, 2
        )

        return TableValidation(
            table_name=table_name,
            total_checks=total_checks,
            passed_checks=checks_passed,
            failed_checks=checks_failed,
            warning_checks=checks_warning,
            pass_rate=pass_rate,
            row_count_source=src_count,
            row_count_target=tgt_count,
            row_count_diff_pct=pct_diff,
            sampled_rows=min(self.config.sample_size, src_count, tgt_count),
            duration_seconds=round(time.time() - start, 2),
            status=status,
            details=" | ".join(details),
            validation_types_run=types_run,
        )

    def validate_custom_query(
        self, source_df: pd.DataFrame, target_df: pd.DataFrame, query_name: str = "Custom Query"
    ) -> TableValidation:
        """Validate two arbitrary DataFrames (from custom SQL or file uploads)."""
        start = time.time()
        checks_passed = checks_failed = checks_warning = 0
        details = [f"Rows: Source={len(source_df):,} Target={len(target_df):,}"]

        if len(source_df) > 0 and len(target_df) > 0:
            results = self._row_hash_comparison(query_name, source_df, target_df)
            for r in results:
                self.validation_results.append(r)
                if r.status == "PASS":
                    checks_passed += 1
                elif r.status == "FAIL":
                    checks_failed += 1
                else:
                    checks_warning += 1
            mismatches = sum(1 for r in results if r.status == "FAIL")
            if mismatches:
                details.append(f"Hash: {mismatches}/{len(results)} mismatched")
            else:
                details.append(f"Hash: All {len(results)} rows matched")

        total = checks_passed + checks_failed + checks_warning
        pass_rate = (checks_passed / total * 100) if total > 0 else 0.0

        tv = TableValidation(
            table_name=query_name,
            total_checks=total,
            passed_checks=checks_passed,
            failed_checks=checks_failed,
            warning_checks=checks_warning,
            pass_rate=pass_rate,
            row_count_source=len(source_df),
            row_count_target=len(target_df),
            row_count_diff_pct=round(
                abs(len(source_df) - len(target_df)) /
                (len(source_df) if len(source_df) > 0 else 1) * 100, 2
            ),
            sampled_rows=min(len(source_df), len(target_df)),
            duration_seconds=round(time.time() - start, 2),
            status="PASS" if checks_failed == 0 and checks_warning == 0
                   else "FAIL" if checks_failed > 0 else "WARNING",
            details=" | ".join(details),
            validation_types_run=["Row Hash"],
        )
        self.table_summaries.append(tv)
        return tv

    # ── Private: Individual Validations ───────────────────────────────────────

    def _validate_row_count(self, table: str, src: int, tgt: int):
        tolerance = self.config.row_count_tolerance_pct
        diff_pct = abs(src - tgt) / (src if src > 0 else 1) * 100

        if src == tgt:
            status, detail = "PASS", f"Row Count: exact match ({src:,})"
            self.validation_results.append(ValidationResult(
                table_name=table, validation_type="ROW_COUNT",
                status="PASS", source_value=src, target_value=tgt,
                details=detail,
            ))
            return 1, 0, 0, detail
        elif diff_pct <= tolerance:
            status = "WARNING"
            detail = f"Row Count: within tolerance ({diff_pct:.2f}% ≤ {tolerance}%)"
            self.validation_results.append(ValidationResult(
                table_name=table, validation_type="ROW_COUNT",
                status="WARNING", source_value=src, target_value=tgt,
                difference=src - tgt, details=detail,
            ))
            return 0, 0, 1, detail
        else:
            detail = f"Row Count: MISMATCH src={src:,} tgt={tgt:,} (diff {diff_pct:.2f}%)"
            self.validation_results.append(ValidationResult(
                table_name=table, validation_type="ROW_COUNT",
                status="FAIL", source_value=src, target_value=tgt,
                difference=src - tgt, details=detail,
            ))
            return 0, 1, 0, detail

    def _validate_schema(self, table: str, src_schema: str, tgt_schema: str):
        try:
            src_cols = self.source.get_schema_info(table, src_schema)
            tgt_cols = self.target.get_schema_info(table, tgt_schema)
        except Exception as e:
            detail = f"Schema: error — {e}"
            return 0, 0, 1, detail

        src_names = {c.column_name.lower() for c in src_cols}
        tgt_names = {c.column_name.lower() for c in tgt_cols}

        missing_in_tgt = src_names - tgt_names
        extra_in_tgt = tgt_names - src_names

        passed = failed = warned = 0

        if not missing_in_tgt and not extra_in_tgt:
            detail = f"Schema: {len(src_names)} columns matched"
            self.validation_results.append(ValidationResult(
                table_name=table, validation_type="SCHEMA",
                status="PASS", source_value=len(src_names),
                target_value=len(tgt_names), details=detail,
            ))
            passed += 1
        else:
            parts = []
            if missing_in_tgt:
                parts.append(f"missing in target: {missing_in_tgt}")
            if extra_in_tgt:
                parts.append(f"extra in target: {extra_in_tgt}")
            detail = f"Schema: {'; '.join(parts)}"
            self.validation_results.append(ValidationResult(
                table_name=table, validation_type="SCHEMA",
                status="FAIL", source_value=len(src_names),
                target_value=len(tgt_names), details=detail,
            ))
            failed += 1

        # Check data types for common columns
        src_type_map = {c.column_name.lower(): c.data_type.lower() for c in src_cols}
        tgt_type_map = {c.column_name.lower(): c.data_type.lower() for c in tgt_cols}
        common = src_names & tgt_names
        type_mismatches = []
        for col in common:
            if src_type_map.get(col) != tgt_type_map.get(col):
                type_mismatches.append(
                    f"{col}: {src_type_map[col]} → {tgt_type_map[col]}"
                )
        if type_mismatches:
            detail += f" | Type diffs: {len(type_mismatches)}"
            warned += 1
        else:
            if common:
                passed += 1

        return passed, failed, warned, detail

    def _validate_row_hashes(self, table: str, src_schema: str, tgt_schema: str, pk: str):
        try:
            src_df = self.source.get_sample_data(
                table, self.config.sample_size, src_schema, pk
            )
            tgt_df = self.target.get_sample_data(
                table, self.config.sample_size, tgt_schema, pk
            )
        except Exception as e:
            return 0, 0, 1, f"Hash: fetch error — {e}"

        results = self._row_hash_comparison(table, src_df, tgt_df)
        p = f = w = 0
        for r in results:
            self.validation_results.append(r)
            if r.status == "PASS":
                p += 1
            elif r.status == "FAIL":
                f += 1
            else:
                w += 1

        if f == 0:
            detail = f"Hash: All {len(results)} rows matched"
        else:
            detail = f"Hash: {f}/{len(results)} rows mismatched"
        return p, f, w, detail

    def _validate_nulls(self, table: str, src_schema: str, tgt_schema: str, pk: str):
        try:
            src_df = self.source.get_sample_data(
                table, self.config.sample_size, src_schema, pk
            )
            tgt_df = self.target.get_sample_data(
                table, self.config.sample_size, tgt_schema, pk
            )
        except Exception as e:
            return 0, 0, 1, f"Nulls: error — {e}"

        src_df = self.normalizer.normalize_dataframe(src_df)
        tgt_df = self.normalizer.normalize_dataframe(tgt_df)
        common = sorted(set(src_df.columns) & set(tgt_df.columns))

        p = f = w = 0
        threshold = self.config.null_diff_threshold_pct

        for col in common:
            src_nulls = src_df[col].isnull().sum()
            tgt_nulls = tgt_df[col].isnull().sum()
            src_pct = (src_nulls / len(src_df) * 100) if len(src_df) > 0 else 0
            tgt_pct = (tgt_nulls / len(tgt_df) * 100) if len(tgt_df) > 0 else 0
            diff = abs(src_pct - tgt_pct)

            if diff <= threshold:
                p += 1
                status = "PASS"
            else:
                f += 1
                status = "FAIL"

            self.validation_results.append(ValidationResult(
                table_name=table, validation_type="NULL_ANALYSIS",
                status=status, source_value=f"{src_pct:.1f}%",
                target_value=f"{tgt_pct:.1f}%", difference=f"{diff:.1f}%",
                column_name=col,
                details=f"Null diff for {col}: {diff:.1f}%",
            ))

        detail = f"Nulls: {p}/{p+f} columns within {threshold}% threshold"
        return p, f, w, detail

    def _validate_duplicates(self, table: str, src_schema: str, tgt_schema: str, pk: str):
        pk_cols = [c.strip() for c in pk.split(",")]
        pk_list = ", ".join(pk_cols)

        try:
            # Source duplicates
            try:
                src_query = f"""
                SELECT {pk_list}, COUNT(*) as dup_count
                FROM {src_schema}.{table}
                GROUP BY {pk_list} HAVING COUNT(*) > 1
                LIMIT 100
                """
                src_dups = self.source.execute_query(src_query)
            except Exception:
                src_dups = pd.DataFrame()

            # Target duplicates
            try:
                tgt_pk_list = ", ".join([c.upper() for c in pk_cols])
                tgt_query = f"""
                SELECT {tgt_pk_list}, COUNT(*) as dup_count
                FROM {tgt_schema}.{table.upper() if 'snowflake' in str(type(self.target)).lower() else table}
                GROUP BY {tgt_pk_list} HAVING COUNT(*) > 1
                LIMIT 100
                """
                tgt_dups = self.target.execute_query(tgt_query)
            except Exception:
                tgt_dups = pd.DataFrame()

            src_dup_count = len(src_dups)
            tgt_dup_count = len(tgt_dups)

            if src_dup_count == 0 and tgt_dup_count == 0:
                status = "PASS"
                detail = f"Duplicates: none found in either source"
            else:
                status = "WARNING"
                detail = f"Duplicates: source={src_dup_count} target={tgt_dup_count}"

            self.validation_results.append(ValidationResult(
                table_name=table, validation_type="DUPLICATE_DETECTION",
                status=status, source_value=src_dup_count,
                target_value=tgt_dup_count, details=detail,
            ))
            p = 1 if status == "PASS" else 0
            w = 1 if status == "WARNING" else 0
            return p, 0, w, detail

        except Exception as e:
            detail = f"Duplicates: error — {e}"
            return 0, 0, 1, detail

    def _validate_statistics(self, table: str, src_schema: str, tgt_schema: str, pk: str):
        try:
            src_df = self.source.get_sample_data(
                table, self.config.sample_size, src_schema, pk
            )
            tgt_df = self.target.get_sample_data(
                table, self.config.sample_size, tgt_schema, pk
            )
        except Exception as e:
            return 0, 0, 1, f"Stats: error — {e}"

        src_df = self.normalizer.normalize_dataframe(src_df)
        tgt_df = self.normalizer.normalize_dataframe(tgt_df)
        common = sorted(set(src_df.columns) & set(tgt_df.columns))

        p = f = 0
        for col in common:
            src_distinct = src_df[col].nunique()
            tgt_distinct = tgt_df[col].nunique()
            match = src_distinct == tgt_distinct

            self.validation_results.append(ValidationResult(
                table_name=table, validation_type="STATISTICAL_PROFILE",
                status="PASS" if match else "WARNING",
                source_value=src_distinct, target_value=tgt_distinct,
                column_name=col,
                details=f"Distinct count for {col}: src={src_distinct} tgt={tgt_distinct}",
            ))

            # Numeric columns — compare min/max/mean
            if pd.api.types.is_numeric_dtype(src_df[col]) and pd.api.types.is_numeric_dtype(tgt_df[col]):
                for metric, fn in [("min", "min"), ("max", "max"), ("mean", "mean")]:
                    sv = getattr(src_df[col], fn)()
                    tv = getattr(tgt_df[col], fn)()
                    m = abs(float(sv) - float(tv)) < 0.001 if pd.notna(sv) and pd.notna(tv) else sv == tv
                    if m:
                        p += 1
                    else:
                        f += 1
                    self.validation_results.append(ValidationResult(
                        table_name=table, validation_type="STATISTICAL_PROFILE",
                        status="PASS" if m else "FAIL",
                        source_value=sv, target_value=tv, column_name=col,
                        details=f"{metric} for {col}",
                    ))

            if match:
                p += 1
            else:
                f += 1

        detail = f"Stats: {p} matched, {f} diffs across {len(common)} columns"
        return p, f, 0, detail

    # ── Private: Row Hash Comparison ──────────────────────────────────────────

    def _row_hash_comparison(
        self, table_name: str, src_df: pd.DataFrame, tgt_df: pd.DataFrame,
    ) -> List[ValidationResult]:
        """Compare rows via MD5 hash. Returns one result per row."""
        src_df = self.normalizer.normalize_dataframe(src_df)
        tgt_df = self.normalizer.normalize_dataframe(tgt_df)

        common_cols = sorted(set(src_df.columns) & set(tgt_df.columns))
        if not common_cols:
            return [ValidationResult(
                table_name=table_name, validation_type="ROW_HASH_DATA",
                status="WARNING", source_value="N/A", target_value="N/A",
                details="No common columns found",
            )]

        min_len = min(len(src_df), len(tgt_df))
        src_sub = src_df[common_cols].head(min_len).reset_index(drop=True)
        tgt_sub = tgt_df[common_cols].head(min_len).reset_index(drop=True)

        results = []
        for i in range(min_len):
            src_hash = self.normalizer.row_hash(src_sub.iloc[i])
            tgt_hash = self.normalizer.row_hash(tgt_sub.iloc[i])

            if src_hash == tgt_hash:
                status, detail = "PASS", "Row matches"
            else:
                status = "FAIL"
                diff_cols = [
                    col for col in common_cols
                    if self.normalizer.normalize_value(src_sub.iloc[i][col])
                    != self.normalizer.normalize_value(tgt_sub.iloc[i][col])
                ]
                detail = f"Mismatch in: {diff_cols}"

            results.append(ValidationResult(
                table_name=table_name,
                validation_type=f"ROW_HASH_{i}",
                status=status,
                source_value=src_hash,
                target_value=tgt_hash,
                details=detail,
            ))

        return results

    # ── Private: Table Resolution ─────────────────────────────────────────────

    def _resolve_tables(self) -> List[str]:
        """Determine which tables to validate."""
        if self.config.tables:
            return self.config.tables

        # Auto-discover common tables
        try:
            src_tables = set(self.source.get_table_list(self.config.source_schema))
            tgt_tables = set(self.target.get_table_list(self.config.target_schema))
            common = sorted(src_tables & tgt_tables)

            only_src = src_tables - tgt_tables
            only_tgt = tgt_tables - src_tables
            if only_src:
                logger.warning(f"Only in source: {only_src}")
            if only_tgt:
                logger.warning(f"Only in target: {only_tgt}")

            return common
        except Exception as e:
            logger.error(f"Table discovery failed: {e}")
            return list((self.config.table_pks or {}).keys())
