import streamlit as st
import requests
from datetime import date
import pandas as pd

st.set_page_config(page_title="Consulta API Futebol", page_icon="⚽", layout="wide")
st.title("⚽ Consulta Inteligente de Jogos - API Futebol")

# Entrada da API Key
API_KEY = st.text_input("Digite sua API Key", type="password").strip()
BASE_URL = "https://api.api-futebol.com.br/v1"

# Funções
def validar_api(api_key):
    url = f"{BASE_URL}/campeonatos"
    headers = {"Authorization": f"Bearer {api_key}"}
    return requests.get(url, headers=headers)

def get_status(api_key):
    url = f"{BASE_URL}/me"
    headers = {"Authorization": f"Bearer {api_key}"}
    return requests.get(url, headers=headers)

# Testa a chave automaticamente
if API_KEY:
    with st.spinner("Validando sua API Key..."):
        resp = validar_api(API_KEY)
        if resp.status_code == 200:
            st.success("✅ API Key válida!")
            status = get_status(API_KEY)
            if status.status_code == 200:
                dados = status.json()
                st.info(f"Plano: {dados['plano']} | Requisições hoje: {dados['requisicoes']['usadas']}/{dados['requisicoes']['limite']}")
        elif resp.status_code == 401:
            st.error("❌ API Key inválida.")
        else:
            st.warning(f"Erro {resp.status_code}: {resp.text}")

# Apenas se a chave for válida, mostra opções
if API_KEY and resp.status_code == 200:
    # Escolha de data
    data_escolhida = st.date_input("📅 Escolha a data dos jogos", value=date.today())
    col1, col2 = st.columns(2)
    with col1:
        buscar_data = st.button("🔍 Buscar Jogos por Data")
    with col2:
        buscar_ao_vivo = st.button("🎥 Jogos Ao Vivo")

    # Buscar dados se usuário clicar
    def buscar(endpoint):
        headers = {"Authorization": f"Bearer {API_KEY}"}
        return requests.get(BASE_URL + endpoint, headers=headers)

    if buscar_data:
        with st.spinner("Buscando jogos..."):
            resp = buscar(f"/partidas/{data_escolhida.strftime('%Y-%m-%d')}")
            if resp.status_code == 200:
                partidas = resp.json()
                if partidas:
                    dados = []
                    for p in partidas:
                        dados.append({
                            "Campeonato": p['campeonato']['nome'],
                            "Casa": p['casa']['nome_popular'],
                            "Visitante": p['visitante']['nome_popular'],
                            "Placar": p['placar'],
                            "Status": p['status']
                        })
                    st.dataframe(pd.DataFrame(dados), use_container_width=True)
                else:
                    st.info("Nenhum jogo encontrado.")
            else:
                st.error(f"Erro {resp.status_code}")
