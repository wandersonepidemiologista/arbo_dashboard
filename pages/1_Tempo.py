import streamlit as st
import pandas as pd
import altair as alt
from utils.data_loader import load_data
from utils.auth import checar_login

checar_login()

st.title("📌 Casos com Destaques Temporais (Altair)")

df = load_data("data/arbo14vale24.parquet")

# Recodifica estudo: 1 → Caso, 2 → Controle
df["estudo"] = df["estudo"].replace({
    1: "Caso",
    2: "Controle"
})

# --- Sidebar: Filtro por estudo
st.sidebar.markdown("### Filtro por Grupo de Estudo")
estudos_disponiveis = df["estudo"].dropna().unique().tolist()
estudo_selecionado = st.sidebar.selectbox("Selecione o grupo:", ["Todos"] + estudos_disponiveis)
if estudo_selecionado != "Todos":
    df = df[df["estudo"] == estudo_selecionado]

# --- Preparar dados para gráfico
df["mes_ano"] = df["DT_NOTIFIC"].dt.to_period("M").astype(str)
df["mes_ano"] = pd.to_datetime(df["mes_ano"])  # Altair precisa de datetime real

serie = df.groupby(["mes_ano", "ID_AGRAVO"]).size().reset_index(name="Casos")

# --- Gráfico base
linha = (
    alt.Chart(serie)
    .mark_line(point=True)
    .encode(
        x="mes_ano:T",
        y="Casos:Q",
        color="ID_AGRAVO:N",
        tooltip=["mes_ano:T", "ID_AGRAVO", "Casos"]
    )
)

# --- Anotações (exemplo adaptado)
eventos = [
    ("2019-01-25", "Rompimento da barragem em Brumadinho"),
    ("2024-03-01", "Pico de dengue em 2024"),
    ("2015-06-01", "Primeiros casos de Zika")
]

anotacoes_df = pd.DataFrame(eventos, columns=["date", "evento"])
anotacoes_df["date"] = pd.to_datetime(anotacoes_df["date"])
anotacoes_df["y"] = 0

anotacoes = (
    alt.Chart(anotacoes_df)
    .mark_text(text="⬇", size=20, dy=-10)
    .encode(
        x="date:T",
        y=alt.value(0),
        tooltip=["evento"]
    )
)

# --- Exibir
st.altair_chart((linha + anotacoes).interactive(), use_container_width=True)
