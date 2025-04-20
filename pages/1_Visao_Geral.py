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
    st.subheader("📈 Taxa de Incidência por Ano e Categoria de Estudo")

    taxa_arbo = df.groupby(["NU_ANO", "estudo"])["ID_AGRAVO"].count().reset_index()
    taxa_arbo.rename(columns={"ID_AGRAVO": "taxa_arbo"}, inplace=True)

    fig_taxa = px.line(
        taxa_arbo,
        x="NU_ANO",
        y="taxa_arbo",
        color="estudo",
        markers=True,
        title="Taxa de Incidência de Arboviroses por Ano e Categoria de Estudo",
        labels={
            "NU_ANO": "Ano",
            "taxa_arbo": "Incidência (/100.000 hab)",
            "estudo": "Estudo"
        }
    )

    fig_taxa.update_layout(
        title_font=dict(size=16),
        margin=dict(l=40, r=40, t=80, b=40),
        legend_title="Estudo",
        height=500
    )

    fig_taxa.add_annotation(
    text="<i>Fonte: Sistema de Informação de Agravos de Notificação (Sinan) - atualizado em janeiro de 2025</i>",
    xref="paper", yref="paper",
    x=0, y=-0.2,
    showarrow=False,
    font=dict(size=10, color="gray")
    )

    st.plotly_chart(fig_taxa, use_container_width=True)

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
