import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data
from utils.auth import checar_login

checar_login()

st.title("🕒 Distribuição Temporal dos Casos")

# --- Carrega os dados
df = load_data("data/arbo14vale24.parquet")

# --- Sidebar: Filtro por grupo de estudo
st.sidebar.markdown("### Filtro por Grupo de Estudo")
estudos_disponiveis = df["estudo"].dropna().unique().tolist()
estudo_selecionado = st.sidebar.selectbox("Selecione o grupo:", ["Todos"] + estudos_disponiveis)
if estudo_selecionado != "Todos":
    df = df[df["estudo"] == estudo_selecionado]

# --- Visualização temporal
df["mes_ano"] = df["DT_NOTIFIC"].dt.to_period("M").astype(str)
casos = df.groupby(["mes_ano", "ID_AGRAVO"]).size().reset_index(name="Casos")

fig = px.line(casos, x="mes_ano", y="Casos", color="ID_AGRAVO", markers=True)
st.plotly_chart(fig, use_container_width=True)
