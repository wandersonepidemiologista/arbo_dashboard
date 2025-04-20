import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data
from utils.auth import checar_login

checar_login()
st.set_page_config(layout="wide")
st.title("👥 Pirâmide Etária dos Casos")

# --- Carrega os dados ---
df = load_data("data/arbo14vale24.parquet")

# Recodificar campo estudo para filtros
df["estudovale"] = df["estudovale"].replace({1: "Caso", 2: "Controle", "1": "Caso", "2": "Controle"})

# Filtros na sidebar
st.sidebar.header("🎛️ Filtros")

agravos = df["id_agravo"].dropna().unique().tolist()
agravo_sel = st.sidebar.selectbox("Selecione o agravo", ["Todos"] + sorted(agravos))

estudos = df["estudovale"].dropna().unique().tolist()
estudo_sel = st.sidebar.selectbox("Selecione o grupo de estudo", ["Todos"] + sorted(estudos))

# Aplicar filtros
if agravo_sel != "Todos":
    df = df[df["id_agravo"] == agravo_sel]

if estudo_sel != "Todos":
    df = df[df["estudovale"] == estudo_sel]

# Apenas registros com sexo válido
df = df[df["cs_sexo"].isin(["M", "F"])]

# Agrupar os dados para a pirâmide
piramide = (
    df.groupby(["faixa_etaria", "cs_sexo"])
    .size()
    .reset_index(name="Casos")
)

# Ordenar faixas etárias
ordem = ["0–10", "11–20", "21–40", "41–60", "61–80", "81+"]
piramide["faixa_etaria"] = pd.Categorical(piramide["faixa_etaria"], categories=ordem, ordered=True)

# Negativar os homens
piramide["Casos"] = piramide["Casos"].astype(int)
piramide["Casos"] = piramide.apply(
    lambda row: -row["Casos"] if row["cs_sexo"] == "M" else row["Casos"], axis=1
)

# Gráfico
fig = px.bar(
    piramide,
    x="Casos",
    y="faixa_etaria",
    color="cs_sexo",
    orientation="h",
    labels={"cs_sexo": "Sexo", "faixa_etaria": "Faixa Etária"},
    title="Distribuição Etária por Sexo"
)

fig.update_layout(
    xaxis_title="Número de Casos",
    yaxis_title="Faixa Etária",
    bargap=0.1
)

st.plotly_chart(fig, use_container_width=True)

# Informações complementares
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
