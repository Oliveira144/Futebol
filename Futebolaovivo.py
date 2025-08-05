import streamlit as st
import requests
import math
import time
import pandas as pd
import numpy as np
from datetime import datetime
import scipy.stats as stats # Importa a biblioteca para cálculos estatísticos

# --- Configurações Iniciais ---
st.set_page_config(page_title="Football Analyzer Pro+", layout="wide", page_icon="⚽")

# Tenta carregar a chave da API de um arquivo de segredos, ou usa a fallback
try:
    API_KEY = st.secrets["api_football"]["key"]
except (KeyError, FileNotFoundError):
    st.warning("Chave da API não encontrada. Usando chave de fallback.")
    API_KEY = "2ca691e1f853684f13f3d7c492d0b0f5" # Sua chave de fallback

API_HOST = "api-football-v1.p.rapidapi.com"
API_URL = "https://api-football-v1.p.rapidapi.com/v3"

# --- Modelos Analíticos ---
@st.cache_data(ttl=3600)  # Cache de 1 hora para evitar re-cálculos
def poisson_pmf(k, mu):
    """Calcula a Probabilidade da Função de Massa (PMF) de Poisson."""
    return stats.poisson.pmf(k, mu)

@st.cache_data(ttl=3600)
def bivariate_poisson_prob(home_goals, away_goals, lambda_home, lambda_away):
    """Calcula a probabilidade de um placar usando Poisson Bivariado."""
    return poisson_pmf(home_goals, lambda_home) * poisson_pmf(away_goals, lambda_away)

class FootballElo:
    def __init__(self, base_rating=1500, k_factor=30, home_advantage=100):
        self.base_rating = base_rating
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.ratings = {}
    
    def get_rating(self, team):
        return self.ratings.get(team, self.base_rating)
    
    def update_ratings(self, home_team, away_team, home_score, away_score):
        rh = self.get_rating(home_team) + self.home_advantage
        ra = self.get_rating(away_team)
        
        home_win = 1 if home_score > away_score else 0
        draw = 1 if home_score == away_score else 0
        
        expected_home = 1 / (1 + 10 ** ((ra - rh) / 400))
        
        self.ratings[home_team] = self.get_rating(home_team) + self.k_factor * (
            (home_win + 0.5 * draw) - expected_home
        )
        self.ratings[away_team] = self.get_rating(away_team) + self.k_factor * (
            (1 - home_win + 0.5 * draw) - (1 - expected_home))
    
    def win_probability(self, home_team, away_team):
        rh = self.get_rating(home_team) + self.home_advantage
        ra = self.get_rating(away_team)
        home_prob = 1 / (1 + 10 ** ((ra - rh) / 400))
        away_prob = 1 / (1 + 10 ** ((rh - ra) / 400))
        return {
            'home': home_prob,
            'away': away_prob,
            'draw': max(0, 1 - (home_prob + away_prob))
        }

# --- Inicialização de Sessão ---
if 'elo_system' not in st.session_state:
    st.session_state.update({
        'avg_goals_home': 1.5,
        'avg_goals_away': 1.2,
        'league_id': 71,
        'league_name': "Campeonato Brasileiro Série A",
        'elo_system': FootballElo(),
    })

# --- Interface Principal ---
st.title("⚽ Football Analyzer Pro+")
st.subheader("Análise Profissional: Inteligência de Apostas")
st.markdown("---")

# --- Barra Lateral de Configurações ---
st.sidebar.header("🔌 Configurações")
st.sidebar.markdown("### 🏆 Seleção de Liga e Temporada")

# Lista de ligas populares
POPULAR_LEAGUES = [
    {"name": "Brasileirão Série A", "id": 71, "country": "Brasil"},
    {"name": "Premier League", "id": 39, "country": "Inglaterra"},
    {"name": "La Liga", "id": 140, "country": "Espanha"},
    {"name": "Bundesliga", "id": 78, "country": "Alemanha"},
    {"name": "Serie A", "id": 135, "country": "Itália"},
    {"name": "Ligue 1", "id": 61, "country": "França"},
    {"name": "Liga Portugal", "id": 94, "country": "Portugal"},
    {"name": "Eredivisie", "id": 88, "country": "Holanda"},
    {"name": "MLS", "id": 253, "country": "EUA/Canadá"},
    {"name": "Copa Libertadores", "id": 13, "country": "América do Sul"}
]

# Usando st.selectbox para uma seleção mais limpa
selected_league = st.sidebar.selectbox(
    "🏆 Selecione a Liga",
    options=POPULAR_LEAGUES,
    format_func=lambda x: f"{x['name']} ({x['country']})"
)
st.session_state.league_id = selected_league['id']
st.session_state.league_name = selected_league['name']

