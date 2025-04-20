import pandas as pd

def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["DT_NOTIFIC", "DT_SIN_PRI"], low_memory=False)
    return df
