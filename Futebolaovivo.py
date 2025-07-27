import streamlit as st
import requests

API_KEY = "live_3c5fe5334d0f4f8a24ae5a4968ff49"
BASE_URL = "https://api.api-futebol.com.br/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

st.title("Análise de Futebol com API Futebol (Brasileirão e outros)")

@st.cache_data(ttl=3600)
def get_competitions():
    url = f"{BASE_URL}/campeonatos"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Erro ao carregar campeonatos. Código: {res.status_code}")
        try:
            st.error(f"Mensagem: {res.text}")
        except:
            pass
        return []

@st.cache_data(ttl=600)
def get_rounds(campeonato_id):
    url = f"{BASE_URL}/campeonatos/{campeonato_id}/rodadas"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Erro ao carregar rodadas. Código: {res.status_code}")
        try:
            st.error(f"Mensagem: {res.text}")
        except:
            pass
        return []

@st.cache_data(ttl=600)
def get_phases(campeonato_id):
    url = f"{BASE_URL}/campeonatos/{campeonato_id}/fases"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Erro ao carregar fases. Código: {res.status_code}")
        try:
            st.error(f"Mensagem: {res.text}")
        except:
            pass
        return []

@st.cache_data(ttl=600)
def get_games_by_phase(campeonato_id, fase_id):
    url = f"{BASE_URL}/campeonatos/{campeonato_id}/fases/{fase_id}/jogos"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Erro ao carregar jogos. Código: {res.status_code}")
        try:
            st.error(f"Mensagem: {res.text}")
        except:
            pass
        return []

def extrair_numero_rodada(nome_rodada):
    return ''.join(filter(str.isdigit, nome_rodada))

# 1. Seleção do Campeonato
competitions = get_competitions()
if not competitions:
    st.stop()
competitions_dict = {c['nome_popular']: c['campeonato_id'] for c in competitions}
selected_competition_name = st.selectbox("Escolha o Campeonato", list(competitions_dict.keys()))
selected_competition_id = competitions_dict[selected_competition_name]

# 2. Seleção da Rodada
rounds = get_rounds(selected_competition_id)
if not rounds:
    st.warning("Nenhuma rodada disponível para este campeonato.")
    st.stop()
round_names = [r['nome'] for r in rounds]
selected_round_name = st.selectbox("Escolha a Rodada", round_names)
selected_round_number = extrair_numero_rodada(selected_round_name)

# 3. Seleção da Fase
phases = get_phases(selected_competition_id)
if not phases:
    st.warning("Nenhuma fase disponível para este campeonato.")
    st.stop()
phases_dict = {p['nome']: p['fase_id'] for p in phases}
selected_phase_name = st.selectbox("Escolha a Fase", list(phases_dict.keys()))
selected_phase_id = phases_dict[selected_phase_name]

# 4. Buscar jogos da fase e filtrar pela rodada
all_games = get_games_by_phase(selected_competition_id, selected_phase_id)
if not all_games:
    st.warning("Nenhum jogo encontrado para a fase selecionada.")
    st.stop()

games_filtered = [g for g in all_games if str(g.get('rodada')) == selected_round_number]
if not games_filtered:
    st.warning(f"Nenhum jogo encontrado para a rodada {selected_round_name} na fase {selected_phase_name}.")
    st.stop()

games_dict = {
    f"{g['time_mandante']['nome_popular']} x {g['time_visitante']['nome_popular']}": g
    for g in games_filtered
}
selected_game_name = st.selectbox("Escolha a Partida", list(games_dict.keys()))
selected_game = games_dict[selected_game_name]

# 5. Mostrar detalhes do jogo
st.subheader(f"Jogo selecionado: {selected_game_name}")
st.write(f"Data da partida: {selected_game['data_realizacao']}")
local = selected_game.get('estadio', {}).get('nome_popular', 'Não disponível')
st.write(f"Local: {local}")

if selected_game.get('placar_oficial_mandante') is not None:
    gols_casa = selected_game['placar_oficial_mandante']
    gols_fora = selected_game['placar_oficial_visitante']
    st.write(f"Gols Casa: {gols_casa}")
    st.write(f"Gols Fora: {gols_fora}")
else:
    st.info("Placar oficial não disponível. O jogo pode ainda não ter ocorrido.")

# 6. Sugestões simples de apostas (exemplo com dados fixos)
st.subheader("Sugestões de Probabilidades e Combos")

prob_over_2_5 = 0.55
prob_btts = 0.50
prob_escanteios_over_9 = 0.60

odds_over_2_5 = 1.90
odds_btts = 1.85
odds_escanteios = 1.80

combo_odds = odds_over_2_5 * odds_btts * odds_escanteios

st.write(f"Probabilidades sugeridas:")
st.write(f"- Over 2.5 gols: {prob_over_2_5 * 100:.1f}%")
st.write(f"- Ambas Marcam (BTTS): {prob_btts * 100:.1f}%")
st.write(f"- Escanteios Over 9.5: {prob_escanteios_over_9 * 100:.1f}%")

st.write(f"Odds para apostas:")
st.write(f"- Over 2.5 gols: {odds_over_2_5}")
st.write(f"- Ambas Marcam (BTTS): {odds_btts}")
st.write(f"- Escanteios Over 9.5: {odds_escanteios}")

st.write(f"Odds combinadas do combo sugerido: {combo_odds:.2f}")

valor_aposta = st.number_input("Valor da aposta (R$)", value=10.0, min_value=0.0, step=1.0)
retorno_potencial = valor_aposta * combo_odds
st.write(f"Retorno potencial da aposta: R$ {retorno_potencial:.2f}")
