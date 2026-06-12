# DataValidator Pro — Enterprise Data Quality & Migration Validator

DataValidator Pro is a generalized, high-performance **Data Validation & Quality Assurance Tool** featuring a premium, **Streamlit UI** and a backward-compatible **CLI**. 

It enables developers, data engineers, and QA analysts to compare, validate, and audit datasets across heterogeneous sources — including **PostgreSQL, MySQL, Snowflake, Redshift, SQLite, and uploaded CSV/Excel files** — using cell-level row hashing, statistical profiles, schema diffs, and customizable SQL tests.

---

## 🎯 Key Features

### 1. UI & Visualization (Streamlit App)
- **Interactive Dashboard**: Rich, glassmorphic dark-theme UI featuring real-time, table-by-table validation progress bars and live log streaming.
- **Visual Analytics**: Interactive Plotly charts showing table status distributions, historical quality/pass-rate trends, and database statistics.
- **Drill-down Inspector**: Investigate specific mismatches, null frequencies, and schema variations in detail.

### 2. Validation Engine Metrics (7 Core Types)
- 🔐 **Row Hash Validation**: MD5 hash-based per-row cellular matching across common columns with configurable sampling sizes.
- #️⃣ **Row Count Comparison**: High-speed row count audits with user-defined threshold tolerances.
- 🏗️ **Schema Difference**: Column-by-column matches of data types, naming, column presence, and nullability flags.
- 🕳️ **Null Analysis**: Metric comparison for null value percentages per column across sources.
- 👯 **Duplicate Detection**: Auto-detect duplicated key records in source and target databases.
- 📊 **Statistical Profiling**: Automatic aggregate profile audits (min, max, mean, distinct count) for numeric and string fields.
- ✏️ **Custom SQL Matching**: Compare arbitrary SQL queries side-by-side.

### 3. Multi-source Adapters
- **Relational Databases**: PostgreSQL, MySQL, SQLite, and Amazon Redshift.
- **Cloud Warehouses**: Snowflake (supporting standard authentication, MFA, and browser SSO).
- **Tabular Files**: Direct CSV, TSV, XLS, and XLSX file comparisons.

### 4. Comprehensive Reporting
- Automatically packages validation runs into a downloadable **ZIP bundle**.
- **Excel Report**: Multi-sheet summary, detailed records, highlighted failures, and aggregate run statistics.
- **Table-wise CSV Folders**: Organized folders for each table containing validation logs and differences.

---

## 🏗️ Project Architecture

```
Data Validation Tool/
├── app.py                          # Streamlit UI Entry Point
├── data_migration_validator.py     # Legacy CLI Entry Point
├── requirements.txt                # Dependencies
├── core/
│   ├── connections.py              # Database/File Adapter Interfaces
│   ├── validators.py               # Validation Strategies Engine
│   ├── normalizers.py              # Data Cleansing & Hash Normalizer
│   ├── reports.py                  # Excel/CSV/ZIP Reports Generator
│   └── models.py                   # Shared Dataclasses & Enums
├── ui/
│   ├── styles.py                   # CSS Custom Themes
│   ├── components.py               # Styled UI Widgets
│   ├── page_home.py                # Landing Dashboard
│   ├── page_connections.py         # Connection Builder Page
│   ├── page_validate.py            # Validation Runner Page
│   ├── page_results.py             # Results Analytics Page
│   ├── page_history.py             # Run Log & Trend Page
│   └── page_settings.py            # Tolerance & Normalization Settings
└── config/
    └── credentials.json            # Saved DB profiles (Git-ignored)
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- Virtual environment setup

### 2. Installation & Setup
Create a virtual environment and install the required dependencies:

```bash
# Clone the repository
cd "Data Validation Tool"

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Streamlit App
Start the interactive UI dashboard:
```bash
streamlit run app.py
```

### 3a. Quick Sandbox Testing (No Database Server Required)
If you don't have active database credentials and want to test the entire validation flow:
1. Go to the **Data Connections** page in the sidebar.
2. Scroll to the bottom and click the **⚡ Generate & Load Demo SQLite Databases** button.
3. This creates two local SQLite databases (`demo_source.db` & `demo_target.db`) with test data and saves a primary key mapping configuration file (`tables/demo_aggregation.json`).
4. Navigate to the **Run Validation** page.
5. In **Table Selection**, select **Filter by configured table group**, select the **demo** group from the dropdown, and click **🚀 Start Validation**.
6. Switch to the **Results Dashboard** page to view metric summaries, interactive charts, table drill-downs, cell mismatch logs, and download Excel/ZIP report bundles!


### 4. Running the CLI (Backward-compatible)
Verify the CLI works or execute validations directly from your terminal:
```bash
# Display help and arguments
python data_migration_validator.py --help

# Run standard table group validation for tenant "chcsno"
python data_migration_validator.py -t chcsno
```

---

## ⚙️ Configuration & Settings

- **Database Settings**: Set up database connections directly in the **Data Connections** page of the UI or configure `config/credentials.json`.
- **Normalization Preferences**: Configure custom float rounding, case-sensitive matching, and text trim options via the **Settings** tab.
- **Validation History**: Runs are saved locally to `config/validation_history.json`, allowing you to reload previous validation runs and view performance charts over time.

---

## 🔑 Syncing Table Primary Keys (100+ Tables)

To perform per-row hashing (`ROW_HASH`), the validation engine requires the primary key(s) of each table to sort and align rows correctly. When validating **hundreds of tables**, you can avoid entering them manually by syncing them from a local JSON configuration file.

### 1. Configuration File Format
Create a JSON file inside the `tables/` directory. The structure is a simple key-value map where the key is the **table name** (lowercase) and the value is the **comma-separated primary key column(s)**.

Example (`tables/standard_aggregation.json`):
```json
{
  "users": "user_id",
  "orders": "order_id, customer_id",
  "claims": "claim_id",
  "transactions": "txn_id"
}
```

### 2. How to Sync in Streamlit UI (Runtime)
1. Navigate to the **Run Validation** page.
2. In the **Table Selection** section, expand **Primary Key Mapping (optional)**.
3. Select your config file from the dropdown under **📂 Sync primary keys from a local configuration file:**.
4. The app will parse the JSON and immediately load all primary key configurations.
5. If needed, you can write overrides or append new ones in the **Manual PK Overrides / Additions** text area below the dropdown.

### 3. How to Sync in the CLI
The CLI parses mapping files matching `tables/{group}_aggregation.json` or `tables/{group}.json` automatically. Pass the group name using the `-g` / `--group` argument:
```bash
# Loads mapping from tables/claims_aggregation.json
python data_migration_validator.py -t chcsno -g claims
```

---
