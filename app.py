import streamlit as st
import pandas as pd
import plotly.express as px
import statsmodels.api as sm
from utils.data_loader import load_data

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

# ========= CONFIGURAÇÃO BÁSICA =========
st.set_page_config(page_title="ESP Brumadinho", layout="wide")

@st.cache_data
def load_data_cached():
    df = load_data("data/arbo14vale24.parquet")
    df['dt_notific'] = pd.to_datetime(df['dt_notific'])
    df['periodo'] = df['nu_ano'].astype(int).apply(lambda x: 'Pré-ESP' if x < 2019 else 'Pós-ESP')
    return df

df = load_data_cached()

# ========= SIDEBAR COM FILTROS =========
st.sidebar.title("🔍 Filtros")

# Período
periodo_sel = st.sidebar.multiselect("Período", options=df['periodo'].unique(), default=df['periodo'].unique())

# Ano
anos_sel = st.sidebar.slider("Ano da Notificação", int(df['nu_ano'].min()), int(df['nu_ano'].max()), (2014, 2024))

# Município
munic_sel = st.sidebar.multiselect("Município", options=sorted(df['nomedomunicipio'].unique()), default=None)

# Agravo
agravo_sel = st.sidebar.multiselect("Doença", options=df['classi_fin'].unique(), default=df['classi_fin'].unique())

# Sexo
sexo_sel = st.sidebar.multiselect("Sexo", options=df['cs_sexo'].unique(), default=["1.Feminino", "2.Masculino"])

# Raça
raca_sel = st.sidebar.multiselect("Raça/Cor", options=df['cs_raca'].unique(), default=df['cs_raca'].unique())

# Grupo de estudo
estudo_sel = st.sidebar.multiselect("Grupo (caso/controle)", options=df['estudovale'].dropna().unique(), default=df['estudovale'].dropna().unique())

# ========= FILTRAGEM =========
df_filtered = df[
    (df['periodo'].isin(periodo_sel)) &
    (df['nu_ano'].astype(int).between(anos_sel[0], anos_sel[1])) &
    (df['classi_fin'].isin(agravo_sel)) &
    (df['cs_sexo'].isin(sexo_sel)) &
    (df['cs_raca'].isin(raca_sel)) &
    (df['estudovale'].isin(estudo_sel))
]

if munic_sel:
    df_filtered = df_filtered[df_filtered['nomedomunicipio'].isin(munic_sel)]

# ========= NAVEGAÇÃO =========
paginas = ["Visão Geral", "Tempo", "Lugar", "Pessoa", "Download", "ITS / DiD"]
pagina = st.sidebar.radio("Navegação", paginas)

# ========= PÁGINA 1: VISÃO GERAL =========
if pagina == "Visão Geral":
    st.title("📊 Situação Epidemiológica Geral")
    st.metric("Casos Registrados", f"{len(df_filtered):,}")
    st.metric("Municípios", df_filtered['nomedomunicipio'].nunique())
    st.metric("Período", f"{anos_sel[0]} - {anos_sel[1]}")

    fig1 = px.histogram(df_filtered, x="nu_ano", color="classi_fin", barmode="group",
                        title="Casos por Ano e Tipo de Agravo")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 Tabela Síntese de Casos confirmados por Doença e Grupo de Estudo (com %)")
    df_filtered["estudo"] = df_filtered["estudo"].replace({1: "Caso", 2: "Controle"})
    tabela_sintese = df_filtered.groupby(["ID_AGRAVO", "estudo"]).size().unstack(fill_value=0)
    for col in ["Caso", "Controle"]:
        if col not in tabela_sintese.columns:
            tabela_sintese[col] = 0
    tabela_sintese["Total"] = tabela_sintese["Caso"] + tabela_sintese["Controle"]
    tabela_sintese["% Caso"] = (tabela_sintese["Caso"] / tabela_sintese["Total"] * 100).round(1)
    tabela_sintese["% Controle"] = (tabela_sintese["Controle"] / tabela_sintese["Total"] * 100).round(1)
    tabela_sintese = tabela_sintese.sort_values("Total", ascending=False)
    st.dataframe(tabela_sintese.drop(columns=["Total"]))

# ========= PÁGINA 2: TEMPO =========
elif pagina == "Tempo":
    st.title("⏳ Análise Temporal")
    fig = px.line(df_filtered.groupby(['nu_ano', 'classi_fin']).size().reset_index(name='casos'),
                  x='nu_ano', y='casos', color='classi_fin',
                  title="Série Temporal de Casos por Ano")
    st.plotly_chart(fig, use_container_width=True)

# ========= PÁGINA 3: LUGAR =========
elif pagina == "Lugar":
    st.title("🗺 Distribuição Espacial dos Casos")
    mapa = df_filtered.groupby("nomedomunicipio").size().reset_index(name="casos")
    fig = px.bar(mapa.sort_values("casos", ascending=False), x="nomedomunicipio", y="casos",
                 title="Casos por Município")
    st.plotly_chart(fig, use_container_width=True)

