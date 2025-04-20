import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data
from utils.auth import checar_login

checar_login()
st.set_page_config(layout="wide")
st.title("📊 Visão Geral – Arboviroses")

df = load_data("data/arbo14vale24.parquet")
df["estudo"] = df["estudo"].replace({1: "Caso", 2: "Controle"})
df["NU_ANO"] = pd.to_numeric(df["NU_ANO"], errors="coerce").astype("Int64")

# Filtros
st.sidebar.header("🎛️ Filtros")
estudo = st.sidebar.selectbox("Grupo", ["Todos"] + df["estudo"].dropna().unique().tolist())
municipio = st.sidebar.selectbox("Município", ["Todos"] + sorted(df["ID_MUNICIP"].dropna().unique().tolist()))
anos = df["NU_ANO"].dropna().sort_values().unique()
ano_range = st.sidebar.slider("Período (Ano)", int(anos.min()), int(anos.max()), (int(anos.min()), int(anos.max())))

if estudo != "Todos":
    df = df[df["estudo"] == estudo]
if municipio != "Todos":
    df = df[df["ID_MUNICIP"] == municipio]
df = df[df["NU_ANO"].between(ano_range[0], ano_range[1])]

# Tabs
tab1, tab2, tab3 = st.tabs(["⏳ Tempo", "🌍 Lugar", "👤 Pessoa"])

# --- TAB TEMPO ---
with tab1:
    st.subheader("⏳ Casos por Mês e Agravo")
    df["mes_ano"] = pd.to_datetime(df["DT_NOTIFIC"].dt.to_period("M").astype(str))
    linha = df.groupby(["mes_ano", "ID_AGRAVO"]).size().reset_index(name="Casos")
    fig = px.line(linha, x="mes_ano", y="Casos", color="ID_AGRAVO", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# --- TAB LUGAR ---
with tab2:
    st.subheader("🌍 Casos por Município")
    lugar = df.groupby("ID_MUNICIP").size().reset_index(name="Casos").sort_values("Casos", ascending=False)
    fig = px.bar(lugar, x="ID_MUNICIP", y="Casos")
    st.plotly_chart(fig, use_container_width=True)

# --- TAB PESSOA ---
with tab3:
    st.subheader("👤 Perfil dos Casos")

    col1, col2 = st.columns(2)

    with col1:
        sexo = df["CS_SEXO"].value_counts().reset_index()
        sexo.columns = ["Sexo", "Casos"]
        fig = px.pie(sexo, names="Sexo", values="Casos", title="Distribuição por Sexo")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        idade = df["faixa_etaria"].value_counts().sort_index().reset_index()
        idade.columns = ["Faixa Etária", "Casos"]
        fig = px.bar(idade, x="Faixa Etária", y="Casos", title="Distribuição por Faixa Etária")
        st.plotly_chart(fig, use_container_width=True)

