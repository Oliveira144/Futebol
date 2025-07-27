import streamlit as st
import requests

API_KEY = "live_faa23ea1b1e8fa03d43634048d455e"
BASE_URL = "https://api.api-futebol.com.br/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

st.title("App de Análise de Futebol com Api-Futebol")

# 1) Buscar competições
@st.cache_data(ttl=3600)
def get_competitions():
    url = f"{BASE_URL}/campeonatos"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        st.error("Erro ao buscar campeonatos.")
        return []

competitions = get_competitions()
competitions_dict = {c['nome_popular']: c['campeonato_id'] for c in competitions}

if not competitions_dict:
    st.stop()

selected_competition_name = st.selectbox("Escolha o Campeonato", list(competitions_dict.keys()))
selected_competition_id = competitions_dict[selected_competition_name]

# 2) Buscar rodadas do campeonato selecionado
@st.cache_data(ttl=600)
def get_rounds(campeonato_id):
    url = f"{BASE_URL}/campeonatos/{campeonato_id}/rodadas"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        st.error("Erro ao buscar rodadas.")
        return []

rounds = get_rounds(selected_competition_id)

round_options = [r['nome'] for r in rounds]
if not round_options:
    st.warning("Campeonato sem rodadas disponíveis.")
    st.stop()

selected_round_name = st.selectbox("Escolha a Rodada", round_options)
selected_round = next(r for r in rounds if r["nome"] == selected_round_name)

# 3) Buscar partidas da rodada
@st.cache_data(ttl=600)
def get_games(campeonato_id, rodada):
    url = f"{BASE_URL}/campeonatos/{campeonato_id}/rodadas/{rodada}/jogos"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        st.error("Erro ao buscar jogos.")
        return []

games = get_games(selected_competition_id, selected_round_name)

if not games:
    st.warning("Nenhum jogo encontrado nessa rodada.")
    st.stop()

games_dict = {f"{g['time_mandante']['nome_popular']} x {g['time_visitante']['nome_popular']}": g for g in games}
selected_game_name = st.selectbox("Escolha a Partida", list(games_dict.keys()))
selected_game = games_dict[selected_game_name]

# 4) Mostrar informações básicas da partida
st.subheader(f"Jogo: {selected_game_name}")
st.write(f"Data: {selected_game['data_realizacao']}")
st.write(f"Local: {selected_game.get('estadio', {}).get('nome_popular', 'N/A')}")

# 5) Estatísticas da partida (caso já tenha ocorrido)
if selected_game.get('placar_oficial_mandante') is not None:
    gols_casa = selected_game['placar_oficial_mandante']
    gols_fora = selected_game['placar_oficial_visitante']
    st.write(f"Gols Casa: {gols_casa}")
    st.write(f"Gols Fora: {gols_fora}")
else:
    st.info("Partida ainda não realizada ou sem placar disponível.")

# 6) Exemplo simples de cálculo de probabilidades fictícias (para você melhorar com dados futuros)
# Aqui você pode programar seus cálculos com dados históricos ou dados da API para escanteios, over/under etc.

st.subheader("Sugestões de Probabilidades e Combos")

# Como exemplo: probabilidade fixa só para demonstrar
prob_over_2_5 = 0.55
prob_btts = 0.50
prob_escanteios_over_9 = 0.60

odds_over_2_5 = 1.90
odds_btts = 1.85
odds_escanteios = 1.80

combo_odds = odds_over_2_5 * odds_btts * odds_escanteios

st.write(f"Probabilidades sugeridas:")
st.write(f"- Over 2.5 gols: {prob_over_2_5*100:.1f}%")
st.write(f"- Ambas marcam (BTTS): {prob_btts*100:.1f}%")
st.write(f"- Escanteios Over 9.5: {prob_escanteios_over_9*100:.1f}%")

st.write(f"Odds:")
st.write(f"- Over 2.5 gols: {odds_over_2_5}")
st.write(f"- Ambas marcam (BTTS): {odds_btts}")
st.write(f"- Escanteios Over 9.5: {odds_escanteios}")

st.write(f"Odds combinadas do combo: {combo_odds:.2f}")

valor_aposta = st.number_input("Valor da aposta (R$)", value=10.0, min_value=0.0, step=1.0)
retorno_potencial = valor_aposta * combo_odds
st.write(f"Retorno potencial: R$ {retorno_potencial:.2f}")
