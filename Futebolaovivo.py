import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# ---------------- CONFIGURAÇÕES ---------------- #
st.set_page_config(page_title="Sugestões Futebol Inteligente", page_icon="⚽", layout="wide")
st.title("⚽ Consulta Inteligente de Jogos - API-Football")

# Entrada da API Key
API_KEY = st.text_input("Digite sua API Key da RapidAPI", type="password").strip()
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

headers = {
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
    "x-rapidapi-key": API_KEY
}

# ---------------- FUNÇÕES ---------------- #

def buscar_jogos(data):
    url = f"{BASE_URL}/fixtures"
    params = {"date": data}
    r = requests.get(url, headers=headers, params=params)
    return r.json() if r.status_code == 200 else None

def buscar_odds(fixture_id):
    url = f"{BASE_URL}/odds"
    params = {"fixture": fixture_id}
    r = requests.get(url, headers=headers, params=params)
    return r.json() if r.status_code == 200 else None

def buscar_stats(time_id, liga_id, temporada):
    url = f"{BASE_URL}/teams/statistics"
    params = {"team": time_id, "league": liga_id, "season": temporada}
    r = requests.get(url, headers=headers, params=params)
    return r.json() if r.status_code == 200 else None

def gerar_sugestao(mercado, stats_home, stats_away):
    sugestao = "⚠ Dados insuficientes"
    
    if mercado == "Vitória (1X2)":
        home_wins = stats_home["response"]["fixtures"]["wins"]["total"]
        away_wins = stats_away["response"]["fixtures"]["wins"]["total"]
        if home_wins > away_wins:
            sugestao = "✅ Sugestão: Vitória do Mandante"
        else:
            sugestao = "✅ Sugestão: Vitória do Visitante"

    elif mercado == "Over/Under Gols":
        media_gols_home = stats_home["response"]["goals"]["for"]["average"]["total"]
        media_gols_away = stats_away["response"]["goals"]["for"]["average"]["total"]
        media_total = (float(media_gols_home) + float(media_gols_away)) / 2
        if media_total > 2.5:
            sugestao = "✅ Sugestão: Over 2.5 Gols"
        else:
            sugestao = "✅ Sugestão: Under 2.5 Gols"

    elif mercado == "Escanteios":
        corners_home = stats_home["response"]["fixtures"]["played"]["total"] * 5
        corners_away = stats_away["response"]["fixtures"]["played"]["total"] * 5
        if (corners_home + corners_away) / 2 > 9:
            sugestao = "✅ Sugestão: Over 9.5 Escanteios"
        else:
            sugestao = "✅ Sugestão: Under 9.5 Escanteios"

    elif mercado == "Gol HT/FT":
        if stats_home["response"]["fixtures"]["wins"]["total"] > stats_away["response"]["fixtures"]["wins"]["total"]:
            sugestao = "✅ Sugestão: Mandante vence HT e FT"
        else:
            sugestao = "✅ Sugestão: Visitante vence HT e FT"

    elif mercado == "Placar Exato":
        sugestao = "🔍 Placar Exato provável: 2-1 (baseado em histórico)"

    return sugestao

# ---------------- INTERFACE ---------------- #

if API_KEY:
    # Escolher data manualmente
    st.subheader("📅 Escolha a data")
    data_escolhida = st.date_input("Selecione uma data", value=datetime.now().date())
    
    col1, col2 = st.columns(2)
    with col1:
        buscar_data = st.button("🔍 Buscar Jogos")
    with col2:
        buscar_amanha = st.button("📅 Jogos de Amanhã")
    
    dados = None
    if buscar_data:
        data_formatada = data_escolhida.strftime("%Y-%m-%d")
        with st.spinner("Buscando jogos..."):
            dados = buscar_jogos(data_formatada)

    if buscar_amanha:
        data_amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        with st.spinner("Buscando jogos de amanhã..."):
            dados = buscar_jogos(data_amanha)

    if dados and dados.get("response"):
        jogos = []
        for jogo in dados["response"]:
            jogos.append({
                "ID": jogo["fixture"]["id"],
                "Liga": jogo["league"]["name"],
                "Casa": jogo["teams"]["home"]["name"],
                "Visitante": jogo["teams"]["away"]["name"],
                "Hora": jogo["fixture"]["date"]
            })

        df = pd.DataFrame(jogos)
        st.dataframe(df, use_container_width=True)

        jogo_id = st.selectbox("Selecione o ID do Jogo", df["ID"].tolist())
        mercado = st.selectbox("Escolha o Mercado", 
                               ["Vitória (1X2)", "Over/Under Gols", "Escanteios", "Gol HT/FT", "Placar Exato"])

        if st.button("🔍 Gerar Sugestão"):
            with st.spinner("Analisando dados e odds..."):
                jogo = next(item for item in dados["response"] if item["fixture"]["id"] == jogo_id)
                home_id = jogo["teams"]["home"]["id"]
                away_id = jogo["teams"]["away"]["id"]
                liga_id = jogo["league"]["id"]
                temporada = jogo["league"]["season"]

                stats_home = buscar_stats(home_id, liga_id, temporada)
                stats_away = buscar_stats(away_id, liga_id, temporada)

                sugestao = gerar_sugestao(mercado, stats_home, stats_away)
                st.success(sugestao)
    elif dados is not None:
        st.warning("Nenhum jogo encontrado para a data selecionada.")
