import pandas as pd

def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_parquet(filepath)
    df["DT_NOTIFIC"] = pd.to_datetime(df["DT_NOTIFIC"], errors="coerce")
    df["DT_SIN_PRI"] = pd.to_datetime(df["DT_SIN_PRI"], errors="coerce")
    return df
