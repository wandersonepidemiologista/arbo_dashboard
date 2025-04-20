import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_data

from utils.auth import checar_login
checar_login()

st.title("🕒 Distribuição Temporal dos Casos")

df = load_data("data/arbo14vale24.parquet")

df["mes_ano"] = df["DT_NOTIFIC"].dt.to_period("M").astype(str)
casos = df.groupby(["mes_ano", "ID_AGRAVO"]).size().reset_index(name="Casos")

fig = px.line(casos, x="mes_ano", y="Casos", color="ID_AGRAVO", markers=True)
st.plotly_chart(fig, use_container_width=True)
