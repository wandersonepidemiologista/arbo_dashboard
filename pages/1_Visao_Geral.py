import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data
from utils.auth import checar_login

checar_login()
st.set_page_config(layout="wide")
st.title("📊 Visão Geral – Arboviroses")

# --- Carregamento dos dados ---
df = load_data("data/arbo14vale24.parquet")

# --- Ajustes de campos e tipos ---
df["estudovale"] = df["estudovale"].replace({1: "Caso", 2: "Controle", "1": "Caso", "2": "Controle"})
df["nu_ano"] = pd.to_numeric(df["nu_ano"], errors="coerce")
df["dt_notific"] = pd.to_datetime(df["dt_notific"], errors="coerce")
df["mes_ano"] = pd.to_datetime(df["dt_notific"].dt.to_period("M").astype(str))

# --- Filtros gerais na sidebar ---
st.sidebar.header("🎛️ Filtros")

# Filtro por grupo de estudo
estudo = st.sidebar.selectbox("Grupo", ["Todos"] + df["estudovale"].dropna().unique().tolist())
if estudo != "Todos":
    df = df[df["estudovale"] == estudo]

# Filtro por município
municipios = df["nomedomunicipio"].dropna().unique().tolist()
municipio_sel = st.sidebar.selectbox("Município", ["Todos"] + sorted(municipios))
if municipio_sel != "Todos":
    df = df[df["nomedomunicipio"] == municipio_sel]

# Filtro por ano (slider)
anos = df["nu_ano"].dropna().astype(int).sort_values().unique()
ano_min, ano_max = int(anos.min()), int(anos.max())
ano_range = st.sidebar.slider("Período (Ano)", ano_min, ano_max, (ano_min, ano_max))
df = df[df["nu_ano"].between(ano_range[0], ano_range[1])]

# --- Abas principais ---
tab1, tab2, tab3 = st.tabs(["⏳ Tempo", "🌍 Lugar", "👤 Pessoa"])

# --- Aba 1: Tempo ---
with tab1:
    st.subheader("⏳ Casos por Mês e Agravo")
    serie = df.groupby(["mes_ano", "id_agravo"]).size().reset_index(name="Casos")
    fig = px.line(serie, x="mes_ano", y="Casos", color="id_agravo", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# --- Aba 2: Lugar ---
with tab2:
    st.subheader("🌍 Casos por Município")
    lugar = df.groupby("nomedomunicipio").size().reset_index(name="Casos").sort_values("Casos", ascending=False)
    fig = px.bar(lugar, x="nomedomunicipio", y="Casos", title="Distribuição por Município")
    st.plotly_chart(fig, use_container_width=True)

# --- Aba 3: Pessoa ---
with tab3:
    st.subheader("👤 Perfil dos Casos")

    col1, col2 = st.columns(2)

    with col1:
        sexo = df["cs_sexo"].value_counts().reset_index()
        sexo.columns = ["Sexo", "Casos"]
        fig = px.pie(sexo, names="Sexo", values="Casos", title="Distribuição por Sexo")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        idade = df["faixa_etaria"].value_counts().sort_index().reset_index()
        idade.columns = ["Faixa Etária", "Casos"]
        fig = px.bar(idade, x="Faixa Etária", y="Casos", title="Distribuição por Faixa Etária")
        st.plotly_chart(fig, use_container_width=True)
