import streamlit as st
import requests
import math
import time
import pandas as pd
import numpy as np
from datetime import datetime

# Configurações
st.set_page_config(page_title="Football Analyzer Pro", layout="wide", page_icon="⚽")

# Configurações da API
API_HOST = "api-football-v1.p.rapidapi.com"
API_URL = "https://api-football-v1.p.rapidapi.com/v3"
API_KEY = "2ca691e1f853684f13f3d7c492d0b0f5"  # Sua chave API

# ▶️ Implementação avançada de Poisson
def poisson_pmf(k, mu):
    return (mu ** k) * math.exp(-mu) / math.factorial(int(k))

def bivariate_poisson_prob(home_goals, away_goals, lambda_home, lambda_away):
    return poisson_pmf(home_goals, lambda_home) * poisson_pmf(away_goals, lambda_away)

# ▶️ Sistema de Rating Elo
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
            (1 - home_win + 0.5 * draw) - (1 - expected_home)
        )
    
    def win_probability(self, home_team, away_team):
        rh = self.get_rating(home_team) + self.home_advantage
        ra = self.get_rating(away_team)
        home_prob = 1 / (1 + 10 ** ((ra - rh) / 400))
        away_prob = 1 / (1 + 10 ** ((rh - ra) / 400))
        return {
            'home': home_prob,
            'away': away_prob,
            'draw': max(0, 1 - (home_prob + away_prob))  # Garantir não negativo
        }

# ▶️ Inicialização de sessão
if 'avg_goals_home' not in st.session_state:
    st.session_state.update({
        'avg_goals_home': 1.5,
        'avg_goals_away': 1.2,
        'win_rate_home': 50.0,
        'win_rate_away': 30.0,
        'league_id': 71,
        'league_name': "Campeonato Brasileiro Série A",
        'elo_system': FootballElo()
    })

# ▶️ Interface principal
st.title("⚽ Football Analyzer Pro+")
st.subheader("Análise Profissional: Inteligência de Apostas")
st.markdown("---")

# ▶️ Configurações na sidebar
st.sidebar.header("🔌 Configurações")
season = st.sidebar.number_input("Temporada", 2023, 2025, 2024)

st.sidebar.markdown("### 🏆 Seleção de Liga")
league_id = st.sidebar.number_input("ID da Liga", min_value=1, value=71, step=1,
                                   help="Ex: 71 = Brasileirão, 39 = Premier League")
st.session_state.league_id = league_id

# ▶️ Função para buscar dados da API
def fetch_team_data(team_name, league, season):
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }
    
    try:
        # Buscar ID do time
        url = f"{API_URL}/teams"
        querystring = {"name": team_name}
        response = requests.get(url, headers=headers, params=querystring)
        team_data = response.json()
        
        if team_data.get('results', 0) == 0:
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
        response = requests.get(url, headers=headers, params=querystring)
        stats_data = response.json()
        
        return stats_data.get('response', {})
    except Exception as e:
        st.error(f"Erro na API: {str(e)}")
        return None

# ▶️ Modelo Avançado de Previsão
def advanced_prediction_model(home_team, away_team, home_data, away_data, elo_system, context_factors):
    # Médias básicas
    lambda_home = home_data['avg_goals_home'] * context_factors['home_attack_factor']
    lambda_away = away_data['avg_goals_away'] * context_factors['away_attack_factor']
    
    # Ajustes defensivos
    home_defense_factor = 1 - (away_data['avg_goals_away'] / 5)
    away_defense_factor = 1 - (home_data['avg_goals_home'] / 5)
    
    lambda_home_adj = lambda_home * away_defense_factor
    lambda_away_adj = lambda_away * home_defense_factor
    
    # Probabilidades de Poisson
    max_goals = 6
    score_probs = np.zeros((max_goals, max_goals))
    
    for i in range(max_goals):
        for j in range(max_goals):
            score_probs[i, j] = bivariate_poisson_prob(i, j, lambda_home_adj, lambda_away_adj)
    
    # Normalizar
    score_probs = score_probs / score_probs.sum()
    
    # Calcular probabilidades de resultados
    home_win_prob = np.sum(np.tril(score_probs, -1))
    draw_prob = np.sum(np.diag(score_probs))
    away_win_prob = np.sum(np.triu(score_probs, 1))
    
    # Over/Under 2.5
    over_25_prob = 1 - np.sum(score_probs[:3, :3])
    
    # Integrar sistema Elo
    elo_probs = elo_system.win_probability(home_team, away_team)
    
    # Combinação ponderada
    final_home = (home_win_prob * 0.6) + (elo_probs['home'] * 0.4)
    final_draw = (draw_prob * 0.6) + (elo_probs['draw'] * 0.4)
    final_away = (away_win_prob * 0.6) + (elo_probs['away'] * 0.4)
    
    # Ajuste de fatores contextuais
    final_home *= context_factors['home_motivation']
    final_away *= context_factors['away_motivation']
    
    # Normalizar
    total = final_home + final_draw + final_away
    return {
        'home_win': final_home / total,
        'draw': final_draw / total,
        'away_win': final_away / total,
        'over_25': over_25_prob,
        'expected_home_goals': lambda_home_adj,
        'expected_away_goals': lambda_away_adj
    }

