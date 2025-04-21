import streamlit as st
import pandas as pd
import plotly.express as px
import os

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
    try:
        df = pd.read_parquet("data/arbo.parquet")
    except Exception as e:
        st.error(f"Erro ao carregar Parquet: {e}")
        st.stop()
    df['dt_notific'] = pd.to_datetime(df['dt_notific'])
    df['periodo'] = df['nu_ano'].astype(int).apply(lambda x: 'Pré-ESP' if x < 2019 else 'Pós-ESP')
    ordem_etaria = [
        "01.0-4 anos", "02.5-9 anos", "03.10 A 14 anos", "04.15-19 anos", "05.20-29 anos",
        "06.30-39 anos", "07.40-49 anos", "08.50-59 anos", "09.60-69 anos", "10.70-79 anos", "11.80+ anos"
    ]
    df['faixa_etaria'] = pd.Categorical(df['faixa_etaria'], categories=ordem_etaria, ordered=True)
    return df

df = load_data_cached()

# ========= SIDEBAR COM FILTROS =========
logo_path = os.path.join(os.getcwd(), 'data', 'logo.png')  # Caminho da logo
st.sidebar.image(logo_path, width=200)  # Exibe a logo no sidebar
st.sidebar.title("🔐 Acesso Restrito")
st.sidebar.markdown("Selecione os filtros desejados para a análise.")
estudo_sel = st.sidebar.multiselect("Grupo (caso/controle)", options=df['estudovale'].dropna().unique(), default=df['estudovale'].dropna().unique())
periodo_sel = st.sidebar.multiselect("Período", options=df['periodo'].unique(), default=df['periodo'].unique())
anos_sel = st.sidebar.slider("Ano da Notificação", int(df['nu_ano'].min()), int(df['nu_ano'].max()), (2014, 2024))
munic_sel = st.sidebar.multiselect("Município", options=sorted(df['nomedomunicipio'].unique()), default=None)
agravo_sel = st.sidebar.multiselect("Doença", options=df['classi_fin'].unique(), default=df['classi_fin'].unique())
sexo_sel = st.sidebar.multiselect("Sexo", options=df['cs_sexo'].unique(), default=["1.Feminino", "2.Masculino"])
raca_sel = st.sidebar.multiselect("Raça/Cor", options=df['cs_raca'].unique(), default=df['cs_raca'].unique())

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

if df_filtered.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# ========= NAVEGAÇÃO =========
paginas = ["Visão Geral", "Tempo", "Lugar", "Pessoa", "Download", "ITS / DiD"]
pagina = st.radio("Escolha uma aba", paginas, horizontal=True)

# ========= VISÃO GERAL =========
if pagina == "Visão Geral":
    st.title("📊 Situação Epidemiológica Geral")
    st.markdown("Bem-vindo ao dashboard de análise da Emergência em Saúde Pública (ESP) de Brumadinho.")
    st.metric("Casos Registrados", f"{len(df_filtered):,}")
    st.metric("Municípios", df_filtered['nomedomunicipio'].nunique())
    st.metric("Período", f"{anos_sel[0]} - {anos_sel[1]}")

    fig1 = px.histogram(df_filtered, x="nu_ano", color="classi_fin", barmode="group", title="Casos por Ano e Tipo de Agravo")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📊 Tabela Síntese de Casos confirmados por Doença e Grupo de Estudo (com %)")
    df_filtered["estudo"] = df_filtered["estudo"].replace({1: "Caso", 2: "Controle"})
    tabela = df_filtered.groupby(["id_agravo", "estudo"]).size().unstack(fill_value=0)
    for col in ["Caso", "Controle"]:
        if col not in tabela.columns:
            tabela[col] = 0
    tabela["Total"] = tabela["Caso"] + tabela["Controle"]
    tabela["% Caso"] = (tabela["Caso"] / tabela["Total"] * 100).round(1)
    tabela["% Controle"] = (tabela["Controle"] / tabela["Total"] * 100).round(1)
    st.dataframe(tabela.drop(columns=["Total"]))

