import streamlit as st
import requests

st.title("Teste da API Futebol")

API_KEY = st.text_input("Digite sua API Key", type="password")
endpoint = "https://api.api-futebol.com.br/v1/campeonatos"

if st.button("Testar API"):
    if API_KEY:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(endpoint, headers=headers)

        if response.status_code == 200:
            st.success("✅ API funcionando! Campeonatos encontrados:")
            campeonatos = response.json()
            for camp in campeonatos:
                st.write(f"{camp['campeonato_id']} - {camp['nome']} ({camp['edicao_atual']['temporada']})")
        elif response.status_code == 401:
            st.error("❌ Erro 401: Chave inválida ou expirada")
        elif response.status_code == 429:
            st.warning("⚠️ Erro 429: Limite diário atingido")
        else:
            st.error(f"Erro {response.status_code}: {response.text}")
    else:
        st.warning("Insira sua API Key para testar")
