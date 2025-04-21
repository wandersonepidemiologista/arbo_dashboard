import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.formula.api as smf
import statsmodels.api as sm
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

# Navegação do Streamlit
paginas = ["Visão Geral", "Tempo", "Lugar", "Pessoa", "ITS / DiD", "Download", "Sobre"]
st.sidebar.title("📊 Navegação")
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
 
# ========= LUGAR =========
elif pagina == "Lugar":
    st.title("🗺 Distribuição Espacial dos Casos")

    # Adicionar filtro para o grupo de estudo (estudovale)
    grupo_estudo = st.selectbox("Selecione o Grupo de Estudo", options=df_filtered['estudovale'].unique())

    # Filtrar o dataframe de acordo com o grupo de estudo selecionado
    df_filtered_grupo = df_filtered[df_filtered['estudovale'] == grupo_estudo]

    # Criar a tabela com 'nomedomunicipio' e 'nu_ano' como colunas
    tabela_municipio_ano = df_filtered_grupo.groupby(['nomedomunicipio', 'nu_ano']).size().unstack(fill_value=0).reset_index()

    # Exibir a tabela com as colunas representando 'nu_ano' e as linhas os municípios
    st.markdown(f"### Tabela de Casos por Município e Ano - Grupo de Estudo: {grupo_estudo}")
    st.dataframe(tabela_municipio_ano)

    # Criação do gráfico de barras com o número de casos por município
    mapa = df_filtered_grupo.groupby("nomedomunicipio").size().reset_index(name="casos")
    fig = px.bar(mapa.sort_values("casos", ascending=False), x="nomedomunicipio", y="casos", title="Casos por Município")
    st.plotly_chart(fig, use_container_width=True)

# ========= PESSOA =========
elif pagina == "Pessoa":
    st.title("🧍 Perfil das Pessoas Afetadas")
    col1, col2 = st.columns(2)
    
    # Gráfico de Pizza por Sexo
    with col1:
        st.plotly_chart(px.pie(df_filtered, names='cs_sexo', title='Distribuição por Sexo'), use_container_width=True)
    
    # Gráfico de Histogram para Faixa Etária
    with col2:
        faixa_etaria_order = sorted(df_filtered['faixa_etaria'].unique())  # Ajuste conforme necessário
        st.plotly_chart(px.histogram(df_filtered, 
                                     x="faixa_etaria", 
                                     color="classi_fin", 
                                     title="Distribuição por Faixa Etária", 
                                     category_orders={"faixa_etaria": faixa_etaria_order}), 
                        use_container_width=True)

    # Gráfico de Barras por Escolaridade (cs_escol_n)
    escolaridade_counts = df_filtered['cs_escol_n'].value_counts().reset_index()
    escolaridade_counts.columns = ['cs_escol_n', 'count']
    fig_escolaridade = px.bar(escolaridade_counts, 
                              x="cs_escol_n", 
                              y="count", 
                              color="cs_escol_n", 
                              title="Distribuição por Escolaridade")
    
    st.plotly_chart(fig_escolaridade, use_container_width=True)
    
    # Gráfico de Barras por Raça/Cor (cs_raca)
    raca_counts = df_filtered['cs_raca'].value_counts().reset_index()
    raca_counts.columns = ['cs_raca', 'count']
    fig_raca = px.bar(raca_counts, 
                      x="cs_raca", 
                      y="count", 
                      color="cs_raca", 
                      title="Distribuição por Raça/Cor")
    
    st.plotly_chart(fig_raca, use_container_width=True)

    # Criando a Pirâmide Etária com Sexo
    piramide_etaria = df_filtered.groupby(['faixa_etaria', 'cs_sexo']).size().reset_index(name='count')
    
    # Agora, vamos dividir o sexo em duas colunas para fazer a pirâmide
    piramide_etaria_masculino = piramide_etaria[piramide_etaria['cs_sexo'] == '2.Masculino']
    piramide_etaria_feminino = piramide_etaria[piramide_etaria['cs_sexo'] == '1.Feminino']
    
    # Inverter a contagem dos homens para ficar no lado esquerdo da pirâmide
    piramide_etaria_masculino['count'] = -piramide_etaria_masculino['count']
    
    # Plotando o gráfico
    fig_piramide = px.bar(piramide_etaria_masculino,
                          y='faixa_etaria',
                          x='count',
                          color='cs_sexo',
                          orientation='h',
                          title="Pirâmide Etária por Sexo",
                          labels={'count': 'Número de Pessoas', 'faixa_etaria': 'Faixa Etária'},
                          color_discrete_map={'2.Masculino': 'blue', '1.Feminino': 'red'})
    
    # Adicionando as barras femininas do lado direito
    fig_piramide.add_bar(y=piramide_etaria_feminino['faixa_etaria'],
                         x=piramide_etaria_feminino['count'],
                         orientation='h',
                         name='Feminino',
                         marker_color='red')
    
    # Exibindo o gráfico
    st.plotly_chart(fig_piramide, use_container_width=True)