# ========= PÁGINA 4: PESSOA =========
elif pagina == "Pessoa":
    st.title("🧍 Perfil das Pessoas Afetadas")

    col1, col2 = st.columns(2)

    with col1:
        fig_sexo = px.pie(df_filtered, names='cs_sexo', title='Distribuição por Sexo')
        st.plotly_chart(fig_sexo, use_container_width=True)

    with col2:
        fig_idade = px.histogram(df_filtered, x="faixa_etaria", color="classi_fin",
                                 title="Distribuição por Faixa Etária")
        st.plotly_chart(fig_idade, use_container_width=True)

    fig_raca = px.pie(df_filtered, names='cs_raca', title='Distribuição por Raça/Cor')
    st.plotly_chart(fig_raca, use_container_width=True)

# ========= PÁGINA 5: DOWNLOAD =========
elif pagina == "Download":
    st.title("📥 Download dos Dados")
    st.write("Você pode baixar os dados filtrados abaixo:")
    st.download_button("📄 Baixar CSV", data=df_filtered.to_csv(index=False), file_name="dados_filtrados.csv")

# ========= PÁGINA 6: ITS / DID =========
elif pagina == "ITS / DiD":
    st.title("📈 ITS e Diferenças em Diferenças (DiD)")
    agravo_focus = st.selectbox("Selecione o Agravo", df_filtered['classi_fin'].unique())
    df_model = df_filtered[df_filtered['classi_fin'] == agravo_focus].copy()

    df_model['semana'] = pd.to_datetime(df_model['dt_notific'])
    df_model = df_model.set_index('semana')
    df_model = df_model.resample('W-MON').size().reset_index(name='casos')
    df_model['intervencao'] = (df_model['semana'] >= '2019-01-28').astype(int)
    df_model['tempo'] = range(1, len(df_model)+1)
    df_model['tempo_pos'] = df_model['tempo'] * df_model['intervencao']

    st.markdown("#### ITS com GLM (Poisson) por Semana Epidemiológica")
    import statsmodels.formula.api as smf
    glm_model = smf.glm("casos ~ tempo + intervencao + tempo_pos", data=df_model, family=sm.families.Poisson()).fit()
    st.write(glm_model.summary())

    st.markdown("#### Previsão com Intervalo de Confiança")
    df_model['preditos'] = glm_model.predict(df_model)
    pred = glm_model.get_prediction(df_model)
    pred_summary = pred.summary_frame(alpha=0.05)
    df_model['ic_inferior'] = pred_summary['mean_ci_lower']
    df_model['ic_superior'] = pred_summary['mean_ci_upper']

    import plotly.graph_objects as go
    fig_its = go.Figure()
    fig_its.add_trace(go.Scatter(x=df_model['semana'], y=df_model['casos'], mode='lines+markers', name='Observado'))
    fig_its.add_trace(go.Scatter(x=df_model['semana'], y=df_model['preditos'], mode='lines', name='Predito'))
    fig_its.add_trace(go.Scatter(x=df_model['semana'], y=df_model['ic_superior'], mode='lines', name='IC 95% Sup', line=dict(width=0), showlegend=False))
    fig_its.add_trace(go.Scatter(x=df_model['semana'], y=df_model['ic_inferior'], mode='lines', name='IC 95% Inf', fill='tonexty', line=dict(width=0), showlegend=False))
    fig_its.update_layout(title=f"ITS – {agravo_focus} (GLM Poisson + IC95%)", xaxis_title='Data', yaxis_title='Casos')
    st.plotly_chart(fig_its, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Diferenças em Diferenças (DiD)")
    df_did = df_filtered[df_filtered['classi_fin'] == agravo_focus].copy()
    df_did['ano'] = df_did['nu_ano'].astype(int)
    df_did['casos'] = 1
    df_did['grupo'] = df_did['estudovale'].apply(lambda x: 1 if x == '1.caso' else 0)
    df_did = df_did.groupby(['ano', 'grupo']).agg({'casos':'sum'}).reset_index()
    df_did['pos_esp'] = (df_did['ano'] >= 2019).astype(int)
    df_did['did'] = df_did['grupo'] * df_did['pos_esp']

    model_did = sm.OLS(df_did['casos'], sm.add_constant(df_did[['grupo', 'pos_esp', 'did']])).fit()
    st.subheader("Resultados do Modelo DiD")
    st.write(model_did.summary())

    fig_did = px.line(df_did, x="ano", y="casos", color=df_did['grupo'].map({1: "Caso", 0: "Controle"}),
                      title=f"Casos Anuais - {agravo_focus} (Comparação Caso vs Controle)")
    st.plotly_chart(fig_did, use_container_width=True)