# ▶️ Visualização de probabilidades
def display_probability_grid(probs, home_team, away_team):
    st.markdown("### 📊 Probabilidades de Resultado")
    
    # Criar DataFrame para o gráfico
    prob_data = pd.DataFrame({
        'Resultado': [f'Vitória {home_team}', 'Empate', f'Vitória {away_team}'],
        'Probabilidade': [probs['home_win'], probs['draw'], probs['away_win']]
    })
    
    # Exibir gráfico de barras
    st.bar_chart(prob_data.set_index('Resultado'), height=300)
    
    # Exibir métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"Vitória {home_team}", f"{probs['home_win']:.1%}")
    with col2:
        st.metric("Empate", f"{probs['draw']:.1%}")
    with col3:
        st.metric(f"Vitória {away_team}", f"{probs['away_win']:.1%}")
    
    # Exibir informações adicionais
    st.markdown(f"**Gols Esperados:** {home_team} {probs['expected_home_goals']:.1f} - "
                f"{away_team} {probs['expected_away_goals']:.1f}")
    st.metric("Probabilidade Over 2.5", f"{probs['over_25']:.1%}")

# ▶️ Análise de valor
def value_bet_analysis(probabilities, market_odds):
    value_bets = []
    
    # Calcular odds justas
    fair_odds = {
        'home': 1 / probabilities['home_win'],
        'draw': 1 / probabilities['draw'],
        'away': 1 / probabilities['away_win'],
        'over25': 1 / probabilities['over_25'],
        'under25': 1 / (1 - probabilities['over_25'])
    }
    
    # Verificar valor em cada mercado
    for market in fair_odds:
        if market in market_odds:
            if market_odds[market] > fair_odds[market]:
                value = (market_odds[market] / fair_odds[market] - 1) * 100
                value_bets.append({
                    'Mercado': market,
                    'Odd Justa': round(fair_odds[market], 2),
                    'Odd Mercado': market_odds[market],
                    'Valor (%)': round(value, 1)
                })
    
    return pd.DataFrame(value_bets)

# ▶️ Entrada de dados
st.header("📋 Informações da Partida")
col1, col2 = st.columns(2)

with col1:
    team_home = st.text_input("Time Mandante", key='home_team')
    avg_goals_home = st.number_input("Média de Gols Marcados (Casa)", 0.0, 10.0, step=0.1, 
                                    value=st.session_state.get('avg_goals_home', 1.5))

with col2:
    team_away = st.text_input("Time Visitante", key='away_team')
    avg_goals_away = st.number_input("Média de Gols Marcados (Fora)", 0.0, 10.0, step=0.1,
                                    value=st.session_state.get('avg_goals_away', 1.2))

# ▶️ Botão para buscar dados automáticos
if st.button("🔄 Buscar Dados Automáticos", help="Busca estatísticas atualizadas da API"):
    if not team_home or not team_away:
        st.error("Por favor, preencha os nomes dos times!")
    else:
        with st.spinner(f"Buscando dados para {team_home} e {team_away}..."):
            home_data = fetch_team_data(team_home, st.session_state.league_id, season)
            away_data = fetch_team_data(team_away, st.session_state.league_id, season)
            
            if home_data and away_data:
                try:
                    # Processar dados da API
                    st.session_state.avg_goals_home = home_data['goals']['for']['average']['home']
                    st.session_state.avg_goals_away = away_data['goals']['for']['average']['away']
                    
                    # Atualizar sistema Elo com dados históricos
                    # (Implementação simplificada)
                    st.session_state.elo_system.ratings[team_home] = 1500
                    st.session_state.elo_system.ratings[team_away] = 1500
                    
                    st.success("Dados atualizados com sucesso!")
                except KeyError:
                    st.warning("Dados incompletos da API - usando valores padrão")
                time.sleep(1)
                st.rerun()

# ▶️ Fatores Contextuais
st.header("🎯 Fatores Contextuais")
st.info("Ajuste os fatores com base em conhecimento específico da partida")

col_context1, col_context2 = st.columns(2)

with col_context1:
    st.subheader(f"Fatores do {team_home}")
    home_attack_factor = st.slider("Fator de Ataque (Casa)", 0.7, 1.3, 1.0, 0.05,
                                  help="Desempenho ofensivo recente", key='home_attack')
    home_motivation = st.slider("Motivação", 0.7, 1.3, 1.0, 0.05,
                               help="Importância da partida", key='home_motivation')

with col_context2:
    st.subheader(f"Fatores do {team_away}")
    away_attack_factor = st.slider("Fator de Ataque (Fora)", 0.7, 1.3, 1.0, 0.05,
                                  help="Desempenho ofensivo recente", key='away_attack')
    away_motivation = st.slider("Motivação", 0.7, 1.3, 1.0, 0.05,
                               help="Importância da partida", key='away_motivation')