season = st.sidebar.number_input("Temporada", 2010, datetime.now().year + 1, datetime.now().year)

st.sidebar.markdown("---")
st.sidebar.subheader("Liga Selecionada")
st.sidebar.info(f"**{st.session_state.league_name}** - ID: **{st.session_state.league_id}**")
st.sidebar.info(f"Temporada: **{season}**")

# --- Funções de API com Cache ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_team_data(team_name, league, season):
    """Busca dados de um time na API com caching."""
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }
    
    try:
        # Buscar ID do time
        url = f"{API_URL}/teams"
        querystring = {"name": team_name}
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 429:
            st.error("Limite de requisições excedido. Tente novamente mais tarde.")
            return None
        elif response.status_code != 200:
            st.error(f"Erro na API ao buscar time: {response.status_code}")
            return None
            
        team_data = response.json()
        if not team_data['response']:
            st.error(f"Time '{team_name}' não encontrado!")
            return None
            
        team_id = team_data['response'][0]['team']['id']
        
        # Buscar estatísticas
        url = f"{API_URL}/teams/statistics"
        querystring = {
            "team": team_id,
            "league": league,
            "season": season
        }
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 429:
            st.error("Limite de requisições excedido. Tente novamente mais tarde.")
            return None
        elif response.status_code != 200:
            st.error(f"Erro na API ao buscar estatísticas: {response.status_code}")
            return None
            
        stats_data = response.json()
        return stats_data.get('response', {})
    except requests.exceptions.Timeout:
        st.error("A requisição demorou muito. Tente novamente.")
        return None
    except Exception as e:
        st.error(f"Erro na API: {str(e)}")
        return None

# --- Modelo de Previsão e Funções de Exibição ---
def advanced_prediction_model(home_team, away_team, home_data, away_data, elo_system, context_factors):
    lambda_home = home_data['avg_goals_home'] * context_factors['home_attack_factor']
    lambda_away = away_data['avg_goals_away'] * context_factors['away_attack_factor']
    
    home_defense_factor = 1 - (away_data['avg_goals_away'] / 5)
    away_defense_factor = 1 - (home_data['avg_goals_home'] / 5)
    
    lambda_home_adj = lambda_home * away_defense_factor
    lambda_away_adj = lambda_away * home_defense_factor
    
    max_goals = 6
    score_probs = np.zeros((max_goals, max_goals))
    
    for i in range(max_goals):
        for j in range(max_goals):
            score_probs[i, j] = bivariate_poisson_prob(i, j, lambda_home_adj, lambda_away_adj)
    
    score_probs = score_probs / score_probs.sum()
    
    home_win_prob = np.sum(np.tril(score_probs, -1))
    draw_prob = np.sum(np.diag(score_probs))
    away_win_prob = np.sum(np.triu(score_probs, 1))
    
    over_25_prob = 1 - np.sum(score_probs[:3, :3])
    
    elo_probs = elo_system.win_probability(home_team, away_team)
    
    final_home = (home_win_prob * 0.6) + (elo_probs['home'] * 0.4)
    final_draw = (draw_prob * 0.6) + (elo_probs['draw'] * 0.4)
    final_away = (away_win_prob * 0.6) + (elo_probs['away'] * 0.4)
    
    final_home *= context_factors['home_motivation']
    final_away *= context_factors['away_motivation']
    
    total = final_home + final_draw + final_away
    if total > 0:
        return {
            'home_win': final_home / total,
            'draw': final_draw / total,
            'away_win': final_away / total,
            'over_25': over_25_prob,
            'expected_home_goals': lambda_home_adj,
            'expected_away_goals': lambda_away_adj
        }
    else:
        return {
            'home_win': 0, 'draw': 0, 'away_win': 0, 'over_25': 0.5,
            'expected_home_goals': 0, 'expected_away_goals': 0
        }

def display_probability_grid(probs, home_team, away_team):
    st.markdown("### 📊 Probabilidades de Resultado")
    prob_data = pd.DataFrame({
        'Resultado': [f'Vitória {home_team}', 'Empate', f'Vitória {away_team}'],
        'Probabilidade': [probs['home_win'], probs['draw'], probs['away_win']]
    })
    st.bar_chart(prob_data.set_index('Resultado'), height=300)
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(f"Vitória {home_team}", f"{probs['home_win']:.1%}")
    with col2: st.metric("Empate", f"{probs['draw']:.1%}")
    with col3: st.metric(f"Vitória {away_team}", f"{probs['away_win']:.1%}")
    st.markdown(f"**Gols Esperados:** {home_team} {probs['expected_home_goals']:.1f} - "
                f"{away_team} {probs['expected_away_goals']:.1f}")
    st.metric("Probabilidade Over 2.5", f"{probs['over_25']:.1%}")

