import streamlit as st
import pandas as pd
from utils.data_loader import load_data

st.title("⏳ Análise de Intervalos entre Datas")

df = load_data("data/arbo14vale24.parquet")

# Conversão segura de datas (caso ainda não tenha sido feita no loader)
df["DT_NOTIFIC"] = pd.to_datetime(df["DT_NOTIFIC"], errors="coerce")
df["DT_ENCERRA"] = pd.to_datetime(df["DT_ENCERRA"], errors="coerce")
df["DT_SIN_PRI"] = pd.to_datetime(df["DT_SIN_PRI"], errors="coerce")

# Remove linhas com datas faltantes antes do cálculo
df_temp = df.dropna(subset=["DT_NOTIFIC", "DT_ENCERRA", "DT_SIN_PRI"]).copy()

# Diferenças de tempo em dias
df_temp["dias_sintomas_ate_notif"] = (df_temp["DT_NOTIFIC"] - df_temp["DT_SIN_PRI"]).dt.days
df_temp["dias_notif_ate_encerramento"] = (df_temp["DT_ENCERRA"] - df_temp["DT_NOTIFIC"]).dt.days

st.markdown("### ⏱ Dias entre sintomas e notificação")
st.dataframe(df_temp["dias_sintomas_ate_notif"].describe())

st.markdown("### ⏱ Dias entre notificação e encerramento")
st.dataframe(df_temp["dias_notif_ate_encerramento"].describe())
