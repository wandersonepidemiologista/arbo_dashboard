import streamlit as st
import pandas as pd
import altair as alt
from utils.data_loader import load_data
from utils.auth import checar_login

checar_login()
st.set_page_config(layout="wide")
st.title("📌 Distribuição de Casos Confirmados – Linha do Tempo e Histograma")

df = load_data("data/arbo14vale24.parquet")

# Recodifica estudo: 1 → Caso, 2 → Controle
df["estudo"] = df["estudo"].replace({1: "Caso", 2: "Controle"})

# --- SIDEBAR: Filtros
st.sidebar.header("🎛️ Filtros")

# Estudo
estudos_disponiveis = df["estudo"].dropna().unique().tolist()
estudo_selecionado = st.sidebar.selectbox("Grupo de Estudo", ["Todos"] + estudos_disponiveis)
if estudo_selecionado != "Todos":
    df = df[df["estudo"] == estudo_selecionado]

# Município
municipios = df["ID_MUNICIP"].dropna().unique().tolist()
municipio_sel = st.sidebar.selectbox("Município", ["Todos"] + sorted(municipios))
if municipio_sel != "Todos":
    df = df[df["ID_MUNICIP"] == municipio_sel]

# Período de anos
anos = df["NU_ANO"].dropna().astype(int).sort_values().unique().tolist()
ano_min, ano_max = min(anos), max(anos)
intervalo = st.sidebar.slider("Intervalo de Anos", ano_min, ano_max, (ano_min, ano_max))
df = df[(df["NU_ANO"] >= intervalo[0]) & (df["NU_ANO"] <= intervalo[1])]

# --- HISTOGRAMA DE CASOS POR ANO E AGRAVO
st.subheader("📊 Histograma por Ano de Notificação e Agravo")
histograma = (
    df.groupby(["NU_ANO", "ID_AGRAVO"])
    .size()
    .reset_index(name="Casos")
)

bar_chart = alt.Chart(histograma).mark_bar().encode(
    x=alt.X("NU_ANO:O", title="Ano"),
    y=alt.Y("Casos:Q", title="Número de Casos"),
    color="ID_AGRAVO:N",
    tooltip=["NU_ANO", "ID_AGRAVO", "Casos"]
).properties(height=400)

st.altair_chart(bar_chart, use_container_width=True)

# --- LINHA DO TEMPO COM ANOTAÇÕES
st.subheader("📈 Linha do Tempo com Anotações")
df["mes_ano"] = pd.to_datetime(df["DT_NOTIFIC"].dt.to_period("M").astype(str))
serie = df.groupby(["mes_ano", "ID_AGRAVO"]).size().reset_index(name="Casos")

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

st.altair_chart((linha + anotacoes).interactive(), use_container_width=True)
