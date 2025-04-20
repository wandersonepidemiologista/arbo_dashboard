import streamlit as st

def login():
    st.sidebar.title("🔐 Acesso Restrito")
    user = st.sidebar.text_input("Usuário")
    password = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        if st.secrets["auth"].get(user) == password:
            st.session_state["autenticado"] = True
        else:
            st.error("Usuário ou senha inválidos.")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    login()
    st.stop()




import streamlit as st
import pandas as pd
from utils.data_loader import load_data
import plotly.express as px

st.set_page_config(page_title="Dashboard Arboviroses", layout="wide")

# --- Carregamento dos dados ---
DATA_PATH = "data/arbo14vale24.parquet"

df = load_data(DATA_PATH)

# --- Conversões e tratamento ---
df["DT_NOTIFIC"] = pd.to_datetime(df["DT_NOTIFIC"], errors="coerce")
df["DT_SIN_PRI"] = pd.to_datetime(df["DT_SIN_PRI"], errors="coerce")
df = df.dropna(subset=["NU_ANO", "ID_AGRAVO", "ID_MUNICIP"])  # garante filtros válidos

# --- Filtros (Sidebar) ---
st.sidebar.header("Filtros")

anos = sorted(df["NU_ANO"].dropna().unique())
anos_selecionados = st.sidebar.multiselect("Ano", anos, default=anos)

doencas = df["ID_AGRAVO"].dropna().unique()
doencas_selecionadas = st.sidebar.multiselect("Doença", doencas, default=doencas)

municipios = df["ID_MUNICIP"].dropna().unique()
municipios_selecionados = st.sidebar.multiselect("Municípios", municipios, default=municipios)

# --- Filtro por período de notificação ---
st.sidebar.subheader("Período de Notificação")
min_data = df["DT_NOTIFIC"].min()
max_data = df["DT_NOTIFIC"].max()
periodo = st.sidebar.date_input("Intervalo", [min_data, max_data], min_value=min_data, max_value=max_data)

# --- Aplicar Filtros ---
df_filtrado = df[
    (df["NU_ANO"].isin(anos_selecionados)) &
    (df["ID_AGRAVO"].isin(doencas_selecionadas)) &
    (df["ID_MUNICIP"].isin(municipios_selecionados)) &
    (df["DT_NOTIFIC"] >= pd.to_datetime(periodo[0])) &
    (df["DT_NOTIFIC"] <= pd.to_datetime(periodo[1]))
]

# --- Visualização ---
st.title("📊 Dashboard de Arboviroses – Brumadinho e Região")

st.subheader("Prévia dos dados filtrados")
st.dataframe(df_filtrado.head())

st.markdown("### Casos por Ano e Doença")
casos_por_ano = df_filtrado.groupby(["NU_ANO", "ID_AGRAVO"]).size().reset_index(name="Casos")
fig = px.bar(casos_por_ano, x="NU_ANO", y="Casos", color="ID_AGRAVO", barmode="group")
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Evolução dos Casos")
evolucao = df_filtrado["EVOLUCAO"].value_counts().reset_index()
evolucao.columns = ["Evolução", "Total de Casos"]
evolucao = evolucao.sort_values(by="Total de Casos", ascending=False)
st.dataframe(evolucao)
