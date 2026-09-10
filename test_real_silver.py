from google.cloud import bigquery

from src.transform.silver.bronze_reader import (
    read_bronze_data,
)

from src.transform.silver.validator import (
    validate_bronze_data,
)

from src.transform.silver.indicators import (
    calculate_indicators,
)

from src.transform.silver.silver_loader import (
    load_silver_data,
)


client = bigquery.Client()


# ==========================================================
# 1. READ BRONZE
# ==========================================================

bronze_df = read_bronze_data(
    client=client,
    symbol="360ONE",
    start_date="2024-03-18",
    end_date="2024-03-18",
)

print("Bronze rows:", len(bronze_df))


# ==========================================================
# 2. VALIDATE
# ==========================================================

valid_df, rejected_df = validate_bronze_data(
    bronze_df
)

print("Valid rows:", len(valid_df))
print("Rejected rows:", len(rejected_df))


# ==========================================================
# 3. CALCULATE INDICATORS
# ==========================================================

silver_df = calculate_indicators(
    valid_df
)

print("Silver dataframe rows:", len(silver_df))
print("Silver dataframe columns:", len(silver_df.columns))


# ==========================================================
# 4. LOAD TO SILVER
# ==========================================================

loaded_rows = load_silver_data(
    client=client,
    df=silver_df,
)

print("Rows processed by loader:", loaded_rows)