def value_bet_analysis(probabilities, market_odds):
    value_bets = []
    fair_odds = {
        'home': 1 / probabilities['home_win'] if probabilities['home_win'] > 0 else 1000,
        'draw': 1 / probabilities['draw'] if probabilities['draw'] > 0 else 1000,
        'away': 1 / probabilities['away_win'] if probabilities['away_win'] > 0 else 1000,
        'over25': 1 / probabilities['over_25'] if probabilities['over_25'] > 0 else 1000,
        'under25': 1 / (1 - probabilities['over_25']) if probabilities['over_25'] < 1 else 1000
    }
    for market in fair_odds:
        if market in market_odds and market_odds[market] > fair_odds[market]:
            value = (market_odds[market] / fair_odds[market] - 1) * 100
            value_bets.append({
                'Mercado': market,
                'Odd Justa': round(fair_odds[market], 2),
                'Odd Mercado': market_odds[market],
                'Valor (%)': round(value, 1)
            })
    return pd.DataFrame(value_bets)

# --- Entrada de Dados e Análise ---
st.header("📋 Informações da Partida")
match_date = st.date_input("🗓️ Data da Partida", datetime.now())

col1, col2 = st.columns(2)
with col1:
    team_home = st.text_input("Time Mandante", key='home_team')
    avg_goals_home = st.number_input(
        "Média de Gols Marcados (Casa)", 
        0.0, 10.0, step=0.1,
        value=st.session_state.avg_goals_home,
        key='avg_home_input'
    )
with col2:
    team_away = st.text_input("Time Visitante", key='away_team')
    avg_goals_away = st.number_input(
        "Média de Gols Marcados (Fora)", 
        0.0, 10.0, step=0.1,
        value=st.session_state.avg_goals_away,
        key='avg_away_input'
    )

if st.button("🔄 Buscar Dados Automáticos", help="Busca estatísticas atualizadas da API"):
    if not team_home or not team_away:
        st.error("Por favor, preencha os nomes dos times!")
    else:
        with st.spinner(f"Buscando dados para {team_home} e {team_away}..."):
            home_data = fetch_team_data(team_home, st.session_state.league_id, season)
            away_data = fetch_team_data(team_away, st.session_state.league_id, season)
            
            if home_data and 'goals' in home_data and 'for' in home_data['goals']:
                avg_home = float(home_data['goals']['for']['average']['home'])
                st.session_state.avg_goals_home = avg_home
            else:
                st.warning(f"Dados de gols em casa não encontrados para {team_home}. Verifique o nome do time ou a liga/temporada.")

            if away_data and 'goals' in away_data and 'for' in away_data['goals']:
                avg_away = float(away_data['goals']['for']['average']['away'])
                st.session_state.avg_goals_away = avg_away
            else:
                st.warning(f"Dados de gols fora não encontrados para {team_away}. Verifique o nome do time ou a liga/temporada.")
            
            st.success("Dados atualizados com sucesso!")
            st.rerun()

st.header("🎯 Fatores Contextuais")
st.info("Ajuste os fatores com base em conhecimento específico da partida")

col_context1, col_context2 = st.columns(2)
with col_context1:
    st.subheader(f"Fatores do {team_home}")
    home_attack_factor = st.slider("Fator de Ataque (Casa)", 0.7, 1.3, 1.0, 0.05, key='home_attack')
    home_motivation = st.slider("Motivação", 0.7, 1.3, 1.0, 0.05, key='home_motivation')
with col_context2:
    st.subheader(f"Fatores do {team_away}")
    away_attack_factor = st.slider("Fator de Ataque (Fora)", 0.7, 1.3, 1.0, 0.05, key='away_attack')
    away_motivation = st.slider("Motivação", 0.7, 1.3, 1.0, 0.05, key='away_motivation')

context_factors = {
    'home_attack_factor': home_attack_factor,
    'away_attack_factor': away_attack_factor,
    'home_motivation': home_motivation,
    'away_motivation': away_motivation
}