# ========= DOWNLOAD =========
elif pagina == "Download":
    st.title("📥 Download dos Dados")
    st.download_button("📄 Baixar CSV", data=df_filtered.to_csv(index=False), file_name="dados_filtrados.csv")

# ========= ITS / DiD =========
elif pagina == "ITS / DiD":
    st.title("📈 ITS (Interrupted Time Series Analysis) e Diferenças em Diferenças (DiD)")
    agravo_focus = st.selectbox("Selecione o Agravo", df_filtered['classi_fin'].unique())
    df_model = df_filtered[df_filtered['classi_fin'] == agravo_focus].copy()

    # Expander com mais conteúdo e ícone
    with st.expander("Detalhes sobre o modelo GLM Poisson", expanded=True, icon="📊"):
        st.write("A explicação detalhada dos coeficientes do modelo é a seguinte:")
        st.markdown("""
        - **Intercepto:** O valor base do modelo.
        - **Tempo:** Indica a mudança na incidência de casos ao longo do tempo.
        - **Intervenção:** Mostra o impacto das intervenções na redução dos casos de dengue.
        - **Tempo pós-intervenção:** Efeito observado após a implementação de intervenções.
        """)

    df_model['semana'] = pd.to_datetime(df_model['dt_notific'])
    df_model = df_model.set_index('semana')
    df_model = df_model.resample('W-MON').size().reset_index(name='casos')
    df_model['intervencao'] = (df_model['semana'] >= '2019-01-28').astype(int)
    df_model['tempo'] = range(1, len(df_model)+1)
    df_model['tempo_pos'] = df_model['tempo'] * df_model['intervencao']
    
    # Modelo GLM Poisson
    st.markdown("#### ITS com GLM (Generalized Linear Model) Poisson por Semana Epidemiológica")
    glm_model = smf.glm("casos ~ tempo + intervencao + tempo_pos", data=df_model, family=sm.families.Poisson()).fit()
    st.write(glm_model.summary())
   
    # Criando o expander com a explicação do modelo GLM Poisson por Semana Epidemiológica
    with st.expander("Interpretação do Modelo GLM Poisson para Chikungunya Confirmado", expanded=True, icon="📊"):
        st.markdown("""
        A análise de séries temporais interrompidas (ITS) utilizando o **modelo GLM Poisson** para os casos de **chikungunya confirmado** revela que o **rompimento da barragem** teve um impacto significativo na redução dos casos da doença. O coeficiente negativo para a variável **rompimento da barragem** (-0.7287) indica que o evento foi eficaz em reduzir a incidência de casos, com um valor de p (0.006) confirmando sua significância estatística. A variável **tempo** não apresentou um efeito significativo (coeficiente de -0.0022 e p = 0.482), sugerindo que a tendência natural dos casos de chikungunya não foi alterada ao longo do tempo antes do rompimento. No entanto, o coeficiente positivo e significativo para **tempo pós-rompimento da barragem** (0.0202, p < 0.001) sugere que, após o evento, houve um aumento considerável nos casos, o que pode indicar a necessidade de ações contínuas ou aprimoramento nas estratégias de controle. O modelo apresenta um **pseudo R-quadrado de 1.000**, indicando que o modelo ajusta bem os dados.
        """)

    # Criando o expander com a explicação do modelo GLM Poisson para casos de dengue
    with st.expander("Interpretação do Modelo GLM Poisson para Dengue", expanded=True, icon="📊"):
        st.markdown("""
        *A análise utilizando o modelo GLM Poisson para os casos de dengue revelou que o **rompimento da barragem** teve um impacto significativo na redução dos casos de dengue, evidenciado pelo coeficiente negativo da intervenção (-1.0123), indicando uma redução substancial nos casos durante o período da intervenção, com alta significância estatística (p < 0.001). Além disso, a variável **tempo** mostrou um efeito negativo (-0.0058), sugerindo uma diminuição contínua no número de casos ao longo do tempo, antes da intervenção. No entanto, o coeficiente positivo para **tempo pós-intervenção** (0.0087) indica que, após a intervenção, houve um aumento no número de casos, sugerindo que os efeitos da intervenção podem ter sido temporários ou que o controle foi insuficiente para evitar a reincidência. O modelo ajustou bem os dados, com um pseudo R-quadrado de 1.000, indicando que as variáveis explicativas foram adequadas para modelar a incidência de dengue durante o período analisado.*
        """)

    # Criando o expander com a explicação do modelo GLM Poisson para casos de Zika
    with st.expander("Interpretação do Modelo GLM Poisson para Zika", expanded=True, icon="📊"):
        st.markdown("""
        *A análise utilizando o modelo GLM Poisson para os casos de **Zika** revelou que o **rompimento da barragem** teve um impacto significativo na redução dos casos da doença, evidenciado pelo coeficiente negativo da intervenção (-3.9574), indicando uma redução substancial nos casos durante o período da intervenção, com alta significância estatística (p < 0.001). Além disso, a variável **tempo** apresentou um efeito negativo (-0.0716), sugerindo que, ao longo do tempo, o número de casos de Zika diminuiu consideravelmente, o que pode ser relacionado a fatores sazonais ou à implementação de medidas preventivas. No entanto, o coeficiente positivo para **tempo pós-rompimento da barragem** (0.0655) sugere que, após o evento, houve um aumento nos casos de Zika, indicando a necessidade de monitoramento contínuo e de estratégias sustentáveis de controle. O modelo apresentou um **pseudo R-quadrado de 0.9910**, o que indica que o modelo se ajusta muito bem aos dados e as variáveis explicativas são altamente relevantes para modelar a incidência de Zika durante o período analisado.*
        """)

    # Previsão com Intervalo de Confiança
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

    # Criando o expander com a explicação do modelo DiD para Chikungunya
    with st.expander("Interpretação do Modelo Diferenças em Diferenças (DiD) para Chikungunya", expanded=True, icon="📉"):
        st.markdown("""
        *A análise utilizando o modelo de **Diferenças em Diferenças (DiD)** para os casos de **chikungunya** revelou que, em termos gerais, o modelo tem um **R-quadrado de 0.130**, indicando que as variáveis explicativas conseguem explicar apenas 13% da variação nos casos de chikungunya. O coeficiente **constante** de 7.0000 sugere que, antes da intervenção, a taxa base de casos de chikungunya foi muito baixa, com uma **alta variabilidade** (p = 0.998). A variável **grupo** apresentou um coeficiente de 4.0000, mas também não foi significativa (p = 0.999), indicando que a diferença entre os grupos **caso** e **controle** não teve um impacto expressivo nos resultados. O coeficiente para **pos_esp** (4970.3333) foi positivo, mas com valor p de 0.257, indicando que, após o evento, a tendência de aumento nos casos não foi estatisticamente significativa. A variável **did** (interação entre grupo e pós-intervenção) teve um coeficiente negativo de -2524.0000, mas também não foi estatisticamente significativa (p = 0.678), sugerindo que a intervenção não teve um efeito significativo no aumento dos casos de chikungunya nos grupos em questão. O modelo apresenta uma **significância global baixa**, com o **F-statistic de 0.6975** e **p = 0.569**, o que indica que as variáveis explicativas não explicam bem a variabilidade nos casos de chikungunya.*
        """)


    # Criando o expander com a explicação do modelo DiD para Dengue
    with st.expander("Interpretação do Modelo Diferenças em Diferenças (DiD) para Dengue", expanded=True, icon="📉"):
        st.markdown("""
        *A análise utilizando o modelo de **Diferenças em Diferenças (DiD)** para os casos de **dengue** revelou que, em termos gerais, o modelo tem um **R-quadrado de 0.143**, indicando que as variáveis explicativas conseguem explicar apenas 14.3% da variação nos casos de dengue. O coeficiente **constante** de 6636.8000 sugere que, antes da intervenção, a taxa base de casos de dengue foi significativa, mas com uma **alta variabilidade** (p = 0.600). A variável **grupo** apresentou um coeficiente de 9063.0000, mas também não foi significativa (p = 0.613), indicando que a diferença entre os grupos **caso** e **controle** não teve um impacto expressivo nos resultados. O coeficiente para **pos_esp** (1.471e+04) foi positivo, mas com valor p de 0.394, indicando que, após o evento, a tendência de aumento nos casos não foi estatisticamente significativa. A variável **did** (interação entre grupo e pós-intervenção) teve um coeficiente positivo de 4520.1667, mas também não foi estatisticamente significativa (p = 0.852), sugerindo que a intervenção não teve um efeito significativo no aumento dos casos de dengue. O modelo apresenta uma **significância global baixa**, com o **F-statistic de 1.005** e **p = 0.414**, o que indica que as variáveis explicativas não explicam bem a variabilidade nos casos de dengue.*
        """)


    # Criando o expander com a explicação do modelo DiD para Zika
    with st.expander("Interpretação do Modelo Diferenças em Diferenças (DiD) para Zika", expanded=True, icon="📉"):
        st.markdown("""
        *A análise utilizando o modelo de **Diferenças em Diferenças (DiD)** para os casos de **Zika** revelou que, em termos gerais, o modelo tem um **R-quadrado de 0.420**, indicando que as variáveis explicativas conseguem explicar cerca de 42% da variação nos casos de Zika. O coeficiente **constante** de 171.0000 sugere que, antes da intervenção, a taxa base de casos era significativa, com uma significância estatística de p = 0.023. A variável **grupo** teve um coeficiente negativo (-131.6667) e não foi estatisticamente significativa (p = 0.133), indicando que a diferença entre os grupos **caso** e **controle** não foi suficientemente expressiva para influenciar os resultados. O coeficiente **pos_esp** (-168.0000), com valor p de 0.055, sugere que, após o evento de intervenção, houve uma tendência à redução nos casos de Zika, embora essa redução não tenha sido considerada totalmente significativa ao nível de 5%. A variável **did** (interação entre grupo e pós-intervenção) teve um coeficiente positivo (135.6667), mas não foi estatisticamente significativa (p = 0.223), sugerindo que a intervenção não teve um efeito estatisticamente significativo no aumento dos casos de Zika nos grupos em questão. O modelo apresenta uma **significância global baixa**, com o **F-statistic de 1.930** e **p = 0.203**, o que indica que as variáveis explicativas não explicam completamente a variabilidade nos casos de Zika.*
        """)



    fig_did = px.line(df_did, x="ano", y="casos", color=df_did['grupo'].map({1: "Caso", 0: "Controle"}), title=f"Casos Anuais - {agravo_focus} (Comparação Caso vs Controle)")
    st.plotly_chart(fig_did, use_container_width=True)