context_factors = {
    'home_attack_factor': home_attack_factor,
    'away_attack_factor': away_attack_factor,
    'home_motivation': home_motivation,
    'away_motivation': away_motivation
}

# ▶️ Análise Profissional
st.markdown("---")
if st.button("🔍 Realizar Análise Profissional", type="primary", use_container_width=True):
    if not team_home or not team_away:
        st.error("Por favor, preencha os nomes dos times!")
    else:
        with st.spinner("Executando modelo avançado..."):
            # Dados para o modelo
            home_data = {
                'avg_goals_home': st.session_state.avg_goals_home,
                'avg_goals_away': st.session_state.avg_goals_away
            }
            
            away_data = {
                'avg_goals_home': st.session_state.avg_goals_away,
                'avg_goals_away': st.session_state.avg_goals_away
            }
            
            # Executar previsão
            prediction = advanced_prediction_model(
                team_home,
                team_away,
                home_data,
                away_data,
                st.session_state.elo_system,
                context_factors
            )
            
            st.success("Análise concluída!")
            st.markdown("---")
            st.subheader("📊 Resultados da Análise")
            
            # Mostrar resultados
            display_probability_grid(prediction, team_home, team_away)
            
            # Análise de valor
            st.markdown("---")
            st.subheader("💰 Análise de Valor")
            st.info("Compare as probabilidades com as odds do mercado")
            
            col_odds1, col_odds2, col_odds3 = st.columns(3)
            with col_odds1:
                market_home = st.number_input(f"Odd {team_home}", min_value=1.01, value=2.10, step=0.05)
            with col_odds2:
                market_draw = st.number_input("Odd Empate", min_value=1.01, value=3.40, step=0.05)
            with col_odds3:
                market_away = st.number_input(f"Odd {team_away}", min_value=1.01, value=3.80, step=0.05)
            
            col_odds4, col_odds5 = st.columns(2)
            with col_odds4:
                market_over = st.number_input("Odd Over 2.5", min_value=1.01, value=1.95, step=0.05)
            with col_odds5:
                market_under = st.number_input("Odd Under 2.5", min_value=1.01, value=1.90, step=0.05)
            
            market_odds = {
                'home': market_home,
                'draw': market_draw,
                'away': market_away,
                'over25': market_over,
                'under25': market_under
            }
            
            value_df = value_bet_analysis({
                'home': prediction['home_win'],
                'draw': prediction['draw'],
                'away': prediction['away_win'],
                'over25': prediction['over_25'],
                'under25': 1 - prediction['over_25']
            }, market_odds)
            
            if not value_df.empty:
                st.success("🎯 OPORTUNIDADES DE VALUE BET")
                st.dataframe(value_df.style.format({
                    'Odd Justa': '{:.2f}',
                    'Odd Mercado': '{:.2f}',
                    'Valor (%)': '{:.1f}%'
                }).background_gradient(subset=['Valor (%)'], cmap='Greens'))
            else:
                st.warning("⚠️ Nenhuma oportunidade de valor identificada")
            
            # Recomendações
            st.markdown("---")
            st.subheader("🎯 Recomendações Estratégicas")
            
            recommendations = []
            
            # Critério para over 2.5
            if prediction['over_25'] > 0.55 and market_over > (1 / prediction['over_25']):
                value_pct = (market_over - 1/prediction['over_25'])/(1/prediction['over_25'])*100
                recommendations.append(f"**OVER 2.5 GOALS** (Prob: {prediction['over_25']:.1%}, Valor: {value_pct:.1f}%)")
            
            # Critério para vitória em casa
            if prediction['home_win'] > 0.5 and market_home > (1 / prediction['home_win']):
                value_pct = (market_home - 1/prediction['home_win'])/(1/prediction['home_win'])*100
                recommendations.append(f"**VITÓRIA {team_home.upper()}** (Prob: {prediction['home_win']:.1%}, Valor: {value_pct:.1f}%)")
            
            # Critério para vitória fora
            if prediction['away_win'] > 0.4 and market_away > (1 / prediction['away_win']):
                value_pct = (market_away - 1/prediction['away_win'])/(1/prediction['away_win'])*100
                recommendations.append(f"**VITÓRIA {team_away.upper()}** (Prob: {prediction['away_win']:.1%}, Valor: {value_pct:.1f}%)")
            
            if recommendations:
                st.success("#### 💡 Melhores Oportunidades:")
                for rec in recommendations:
                    st.markdown(f"- {rec}")
            else:
                st.info("#### ⚖️ Partida Equilibrada")
                st.markdown("- Considere mercados alternativos ou apostas menores")
            
            st.markdown("---")
            st.caption("⚠️ **Nota:** Recomendações baseadas em modelos estatísticos. Considere outros fatores antes de apostar.")

# ▶️ Rodapé
st.markdown("---")
st.caption(f"© {datetime.now().year} Football Analyzer Pro+ • Modelo Profissional v2.0 • Dados: API-Football")
