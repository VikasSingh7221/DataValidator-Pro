"""
Generic database connection adapters.
Supports PostgreSQL, Redshift, MySQL, Snowflake, SQLite, and CSV/Excel files.
"""

import os
import time
import logging
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from core.models import DataSourceType, ConnectionProfile, SchemaColumn

logger = logging.getLogger(__name__)


# ── Abstract Base ─────────────────────────────────────────────────────────────

class DatabaseConnection(ABC):
    """Abstract database connection interface."""

    def __init__(self, profile: ConnectionProfile):
        self.profile = profile
        self.conn = None

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection. Returns True on success."""
        ...

    @abstractmethod
    def disconnect(self):
        """Close connection."""
        ...

    @abstractmethod
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL and return a DataFrame."""
        ...

    @abstractmethod
    def get_table_list(self, schema: Optional[str] = None) -> List[str]:
        """List all tables in the given schema."""
        ...

    @abstractmethod
    def get_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        """Return row count for a table."""
        ...

    @abstractmethod
    def get_sample_data(
        self, table_name: str, sample_size: int = 100,
        schema: Optional[str] = None, pk: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch a sample of rows from a table."""
        ...

    @abstractmethod
    def get_schema_info(self, table_name: str, schema: Optional[str] = None) -> List[SchemaColumn]:
        """Return column metadata for a table."""
        ...

    def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status + latency."""
        start = time.time()
        try:
            ok = self.connect()
            latency = (time.time() - start) * 1000
            self.profile.latency_ms = latency
            self.profile.is_connected = ok
            return {"success": ok, "latency_ms": round(latency, 1), "error": None}
        except Exception as e:
            return {"success": False, "latency_ms": 0, "error": str(e)}


# ── PostgreSQL / Redshift ─────────────────────────────────────────────────────

class PostgreSQLConnection(DatabaseConnection):
    """Handles PostgreSQL and Redshift (both use psycopg2)."""

    def connect(self) -> bool:
        try:
            import psycopg2
            self.conn = psycopg2.connect(
                host=self.profile.host,
                port=self.profile.port or 5432,
                database=self.profile.database,
                user=self.profile.user,
                password=self.profile.password,
                connect_timeout=10,
            )
            logger.info(f"Connected to {self.profile.source_type.value}: {self.profile.host}")
            self.profile.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.profile.is_connected = False
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.profile.is_connected = False

    def execute_query(self, query: str) -> pd.DataFrame:
        return pd.read_sql_query(query, self.conn)

    def get_table_list(self, schema: Optional[str] = None) -> List[str]:
        schema = schema or self.profile.schema or "public"
        query = f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        df = self.execute_query(query)
        return df["table_name"].str.lower().tolist()

    def get_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        schema = schema or self.profile.schema or "public"
        df = self.execute_query(f"SELECT COUNT(*) as cnt FROM {schema}.{table_name}")
        return int(df["cnt"].iloc[0])

    def get_sample_data(
        self, table_name: str, sample_size: int = 100,
        schema: Optional[str] = None, pk: Optional[str] = None,
    ) -> pd.DataFrame:
        schema = schema or self.profile.schema or "public"
        order = f"ORDER BY {pk}" if pk else "ORDER BY 1"
        query = f"SELECT * FROM {schema}.{table_name} {order} LIMIT {sample_size}"
        return self.execute_query(query)

    def get_schema_info(self, table_name: str, schema: Optional[str] = None) -> List[SchemaColumn]:
        schema = schema or self.profile.schema or "public"
        query = f"""
        SELECT column_name, data_type, is_nullable, ordinal_position,
               character_maximum_length, numeric_precision
        FROM information_schema.columns
        WHERE table_schema = '{schema}' AND LOWER(table_name) = LOWER('{table_name}')
        ORDER BY ordinal_position
        """
        df = self.execute_query(query)
        results = []
        for _, row in df.iterrows():
            results.append(SchemaColumn(
                column_name=row["column_name"],
                data_type=row["data_type"],
                is_nullable=row["is_nullable"] == "YES",
                ordinal_position=int(row["ordinal_position"]),
                character_maximum_length=row.get("character_maximum_length"),
                numeric_precision=row.get("numeric_precision"),
            ))
        return results


# ── Snowflake ─────────────────────────────────────────────────────────────────

class SnowflakeDBConnection(DatabaseConnection):

    def connect(self) -> bool:
        try:
            import snowflake.connector
            connect_args = {
                "account": self.profile.account,
                "user": self.profile.user,
                "warehouse": self.profile.warehouse,
                "database": self.profile.database,
            }
            if self.profile.role:
                connect_args["role"] = self.profile.role
            if self.profile.use_sso:
                connect_args["authenticator"] = "externalbrowser"
            else:
                connect_args["password"] = self.profile.password
                if self.profile.mfa_code is not None:
                    connect_args["passcode"] = self.profile.mfa_code

            self.conn = snowflake.connector.connect(**connect_args)
            logger.info(f"Connected to Snowflake: {self.profile.account}")
            self.profile.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Snowflake connection failed: {e}")
            self.profile.is_connected = False
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.profile.is_connected = False

    def execute_query(self, query: str) -> pd.DataFrame:
        cursor = self.conn.cursor()
        cursor.execute(query)
        df = cursor.fetch_pandas_all()
        cursor.close()
        return df

    def get_table_list(self, schema: Optional[str] = None) -> List[str]:
        schema = schema or self.profile.schema or "PUBLIC"
        query = f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = '{schema.upper()}'
        ORDER BY table_name
        """
        df = self.execute_query(query)
        return df["TABLE_NAME"].str.lower().tolist()

    def get_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        schema = schema or self.profile.schema or "PUBLIC"
        df = self.execute_query(
            f"SELECT COUNT(*) as CNT FROM {schema.upper()}.{table_name.upper()}"
        )
        return int(df["CNT"].iloc[0])

    def get_sample_data(
        self, table_name: str, sample_size: int = 100,
        schema: Optional[str] = None, pk: Optional[str] = None,
    ) -> pd.DataFrame:
        schema = schema or self.profile.schema or "PUBLIC"
        order = f"ORDER BY {pk.upper()}" if pk else "ORDER BY 1"
        query = (
            f"SELECT * FROM {schema.upper()}.{table_name.upper()} "
            f"{order} LIMIT {sample_size}"
        )
        return self.execute_query(query)

    def get_schema_info(self, table_name: str, schema: Optional[str] = None) -> List[SchemaColumn]:
        schema = schema or self.profile.schema or "PUBLIC"
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION,
               CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION
        FROM information_schema.columns
        WHERE table_schema = '{schema.upper()}' AND UPPER(table_name) = '{table_name.upper()}'
        ORDER BY ORDINAL_POSITION
        """
        df = self.execute_query(query)
        results = []
        for _, row in df.iterrows():
            results.append(SchemaColumn(
                column_name=row["COLUMN_NAME"],
                data_type=row["DATA_TYPE"],
                is_nullable=str(row["IS_NULLABLE"]).upper() == "YES",
                ordinal_position=int(row["ORDINAL_POSITION"]),
                character_maximum_length=row.get("CHARACTER_MAXIMUM_LENGTH"),
                numeric_precision=row.get("NUMERIC_PRECISION"),
            ))
        return results


# ── MySQL ─────────────────────────────────────────────────────────────────────

class MySQLConnection(DatabaseConnection):

    def connect(self) -> bool:
        try:
            import mysql.connector
            self.conn = mysql.connector.connect(
                host=self.profile.host,
                port=self.profile.port or 3306,
                database=self.profile.database,
                user=self.profile.user,
                password=self.profile.password,
                connect_timeout=10,
            )
            logger.info(f"Connected to MySQL: {self.profile.host}")
            self.profile.is_connected = True
            return True
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            self.profile.is_connected = False
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.profile.is_connected = False

    def execute_query(self, query: str) -> pd.DataFrame:
        return pd.read_sql_query(query, self.conn)

    def get_table_list(self, schema: Optional[str] = None) -> List[str]:
        schema = schema or self.profile.database
        query = f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = '{schema}' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        df = self.execute_query(query)
        col = df.columns[0]
        return df[col].str.lower().tolist()

    def get_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        schema = schema or self.profile.database
        df = self.execute_query(f"SELECT COUNT(*) as cnt FROM {schema}.{table_name}")
        return int(df["cnt"].iloc[0])

    def get_sample_data(
        self, table_name: str, sample_size: int = 100,
        schema: Optional[str] = None, pk: Optional[str] = None,
    ) -> pd.DataFrame:
        schema = schema or self.profile.database
        order = f"ORDER BY {pk}" if pk else "ORDER BY 1"
        return self.execute_query(
            f"SELECT * FROM {schema}.{table_name} {order} LIMIT {sample_size}"
        )

    def get_schema_info(self, table_name: str, schema: Optional[str] = None) -> List[SchemaColumn]:
        schema = schema or self.profile.database
        query = f"""
        SELECT column_name, data_type, is_nullable, ordinal_position,
               character_maximum_length, numeric_precision
        FROM information_schema.columns
        WHERE table_schema = '{schema}' AND table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        df = self.execute_query(query)
        results = []
        for _, row in df.iterrows():
            results.append(SchemaColumn(
                column_name=row["column_name"] if "column_name" in row.index else row["COLUMN_NAME"],
                data_type=row["data_type"] if "data_type" in row.index else row["DATA_TYPE"],
                is_nullable=str(row.get("is_nullable", row.get("IS_NULLABLE", "YES"))).upper() == "YES",
                ordinal_position=int(row.get("ordinal_position", row.get("ORDINAL_POSITION", 0))),
            ))
        return results


# ── SQLite ────────────────────────────────────────────────────────────────────

class SQLiteConnection(DatabaseConnection):

    def connect(self) -> bool:
        try:
            import sqlite3
            db_path = self.profile.database or self.profile.file_path or ":memory:"
            self.conn = sqlite3.connect(db_path)
            logger.info(f"Connected to SQLite: {db_path}")
            self.profile.is_connected = True
            return True
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            self.profile.is_connected = False
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.profile.is_connected = False

    def execute_query(self, query: str) -> pd.DataFrame:
        return pd.read_sql_query(query, self.conn)

    def get_table_list(self, schema: Optional[str] = None) -> List[str]:
        df = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return df["name"].tolist()

    def get_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        df = self.execute_query(f"SELECT COUNT(*) as cnt FROM [{table_name}]")
        return int(df["cnt"].iloc[0])

    def get_sample_data(
        self, table_name: str, sample_size: int = 100,
        schema: Optional[str] = None, pk: Optional[str] = None,
    ) -> pd.DataFrame:
        order = f"ORDER BY [{pk}]" if pk else "ORDER BY 1"
        return self.execute_query(
            f"SELECT * FROM [{table_name}] {order} LIMIT {sample_size}"
        )

    def get_schema_info(self, table_name: str, schema: Optional[str] = None) -> List[SchemaColumn]:
        df = self.execute_query(f"PRAGMA table_info([{table_name}])")
        results = []
        for _, row in df.iterrows():
            results.append(SchemaColumn(
                column_name=row["name"],
                data_type=row["type"],
                is_nullable=int(row["notnull"]) == 0,
                ordinal_position=int(row["cid"]),
            ))
        return results


# ── CSV / Excel File ──────────────────────────────────────────────────────────

class CSVDataSource(DatabaseConnection):
    """Treats a CSV or Excel file as a single-table data source."""

    def __init__(self, profile: ConnectionProfile):
        super().__init__(profile)
        self._dataframes: Dict[str, pd.DataFrame] = {}

    def connect(self) -> bool:
        try:
            path = self.profile.file_path
            if not path:
                raise ValueError("No file path provided")

            if path.endswith((".csv", ".tsv")):
                sep = "\t" if path.endswith(".tsv") else ","
                df = pd.read_csv(path, sep=sep)
                name = os.path.splitext(os.path.basename(path))[0]
                self._dataframes[name] = df
            elif path.endswith((".xlsx", ".xls")):
                xls = pd.ExcelFile(path)
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    self._dataframes[sheet_name] = df
            else:
                raise ValueError(f"Unsupported file type: {path}")

            logger.info(f"Loaded file: {path} ({len(self._dataframes)} tables)")
            self.profile.is_connected = True
            return True
        except Exception as e:
            logger.error(f"File load failed: {e}")
            self.profile.is_connected = False
            raise

    def load_dataframe(self, name: str, df: pd.DataFrame):
        """Programmatically add a DataFrame (used for Streamlit file uploads)."""
        self._dataframes[name] = df
        self.profile.is_connected = True

    def disconnect(self):
        self._dataframes.clear()
        self.profile.is_connected = False

    def execute_query(self, query: str) -> pd.DataFrame:
        raise NotImplementedError("CSV sources don't support SQL queries")

    def get_table_list(self, schema: Optional[str] = None) -> List[str]:
        return list(self._dataframes.keys())

    def get_row_count(self, table_name: str, schema: Optional[str] = None) -> int:
        return len(self._dataframes.get(table_name, pd.DataFrame()))

    def get_sample_data(
        self, table_name: str, sample_size: int = 100,
        schema: Optional[str] = None, pk: Optional[str] = None,
    ) -> pd.DataFrame:
        df = self._dataframes.get(table_name, pd.DataFrame())
        if pk and pk in df.columns:
            df = df.sort_values(by=pk.split(","))
        return df.head(sample_size)

    def get_schema_info(self, table_name: str, schema: Optional[str] = None) -> List[SchemaColumn]:
        df = self._dataframes.get(table_name, pd.DataFrame())
        results = []
        for i, col in enumerate(df.columns):
            results.append(SchemaColumn(
                column_name=col,
                data_type=str(df[col].dtype),
                is_nullable=df[col].isnull().any(),
                ordinal_position=i,
            ))
        return results


# ── Factory ───────────────────────────────────────────────────────────────────

def create_connection(profile: ConnectionProfile) -> DatabaseConnection:
    """Factory: create the appropriate connection adapter from a profile."""
    mapping = {
        DataSourceType.POSTGRESQL: PostgreSQLConnection,
        DataSourceType.REDSHIFT: PostgreSQLConnection,
        DataSourceType.MYSQL: MySQLConnection,
        DataSourceType.SNOWFLAKE: SnowflakeDBConnection,
        DataSourceType.SQLITE: SQLiteConnection,
        DataSourceType.CSV_FILE: CSVDataSource,
    }
    cls = mapping.get(profile.source_type)
    if cls is None:
        raise ValueError(f"Unsupported source type: {profile.source_type}")
    return cls(profile)
