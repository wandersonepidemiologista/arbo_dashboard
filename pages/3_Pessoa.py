import streamlit as st
import pandas as pd
from utils.data_loader import load_data

st.title("👤 Perfil dos Casos")

df = load_data("data/arbo14vale24.parquet")

st.markdown("### Por Sexo")
sexo = df["CS_SEXO"].value_counts().reset_index()
sexo.columns = ["Sexo", "Casos"]
st.dataframe(sexo)

st.markdown("### Por Escolaridade")
escol = df["CS_ESCOL_N"].value_counts().reset_index()
escol.columns = ["Escolaridade", "Casos"]
st.dataframe(escol)

st.markdown("### Por Faixa Etária")
faixa = df["faixa_etaria"].value_counts().sort_index().reset_index()
faixa.columns = ["Faixa Etária", "Casos"]
st.dataframe(faixa)
