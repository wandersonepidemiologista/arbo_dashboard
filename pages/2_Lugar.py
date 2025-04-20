import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

from utils.auth import checar_login
checar_login()

st.title("🗺️ Distribuição Geográfica dos Casos")

df = load_data("data/arbo14vale24.parquet")

# Total de casos por município
mapa_df = df.groupby("ID_MUNICIP").size().reset_index(name="Casos")

# Renomear para facilitar leitura
mapa_df.columns = ["cod_mun", "Casos"]

# Plotar mapa com Plotly Choropleth se você tiver geojson dos municípios
st.warning("Para ativar o mapa, precisamos de um arquivo GeoJSON com os municípios. Posso te ajudar a adicionar.")

# Enquanto isso, visual simples:
fig = px.bar(mapa_df.sort_values("Casos", ascending=False), x="cod_mun", y="Casos")
st.plotly_chart(fig, use_container_width=True)
