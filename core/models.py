"""
Data models and enums for the validation engine.
"""

import uuid
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ─────────────────────────────────────────────────────────────────────

class DataSourceType(str, Enum):
    """Supported data source types."""
    POSTGRESQL = "PostgreSQL"
    MYSQL = "MySQL"
    SNOWFLAKE = "Snowflake"
    REDSHIFT = "Redshift"
    SQLITE = "SQLite"
    CSV_FILE = "CSV / Excel File"


class ValidationType(str, Enum):
    """Available validation checks."""
    ROW_HASH = "Row Hash Comparison"
    ROW_COUNT = "Row Count Comparison"
    SCHEMA = "Schema Comparison"
    NULL_ANALYSIS = "Null Analysis"
    DUPLICATE_DETECTION = "Duplicate Detection"
    STATISTICAL_PROFILE = "Statistical Profiling"
    CUSTOM_QUERY = "Custom Query Comparison"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class ConnectionProfile:
    """Stores database connection parameters."""
    name: str
    source_type: DataSourceType
    host: str = ""
    port: int = 0
    database: str = ""
    schema: str = ""
    user: str = ""
    password: str = ""
    # Snowflake-specific
    account: str = ""
    warehouse: str = ""
    role: str = ""
    # Auth options
    use_sso: bool = False
    use_mfa: bool = False
    mfa_code: Optional[int] = None
    # CSV/File source
    file_path: str = ""
    # Connection status
    is_connected: bool = False
    latency_ms: float = 0.0

    def display_label(self) -> str:
        if self.source_type == DataSourceType.CSV_FILE:
            return f"📄 {self.name} ({self.file_path})"
        elif self.source_type == DataSourceType.SNOWFLAKE:
            return f"❄️ {self.name} ({self.account}/{self.database})"
        else:
            return f"🗄️ {self.name} ({self.host}:{self.port}/{self.database})"


@dataclass
class ValidationResult:
    """One validation result record."""
    table_name: str
    validation_type: str
    status: str
    source_value: Any
    target_value: Any
    difference: Any = None
    details: str = ""
    column_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TableValidation:
    """Per-table summary."""
    table_name: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    pass_rate: float
    row_count_source: int
    row_count_target: int
    row_count_diff_pct: float
    sampled_rows: int
    duration_seconds: float
    status: str
    details: str = ""
    validation_types_run: List[str] = field(default_factory=list)


@dataclass
class SchemaColumn:
    """Schema information for a single column."""
    column_name: str
    data_type: str
    is_nullable: bool = True
    ordinal_position: int = 0
    character_maximum_length: Optional[int] = None
    numeric_precision: Optional[int] = None


@dataclass
class NullAnalysisResult:
    """Null analysis for a single column."""
    column_name: str
    source_null_count: int
    source_null_pct: float
    target_null_count: int
    target_null_pct: float
    difference_pct: float
    status: str


@dataclass
class StatisticalResult:
    """Statistical profile for a single column."""
    column_name: str
    metric: str  # min, max, mean, stddev, distinct_count
    source_value: Any
    target_value: Any
    match: bool


@dataclass
class ValidationConfig:
    """Configuration for a validation run."""
    validation_types: List[ValidationType] = field(
        default_factory=lambda: [ValidationType.ROW_HASH, ValidationType.ROW_COUNT]
    )
    sample_size: int = 100
    row_count_tolerance_pct: float = 0.0
    null_diff_threshold_pct: float = 5.0
    case_sensitive: bool = False
    normalize_whitespace: bool = True
    normalize_dates: bool = True
    numeric_precision: int = 6
    tables: Optional[List[str]] = None
    table_pks: Optional[Dict[str, str]] = None
    source_schema: str = "public"
    target_schema: str = "public"
    custom_source_query: str = ""
    custom_target_query: str = ""


@dataclass
class ValidationRun:
    """A complete validation run record."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now(
        timezone(timedelta(hours=5, minutes=30))
    ).strftime("%Y-%m-%d %H:%M:%S"))
    source_label: str = ""
    target_label: str = ""
    config: ValidationConfig = field(default_factory=ValidationConfig)
    table_summaries: List[TableValidation] = field(default_factory=list)
    detailed_results: List[ValidationResult] = field(default_factory=list)
    total_tables: int = 0
    passed_tables: int = 0
    failed_tables: int = 0
    warning_tables: int = 0
    overall_pass_rate: float = 0.0
    duration_seconds: float = 0.0
    status: str = "PENDING"
    report_path: str = ""
