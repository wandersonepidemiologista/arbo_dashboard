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
st.title("📊 Dashboard de Arboviroses")
st.markdown("Navegue pelas seções no menu lateral: **Tempo**, **Lugar**, e **Pessoa**.")
