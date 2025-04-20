import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data
from utils.auth import checar_login

checar_login()
st.set_page_config(layout="wide")
st.title("👥 Pirâmide Etária dos Casos")

df = load_data("data/arbo14vale24.parquet")

# Recodificar campo estudo para filtros
df["estudo"] = df["estudo"].replace({1: "Caso", 2: "Controle"})

# Filtros
st.sidebar.header("Filtros")
agravos = df["ID_AGRAVO"].dropna().unique().tolist()
agravo_sel = st.sidebar.selectbox("Selecione o agravo", ["Todos"] + agravos)

estudos = df["estudo"].dropna().unique().tolist()
estudo_sel = st.sidebar.selectbox("Selecione o grupo de estudo", ["Todos"] + estudos)

# Aplicar filtros
if agravo_sel != "Todos":
    df = df[df["ID_AGRAVO"] == agravo_sel]

if estudo_sel != "Todos":
    df = df[df["estudo"] == estudo_sel]

# Agrupar para pirâmide
df = df[df["CS_SEXO"].isin(["M", "F"])]  # remove dados sem sexo

# Agrupa os dados para a pirâmide
piramide = (
    df.groupby(["faixa_etaria", "CS_SEXO"])
    .size()
    .reset_index(name="Casos")
)

# Negativar homens para formar pirâmide
piramide["Casos"] = piramide.apply(
    lambda row: -row["Casos"] if row["CS_SEXO"] == "M" else row["Casos"], axis=1
)

# Gráfico
fig = px.bar(
    piramide,
    x="Casos",
    y="faixa_etaria",
    color="CS_SEXO",
    orientation="h",
    labels={"CS_SEXO": "Sexo", "faixa_etaria": "Faixa Etária"},
    title="Distribuição Etária por Sexo",
)

fig.update_layout(
    xaxis_title="Número de Casos",
    yaxis_title="Faixa Etária",
    bargap=0.1,
)

st.plotly_chart(fig, use_container_width=True)
st.markdown(
    """
    A pirâmide etária é uma representação gráfica que mostra a distribuição da população por faixa etária e sexo. 
    Neste gráfico, os homens estão representados em valores negativos para criar a forma de pirâmide.
    """
)
st.markdown(
    """
    **Fontes:**
    - [Plotly Express](https://plotly.com/python/plotly-express/)
    - [Pandas](https://pandas.pydata.org/)
    """
)
st.markdown(
    """
    **Nota:** A pirâmide etária é uma ferramenta útil para visualizar a estrutura etária de uma população e pode ajudar na identificação de tendências demográficas.
    """
)
st.markdown(
    """
    **Observação:** Os dados utilizados para criar esta pirâmide etária foram extraídos de um conjunto de dados de saúde pública e podem não refletir a população geral.
    """
)