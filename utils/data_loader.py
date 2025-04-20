import pandas as pd

def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_parquet(filepath)
    df["DT_NOTIFIC"] = pd.to_datetime(df["DT_NOTIFIC"], errors="coerce")
    df["DT_SIN_PRI"] = pd.to_datetime(df["DT_SIN_PRI"], errors="coerce")
    df["idade_anos"] = df["NU_IDADE_N"].apply(lambda x: int(str(x)[1:]) if str(x).startswith("4") else None)
    df["faixa_etaria"] = pd.cut(df["idade_anos"], bins=[0, 10, 20, 40, 60, 80, 120],
                                labels=["0–10", "11–20", "21–40", "41–60", "61–80", "81+"], right=False)
    return df
