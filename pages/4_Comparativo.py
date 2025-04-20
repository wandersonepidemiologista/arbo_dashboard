import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

from utils.auth import checar_login
checar_login()

st.title("⚖️ Comparativo: Afetados vs Controle")

df = load_data("data/arbo14vale24.parquet")

# Agrupar por tipo de estudo (afetado ou controle)
casos_por_estudo = df["estudo"].value_counts().reset_index()
casos_por_estudo.columns = ["Grupo", "Total de Casos"]
st.dataframe(casos_por_estudo)

fig = px.bar(casos_por_estudo, x="Grupo", y="Total de Casos", color="Grupo", text_auto=True)
st.plotly_chart(fig, use_container_width=True)

# Comparativo por doença
comparativo = df.groupby(["estudo", "ID_AGRAVO"]).size().reset_index(name="Casos")
fig2 = px.bar(comparativo, x="ID_AGRAVO", y="Casos", color="estudo", barmode="group")
st.plotly_chart(fig2, use_container_width=True)