st.markdown("---")
if st.button("🔍 Realizar Análise Profissional", type="primary", use_container_width=True):
    if not team_home or not team_away:
        st.error("Por favor, preencha os nomes dos times!")
    else:
        with st.spinner("Executando modelo avançado..."):
            home_data = {'avg_goals_home': st.session_state.avg_goals_home, 'avg_goals_away': st.session_state.avg_goals_away}
            away_data = {'avg_goals_home': st.session_state.avg_goals_away, 'avg_goals_away': st.session_state.avg_goals_away}
            
            prediction = advanced_prediction_model(team_home, team_away, home_data, away_data, st.session_state.elo_system, context_factors)
            
            st.success("Análise concluída!")
            st.markdown("---")
            st.subheader("📊 Resultados da Análise")
            display_probability_grid(prediction, team_home, team_away)
            
            st.markdown("---")
            st.subheader("💰 Análise de Valor")
            st.info("Compare as probabilidades com as odds do mercado")
            
            col_odds1, col_odds2, col_odds3 = st.columns(3)
            with col_odds1: market_home = st.number_input(f"Odd {team_home}", min_value=1.01, value=2.10, step=0.05)
            with col_odds2: market_draw = st.number_input("Odd Empate", min_value=1.01, value=3.40, step=0.05)
            with col_odds3: market_away = st.number_input(f"Odd {team_away}", min_value=1.01, value=3.80, step=0.05)
            col_odds4, col_odds5 = st.columns(2)
            with col_odds4: market_over = st.number_input("Odd Over 2.5", min_value=1.01, value=1.95, step=0.05)
            with col_odds5: market_under = st.number_input("Odd Under 2.5", min_value=1.01, value=1.90, step=0.05)
            
            market_odds = {'home': market_home, 'draw': market_draw, 'away': market_away, 'over25': market_over, 'under25': market_under}
            
            value_df = value_bet_analysis({'home_win': prediction['home_win'], 'draw': prediction['draw'], 'away_win': prediction['away_win'], 'over_25': prediction['over_25']}, market_odds)
            
            if not value_df.empty:
                st.success("🎯 OPORTUNIDADES DE VALUE BET")
                styled_df = value_df.style.format({'Odd Justa': '{:.2f}', 'Odd Mercado': '{:.2f}', 'Valor (%)': '{:.1f}%'}).background_gradient(subset=['Valor (%)'], cmap='Greens')
                st.dataframe(styled_df)
            else:
                st.warning("⚠️ Nenhuma oportunidade de valor identificada")
            
            st.markdown("---")
            st.subheader("🎯 Recomendações Estratégicas")
            recommendations = []
            if prediction['over_25'] > 0.55 and market_over > (1 / prediction['over_25']):
                value_pct = (market_over - 1/prediction['over_25'])/(1/prediction['over_25'])*100
                recommendations.append(f"**OVER 2.5 GOALS** (Prob: {prediction['over_25']:.1%}, Valor: {value_pct:.1f}%)")
            if prediction['home_win'] > 0.5 and market_home > (1 / prediction['home_win']):
                value_pct = (market_home - 1/prediction['home_win'])/(1/prediction['home_win'])*100
                recommendations.append(f"**VITÓRIA {team_home.upper()}** (Prob: {prediction['home_win']:.1%}, Valor: {value_pct:.1f}%)")
            if prediction['away_win'] > 0.4 and market_away > (1 / prediction['away_win']):
                value_pct = (market_away - 1/prediction['away_win'])/(1/prediction['away_win'])*100
                recommendations.append(f"**VITÓRIA {team_away.upper()}** (Prob: {prediction['away_win']:.1%}, Valor: {value_pct:.1f}%)")
            
            if recommendations:
                st.success("#### 💡 Melhores Oportunidades:")
                for rec in recommendations: st.markdown(f"- {rec}")
                st.markdown("""
                **Estratégia Recomendada:**
                - Aposte apenas em mercados com >5% de valor
                - Gerencie seu bankroll (não aposte mais que 2% por aposta)
                - Considere combinar com outros mercados para aumentar o valor
                """)
            else:
                st.info("#### ⚖️ Partida Equilibrada")
                st.markdown("""
                - Considere mercados alternativos (ambos marcam, escanteios, etc.)
                - Apostas menores com maior valor
                - Aguarde odds melhores durante o jogo
                """)
            
            st.markdown("---")
            st.caption("⚠️ **Nota Profissional:** As recomendações são baseadas em modelos estatísticos. Sempre considere fatores adicionais como escalações completas, condições climáticas, histórico de confrontos e contexto da partida antes de apostar.")

st.markdown("---")
st.caption(f"© {datetime.now().year} Football Analyzer Pro+ • Modelo Profissional v2.1 • Dados: API-Football")
        
