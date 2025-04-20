import streamlit as st

def checar_login():
    if "autenticado" not in st.session_state or not st.session_state["autenticado"]:
        st.error("🔐 Acesso não autorizado. Faça login na página principal.")
        st.stop()
