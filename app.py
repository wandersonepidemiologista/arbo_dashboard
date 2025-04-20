import streamlit as st
from utils.data_loader import load_data

# --- Carregamento dos dados ---
df = load_data("data/arbo14vale24.parquet")

# --- Login simples com st.secrets ---
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

# --- Configuração da página ---
st.set_page_config(page_title="Arboviroses - Brumadinho", layout="wide")
st.title("📊 Dashboard de Arboviroses – Brumadinho e Região")
st.markdown("---")

# 📌 Introdução ao dashboard
st.markdown("""
Este dashboard tem como objetivo monitorar e analisar os casos de **Dengue**, **Zika** e **Chikungunya** notificados em municípios afetados pelo rompimento da barragem em **Brumadinho (MG)**, bem como em municípios controle da mesma região de saúde.

A análise é baseada em dados extraídos do **SINAN (Sistema de Informação de Agravos de Notificação)**, contendo mais de **570 mil registros** entre os anos de **2013 a 2024**.
""")

st.markdown("### 🦟 Sobre as Arboviroses Monitoradas")
st.markdown("""
- **Dengue**: doença viral transmitida por mosquitos do gênero *Aedes*, com sintomas como febre alta, dores no corpo e manchas vermelhas.
- **Zika**: além de sintomas leves, a infecção durante a gravidez pode causar microcefalia e outras malformações congênitas.
- **Chikungunya**: caracteriza-se por febre alta e intensas dores nas articulações, que podem durar por semanas ou meses.

Todas são transmitidas principalmente pelo **Aedes aegypti**, vetor urbano que prolifera em ambientes com água parada.
""")

st.markdown("### 🌍 Contexto Epidemiológico")
st.markdown("""
Após o desastre ambiental de **Brumadinho em janeiro de 2019**, diversas áreas foram impactadas em sua infraestrutura, saneamento e cobertura de saúde — o que pode ter influenciado na dinâmica das arboviroses nas regiões expostas.

Este painel permite comparar municípios **afetados diretamente** com municípios **controle**, utilizando filtros e visualizações dinâmicas por **tempo**, **espaço**, **perfil dos casos** e **evolução clínica**.
""")

st.markdown("### 🧭 Como navegar")
st.markdown("""
Use o menu lateral para acessar:

- **Tempo** – tendência temporal de casos por mês e ano  
- **Lugar** – distribuição geográfica por município  
- **Pessoa** – perfil sociodemográfico dos casos  
- **Comparativo** – análise entre grupos afetados e controle  
- **Temporal** – intervalos clínicos: sintomas, notificação e encerramento  
- **Pirâmide** – estrutura etária por sexo e agravo
""")

st.markdown("📌 *Este painel é uma ferramenta exploratória, não substituindo análises oficiais das autoridades de saúde.*")

# --- Tabela síntese por agravo e grupo de estudo ---
# Recodificar o campo estudo
df["estudo"] = df["estudo"].replace({1: "Caso", 2: "Controle"})

# Tabela cruzada: ID_AGRAVO vs estudo
tabela_sintese = df.groupby(["ID_AGRAVO", "estudo"]).size().unstack(fill_value=0)

# Garante que as colunas existam mesmo se algum grupo estiver ausente
for col in ["Caso", "Controle"]:
    if col not in tabela_sintese.columns:
        tabela_sintese[col] = 0

# Total por agravo
tabela_sintese["Total"] = tabela_sintese["Caso"] + tabela_sintese["Controle"]

# Percentuais
tabela_sintese["% Caso"] = (tabela_sintese["Caso"] / tabela_sintese["Total"] * 100).round(1)
tabela_sintese["% Controle"] = (tabela_sintese["Controle"] / tabela_sintese["Total"] * 100).round(1)

# Ordenar por total
tabela_sintese = tabela_sintese.sort_values("Total", ascending=False)

# Exibir
st.markdown("### 📊 Tabela Síntese de Casos confirmados por Doença e Grupo de Estudo (com %)")
st.dataframe(tabela_sintese.drop(columns=["Total"])) 