# ========= SOBRE =========

elif pagina == "Sobre":
    st.title("📖 Sobre o Dashboard")

    st.markdown("""
    Este dashboard está sendo desenvolvido para apresentar a análise dos dados da **Emergência em Saúde Pública (ESP)** de Brumadinho, com foco na avaliação do impacto do rompimento da barragem de rejeitos de **Brumadinho** sobre a saúde pública da região. O evento, ocorrido em 25 de janeiro de 2019, teve profundas consequências para os municípios localizados na bacia do Rio Paraopeba, afetando diretamente a saúde da população de 26 municípios. Este dashboard visa fornecer uma visão abrangente e interativa da evolução epidemiológica das doenças na área afetada, permitindo uma análise detalhada ao longo do tempo, no espaço geográfico e nas características demográficas das pessoas impactadas.

    **Objetivos:**
    
    O objetivo principal deste dashboard é oferecer uma análise detalhada da situação de saúde nos municípios afetados pelo rompimento da barragem, comparando-os com municípios não afetados, mas localizados nas mesmas **Regiões de Saúde** ou **Bacias Hidrográficas**. A análise é realizada para dois períodos: antes (2014–2018) e após (2019–2024) o evento de rompimento, com o intuito de:
    
    - Avaliar o impacto das intervenções de saúde pública implementadas após o rompimento da barragem, incluindo campanhas de controle e medidas emergenciais.
    - Identificar padrões epidemiológicos e mudanças nas taxas de doenças relacionadas ao evento.
    - Propor estratégias de preparação, resposta e recuperação para futuras emergências em saúde pública baseadas nos resultados observados.

    **Métodos Aplicados:**
    
    Para avaliar o impacto da ESP na saúde da população, foram aplicados métodos quantitativos avançados de análise de dados, entre eles:
    
    - **Análise de Séries Temporais Interrompidas (ITS)**: Essa técnica foi utilizada para analisar as séries temporais de doenças e agravos antes e depois do rompimento da barragem. A ITS permite verificar a **mudança nas tendências** de incidência de doenças após a intervenção, controlando fatores temporais e sazonais. O modelo **Generalized Linear Model (GLM)** com **distribuição de Poisson** foi aplicado para estimar a relação entre a intervenção e a incidência de doenças ao longo do tempo, considerando o efeito do **tempo pós-intervenção**.
    
    - **Diferenças em Diferenças (DiD)**: A técnica de **Diferenças em Diferenças** foi utilizada para comparar os indicadores de saúde dos municípios afetados pelo rompimento com aqueles não afetados, mas situados nas mesmas regiões de saúde. O método DiD permite estimar o efeito causal da intervenção, comparando as mudanças nos resultados de saúde nos dois grupos antes e depois do evento, controlando fatores de confusão.
    
    Ambas as técnicas são essenciais para entender os **efeitos diretos e indiretos** da emergência em saúde pública, permitindo analisar não apenas a incidência de doenças, mas também a eficácia das intervenções implementadas.

    **Desenho do Estudo:**
    
    **Tipo de Estudo:**
    Diferentes metodologias serão empregadas conforme a natureza da doença, agravo ou evento de saúde pública em análise. Em alguns casos, a abordagem descritiva será a única viável, caracterizando a situação segundo tempo, espaço e características populacionais. Em outros, será possível adotar métodos como estudos ecológicos, transversais e a análise de séries temporais interrompidas (Interrupted Time Series Analysis - ITSA), ferramenta que permite avaliar mudanças de tendência antes e após um evento específico. Além disso, o método de diferenças em diferenças (Difference-in-Differences) será utilizado como estratégia complementar, comparando a evolução de indicadores entre grupos expostos (municípios afetados) e não expostos (municípios de referência), possibilitando o controle de fatores de confusão ao longo do tempo.

    **Períodos Avaliados:**
    ● Antes: janeiro de 2014 a dezembro de 2018.  
    ● Depois: janeiro de 2019 a dezembro de 2024.  

    **Grupos de Comparação:**
    
    Em Minas Gerais, existem 853 municípios, com uma densidade demográfica de 35,02 habitantes por quilômetro quadrado e uma população estimada de 20.539.989 habitantes no Censo de 2022. Do total de municípios, 28% (239) integram a Bacia do Rio São Francisco, onde está situado o Rio Paraopeba, atingido pelo rompimento da barragem em 25 de janeiro de 2019. Destes, 10,9% (26) municípios foram diretamente afetados e estão situados nas áreas de abrangência de 5 (cinco) Regiões de Saúde, são elas: Betim, Sete Lagoas, Curvelo, Pará de Minas/Nova Serrana e Patos de Minas, totalizando 1.075.083 de habitantes. Entre as 89 Regiões de Saúde do estado, cinco foram selecionadas por abrigarem ao menos um dos 26 municípios impactados, somando 67 municípios (26 afetados e 41 não afetados).

    **Municípios afetados (n=26):**  
    Betim, Esmeraldas, Pará de Minas, Curvelo, Igarapé, Mateus Leme, Brumadinho, São Joaquim de Bicas, Juatuba, Pompéu, Três Marias, Paraopeba, Abaeté, Mário Campos, Felixlândia, Papagaios, Caetanópolis, Morada Nova de Minas, Florestal, Maravilhas, São Gonçalo do Abaeté, São José da Varginha, Paineiras, Pequi, Fortuna de Minas, Biquinhas.

    **Municípios não afetados nas mesmas regiões de saúde (n=41):**  
    Sete Lagoas, Patos de Minas, Nova Serrana, Pitangui, Corinto, Vazante, Presidente Olegário, Lagoa Formosa, Serra do Salitre, Prudente de Morais, Igaratinga, Capim Branco, Buenópolis, Guimarânia, Cordisburgo, Inimutaba, Bonfim, Baldim, Lagamar, Varjão de Minas, Santana de Pirapama, Guarda-Mor, Inhaúma, Jequitibá, Crucilândia, Rio Manso, Conceição do Pará, Piedade dos Gerais, Funilândia, Augusto de Lima, Cachoeira da Prata, Presidente Juscelino, Cruzeiro da Fortaleza, Quartel Geral, Leandro Ferreira, Onça de Pitangui, Morro da Garça, Santo Hipólito, Araçaí, Monjolos, Cedro do Abaeté.
    """)
    
    st.markdown("**Desenvolvimento: Wanderson Oliveira - Epidemiologista**")
    st.markdown("**Versão: beta 1 - NÃO DIVULGAR**")