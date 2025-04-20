import duckdb
import os

INPUT_FILE = "data/arbo14vale24.parquet"
OUTPUT_FILE = "data/arbo14vale24_clean.parquet"

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

duckdb.sql(f"""
    COPY (SELECT * FROM '{INPUT_FILE}')
    TO '{OUTPUT_FILE}' (FORMAT PARQUET)
""")

print(f"✅ Novo arquivo gerado: {OUTPUT_FILE}")