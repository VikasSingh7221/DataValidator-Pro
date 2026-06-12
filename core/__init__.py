"""
DataValidator Core — Generalized data validation engine.
Supports multiple database types and validation strategies.
"""

from core.models import (
    DataSourceType,
    ValidationResult,
    TableValidation,
    ValidationRun,
    ConnectionProfile,
    ValidationConfig,
)
from core.connections import create_connection
from core.validators import DataValidator
from core.reports import ReportGenerator

__all__ = [
    "DataSourceType",
    "ValidationResult",
    "TableValidation",
    "ValidationRun",
    "ConnectionProfile",
    "ValidationConfig",
    "create_connection",
    "DataValidator",
    "ReportGenerator",
]
