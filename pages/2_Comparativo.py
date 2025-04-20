import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data
from utils.auth import checar_login

checar_login()
st.set_page_config(layout="wide")
st.title("⚖️ Comparativo: Afetados vs Controle")

# --- Carregamento dos dados ---
df = load_data("data/arbo14vale24.parquet")

# --- Recodificação ---
df["estudovale"] = df["estudovale"].replace({1: "Caso", 2: "Controle", "1": "Caso", "2": "Controle"})

# --- Tabela simples por grupo ---
casos_por_grupo = df["estudovale"].value_counts().reset_index()
casos_por_grupo.columns = ["Grupo", "Total de Casos"]

st.markdown("### 📊 Total de Casos por Grupo")
st.dataframe(casos_por_grupo)

fig = px.bar(
    casos_por_grupo,
    x="Grupo",
    y="Total de Casos",
    color="Grupo",
    text_auto=True,
    title="Total de Casos - Caso vs Controle"
)
st.plotly_chart(fig, use_container_width=True)

# --- Comparativo por doença ---
st.markdown("### 🦠 Casos por Agravo e Grupo")
comparativo = df.groupby(["estudovale", "id_agravo"]).size().reset_index(name="Casos")

fig2 = px.bar(
    comparativo,
    x="id_agravo",
    y="Casos",
    color="estudovale",
    barmode="group",
    title="Distribuição por Doença e Grupo"
)
st.plotly_chart(fig2, use_container_width=True)