# ========= TEMPO =========
elif pagina == "Tempo":
    st.title("⏳ Análise Temporal")
    fig = px.bar(df_filtered.groupby(['nu_ano', 'classi_fin']).size().reset_index(name='casos'),
                  x='nu_ano', y='casos', color='classi_fin', title="Série Temporal de Casos por Ano")
    st.plotly_chart(fig, use_container_width=True)
 
with st.expander("SAIBA+"):
    st.write('''
        O rompimento da barragem ocorreu em janeiro de 2019. Se você selecionar o Período ***Pré-ESP***, significa que verá
        o período de 2014 a 2018, antes do rompimento. Se selecionar o Período ***Pós-ESP***, verá o período de 2019 a 2024.
        O gráfico mostra a série temporal de casos confirmados por ano e tipo de agravo. Você pode observar a evolução dos casos ao longo do tempo.
        O gráfico de barras apresenta a contagem de casos confirmados por ano, permitindo uma análise visual clara da tendência temporal.
    ''')

# ========= LUGAR =========
elif pagina == "Lugar":
    st.title("🗺 Distribuição Espacial dos Casos")
    
    # Correct indentation here
    mapa = df_filtered.groupby("nomedomunicipio").size().reset_index(name="casos")
    fig = px.bar(mapa.sort_values("casos", ascending=False), x="nomedomunicipio", y="casos", title="Casos por Município")
    
    st.plotly_chart(fig, use_container_width=True)

# ========= PESSOA =========
elif pagina == "Pessoa":
    st.title("🧍 Perfil das Pessoas Afetadas")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(df_filtered, names='cs_sexo', title='Distribuição por Sexo'), use_container_width=True)
    with col2:
        # Ordenando as faixas etárias de forma crescente (ajustando para a ordem)
        faixa_etaria_order = sorted(df_filtered['faixa_etaria'].unique())  # Ajuste conforme necessário
        st.plotly_chart(px.histogram(df_filtered, 
                                     x="faixa_etaria", 
                                     color="classi_fin", 
                                     title="Distribuição por Faixa Etária", 
                                     category_orders={"faixa_etaria": faixa_etaria_order}), 
                        use_container_width=True)
    st.plotly_chart(px.pie(df_filtered, names='cs_raca', title='Distribuição por Raça/Cor'), use_container_width=True)

# ========= DOWNLOAD =========
elif pagina == "Download":
    st.title("📥 Download dos Dados")
    st.download_button("📄 Baixar CSV", data=df_filtered.to_csv(index=False), file_name="dados_filtrados.csv")

# ========= ITS / DiD =========
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
    glm_model = smf.glm("casos ~ tempo + intervencao + tempo_pos", data=df_model, family=sm.families.Poisson()).fit()
    st.write(glm_model.summary())

    st.markdown("#### Previsão com Intervalo de Confiança")
    df_model['preditos'] = glm_model.predict(df_model)
    pred = glm_model.get_prediction(df_model)
    pred_summary = pred.summary_frame(alpha=0.05)
    df_model['ic_inferior'] = pred_summary['mean_ci_lower']
    df_model['ic_superior'] = pred_summary['mean_ci_upper']

    fig_its = go.Figure()
    fig_its.add_trace(go.Scatter(x=df_model['semana'], y=df_model['casos'], mode='lines+markers', name='Observado'))
    fig_its.add_trace(go.Scatter(x=df_model['semana'], y=df_model['preditos'], mode='lines', name='Predito'))
    fig_its.add_trace(go.Scatter(x=df_model['semana'], y=df_model['ic_superior'], mode='lines', line=dict(width=0), name='IC Sup', showlegend=False))
    fig_its.add_trace(go.Scatter(x=df_model['semana'], y=df_model['ic_inferior'], mode='lines', fill='tonexty', line=dict(width=0), name='IC Inf', showlegend=False))
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

    fig_did = px.line(df_did, x="ano", y="casos", color=df_did['grupo'].map({1: "Caso", 0: "Controle"}), title=f"Casos Anuais - {agravo_focus} (Comparação Caso vs Controle)")
    st.plotly_chart(fig_did, use_container_width=True)
