import streamlit as st
import requests
from datetime import date
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Consulta API Futebol", page_icon="⚽", layout="wide")

st.title("⚽ Consulta Inteligente de Jogos - API Futebol")

# Entrada da API Key
API_KEY = st.text_input("Digite sua API Key", type="password")

# Base URL
BASE_URL = "https://api.api-futebol.com.br/v1"

# Funções para acessar API
def get_jogos_por_data(api_key, data):
    url = f"{BASE_URL}/partidas/{data}"
    headers = {"Authorization": f"Bearer {api_key}"}
    return requests.get(url, headers=headers)

def get_ao_vivo(api_key):
    url = f"{BASE_URL}/ao-vivo"
    headers = {"Authorization": f"Bearer {api_key}"}
    return requests.get(url, headers=headers)

def get_campeonatos(api_key):
    url = f"{BASE_URL}/campeonatos"
    headers = {"Authorization": f"Bearer {api_key}"}
    return requests.get(url, headers=headers)

# Escolha da data
data_escolhida = st.date_input("📅 Escolha a data dos jogos", value=date.today())

# Opção para buscar
col1, col2 = st.columns(2)
with col1:
    buscar_data = st.button("🔍 Buscar Jogos por Data")
with col2:
    buscar_ao_vivo = st.button("🎥 Jogos Ao Vivo")

# Checa API Key
if not API_KEY:
    st.warning("Insira sua API Key para continuar.")
else:
    # Exibe campeonatos para filtro
    campeonatos = get_campeonatos(API_KEY)
    if campeonatos.status_code == 200:
        lista_camps = campeonatos.json()
        nomes_camps = {camp['campeonato_id']: camp['nome'] for camp in lista_camps}
        camp_id = st.selectbox("Filtrar por Campeonato", options=[0] + list(nomes_camps.keys()), format_func=lambda x: "Todos" if x == 0 else nomes_camps[x])
    else:
        st.error("Erro ao buscar campeonatos.")

    # Buscar jogos por data
    if buscar_data:
        with st.spinner("Buscando jogos..."):
            response = get_jogos_por_data(API_KEY, data_escolhida.strftime("%Y-%m-%d"))
            if response.status_code == 200:
                partidas = response.json()
                # Filtrar por campeonato
                if camp_id != 0:
                    partidas = [p for p in partidas if p['campeonato']['campeonato_id'] == camp_id]
                if partidas:
                    st.success(f"✅ {len(partidas)} jogos encontrados para {data_escolhida}")
                    dados = []
                    for p in partidas:
                        dados.append({
                            "Campeonato": p['campeonato']['nome'],
                            "Casa": p['casa']['nome_popular'],
                            "Visitante": p['visitante']['nome_popular'],
                            "Placar": p['placar'],
                            "Status": p['status'],
                            "Hora": p['data_realizacao'] + " " + p['hora_realizacao']
                        })
                    df = pd.DataFrame(dados)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhum jogo encontrado para os filtros.")
            elif response.status_code == 401:
                st.error("❌ API Key inválida.")
            elif response.status_code == 429:
                st.warning("⚠️ Limite diário atingido.")
            else:
                st.error(f"Erro {response.status_code}: {response.text}")

    # Buscar jogos ao vivo
    if buscar_ao_vivo:
        with st.spinner("Carregando jogos ao vivo..."):
            response = get_ao_vivo(API_KEY)
            if response.status_code == 200:
                partidas = response.json()
                if partidas:
                    st.success(f"🎥 {len(partidas)} jogos ao vivo agora!")
                    dados = []
                    for p in partidas:
                        dados.append({
                            "Campeonato": p['campeonato']['nome'],
                            "Casa": p['casa']['nome_popular'],
                            "Visitante": p['visitante']['nome_popular'],
                            "Placar": p['placar'],
                            "Status": p['status']
                        })
                    df = pd.DataFrame(dados)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Nenhum jogo ao vivo no momento.")
            else:
                st.error(f"Erro {response.status_code}: {response.text}")
