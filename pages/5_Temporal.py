import streamlit as st
import pandas as pd
from utils.data_loader import load_data

st.title("⏳ Análise de Intervalos entre Datas")

df = load_data("data/arbo14vale24.parquet")

# Diferença entre datas
df["dias_sintomas_ate_notif"] = (df["DT_NOTIFIC"] - df["DT_SIN_PRI"]).dt.days
df["dias_notif_ate_encerramento"] = (df["DT_ENCERRA"] - df["DT_NOTIFIC"]).dt.days

st.markdown("### ⏱ Dias entre sintomas e notificação")
st.dataframe(df["dias_sintomas_ate_notif"].describe())

st.markdown("### ⏱ Dias entre notificação e encerramento")
st.dataframe(df["dias_notif_ate_encerramento"].describe())
