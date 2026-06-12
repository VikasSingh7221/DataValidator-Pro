"""
Data normalization utilities for consistent comparison across databases.
"""

import hashlib
import re
import pandas as pd
from typing import Optional


class DataNormalizer:
    """Configurable value normalization for cross-database comparison."""

    def __init__(
        self,
        case_sensitive: bool = False,
        normalize_whitespace: bool = True,
        numeric_precision: int = 6,
    ):
        self.case_sensitive = case_sensitive
        self.normalize_whitespace = normalize_whitespace
        self.numeric_precision = numeric_precision

    def normalize_value(self, v) -> str:
        """Normalize a single cell value to a comparable string."""
        # Handle pandas NA types
        if pd.isna(v) if not isinstance(v, str) else False:
            return ""

        # Convert floats that are whole numbers to integers
        if isinstance(v, float) and pd.notna(v):
            if v.is_integer():
                v = int(v)

        val_str = str(v).strip()

        # Remove trailing .0 from string representations
        if val_str.endswith(".0"):
            try:
                if float(val_str).is_integer():
                    val_str = val_str[:-2]
            except ValueError:
                pass

        # Null-like values → empty string
        null_values = {"nan", "None", "NaT", "<NA>", "NaN", "NULL", "null", ""}
        if val_str in null_values:
            return ""

        # Whitespace normalization
        if self.normalize_whitespace:
            val_str = re.sub(r"\s+", " ", val_str).strip()

        # Case normalization
        if not self.case_sensitive:
            val_str = val_str.lower()

        return val_str

    def row_hash(self, row: pd.Series, columns: Optional[list] = None) -> str:
        """Return a 12-char MD5 hex digest for one normalized row."""
        if columns:
            row = row[columns]
        concatenated = "|".join(self.normalize_value(v) for v in row)
        return hashlib.md5(concatenated.encode("utf-8")).hexdigest()[:12]

    def normalize_column_name(self, col: str) -> str:
        """Normalize column name for comparison."""
        return col.strip().lower().replace(" ", "_")

    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize all column names in a DataFrame."""
        df = df.copy()
        df.columns = [self.normalize_column_name(c) for c in df.columns]
        return df
