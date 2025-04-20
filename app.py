import streamlit as st

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

# --- Página inicial ---
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

# Certifique-se de que o campo estudo está recodificado
df["estudo"] = df["estudo"].replace({1: "Caso", 2: "Controle"})

# Agrupar por ID_AGRAVO (doença) e grupo de estudo
tabela_sintese = df.groupby(["ID_AGRAVO", "estudo"]).size().unstack(fill_value=0)

# Mostrar a tabela
st.markdown("### 📊 Tabela Síntese de Casos por Doença e Grupo de Estudo")
st.dataframe(tabela_sintese)