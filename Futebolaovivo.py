import streamlit as st
import requests

# Chave da API que você informou
API_KEY = "live_3c5fe5334d0f4f8a24ae5a4968ff49"
BASE_URL = "https://api.api-futebol.com.br/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

st.title("Análise de Futebol com API Futebol (Brasileirão e outros)")

# Função para buscar campeonatos
@st.cache_data(ttl=3600)
def get_competitions():
    url = f"{BASE_URL}/campeonatos"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Erro ao carregar campeonatos da API. Código: {res.status_code}")
        try:
            st.error(f"Mensagem: {res.text}")
        except:
            pass
        return []

competitions = get_competitions()
if not competitions:
    st.stop()

competitions_dict = {c['nome_popular']: c['campeonato_id'] for c in competitions}

selected_competition_name = st.selectbox("Escolha o Campeonato", list(competitions_dict.keys()))
selected_competition_id = competitions_dict[selected_competition_name]

# Função para buscar rodadas do campeonato
@st.cache_data(ttl=600)
def get_rounds(campeonato_id):
    url = f"{BASE_URL}/campeonatos/{campeonato_id}/rodadas"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Erro ao carregar rodadas da API. Código: {res.status_code}")
        try:
            st.error(f"Mensagem: {res.text}")
        except:
            pass
        return []

rounds = get_rounds(selected_competition_id)
if not rounds:
    st.warning("Não há rodadas disponíveis para este campeonato.")
    st.stop()

round_options = [r['nome'] for r in rounds]
selected_round_name = st.selectbox("Escolha a Rodada", round_options)

# Função para extrair apenas números da rodada (ex: "19" de "19ª Rodada")
def extrair_numero_rodada(nome_rodada):
    return ''.join(filter(str.isdigit, nome_rodada))

selected_round_number = extrair_numero_rodada(selected_round_name)

# Função para buscar jogos de uma rodada usando o número da rodada
@st.cache_data(ttl=600)
def get_games(campeonato_id, rodada_num):
    url = f"{BASE_URL}/campeonatos/{campeonato_id}/rodadas/{rodada_num}/jogos"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Erro ao carregar jogos da API. Código: {res.status_code}")
        try:
            st.error(f"Mensagem: {res.text}")
        except:
            pass
        return []

games = get_games(selected_competition_id, selected_round_number)
if not games:
    st.warning("Nenhum jogo encontrado nesta rodada.")
    st.stop()

games_dict = {
    f"{g['time_mandante']['nome_popular']} x {g['time_visitante']['nome_popular']}": g
    for g in games
}
selected_game_name = st.selectbox("Escolha a Partida", list(games_dict.keys()))
selected_game = games_dict[selected_game_name]

# Mostrar informações básicas da partida
st.subheader(f"Jogo selecionado: {selected_game_name}")
st.write(f"Data da partida: {selected_game['data_realizacao']}")
local = selected_game.get('estadio', {}).get('nome_popular', 'Não disponível')
st.write(f"Local: {local}")

# Estatísticas oficiais (se disponíveis)
if selected_game.get('placar_oficial_mandante') is not None:
    gols_casa = selected_game['placar_oficial_mandante']
    gols_fora = selected_game['placar_oficial_visitante']
    st.write(f"Gols Casa: {gols_casa}")
    st.write(f"Gols Fora: {gols_fora}")
else:
    st.info("Placar oficial não disponível. Partida pode não ter sido realizada ainda.")

# Aqui podemos buscar dados adicionais como escanteios e outras estatísticas,
# mas como a API fornece dados básicos neste endpoint, deixo como próximo passo para você.

# Exemplo com probabilidades fixas (substitua por cálculos reais com dados)
st.subheader("Análise simples e sugestões de apostas")

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

st.write(f"Cotações (Odds):")
st.write(f"- Over 2.5 gols: {odds_over_2_5}")
st.write(f"- Ambas Marcam (BTTS): {odds_btts}")
st.write(f"- Escanteios Over 9.5: {odds_escanteios}")

st.write(f"Odds combinadas do combo sugerido: {combo_odds:.2f}")

valor_aposta = st.number_input("Valor da aposta (R$)", value=10.0, min_value=0.0, step=1.0)
retorno_potencial = valor_aposta * combo_odds
st.write(f"Retorno potencial da aposta: R$ {retorno_potencial:.2f}")
