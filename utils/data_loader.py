import pandas as pd

def extrair_idade(x):
    try:
        x_str = str(int(float(x)))  # cobre casos como 'nan', float, etc.
        if x_str.startswith("4"):
            return int(x_str[1:])
    except:
        return None

def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_parquet(filepath)
    df["DT_NOTIFIC"] = pd.to_datetime(df["DT_NOTIFIC"], errors="coerce")
    df["DT_SIN_PRI"] = pd.to_datetime(df["DT_SIN_PRI"], errors="coerce")
    df["idade_anos"] = df["NU_IDADE_N"].apply(extrair_idade)
    df["faixa_etaria"] = pd.cut(
        df["idade_anos"],
        bins=[0, 10, 20, 40, 60, 80, 120],
        labels=["0–10", "11–20", "21–40", "41–60", "61–80", "81+"],
        right=False
    )
    return df
