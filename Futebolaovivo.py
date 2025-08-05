import streamlit as st
import requests
import math
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Configurações
st.set_page_config(page_title="Football Analyzer Pro", layout="wide")
sns.set_theme(style="whitegrid")

# Configurações da API
API_HOST = "api-football-v1.p.rapidapi.com"
API_URL = "https://api-football-v1.p.rapidapi.com/v3"
API_KEY = "2ca691e1f853684f13f3d7c492d0b0f5"  # Sua chave aqui

# ▶️ Implementação avançada de Poisson
def poisson_pmf(k, mu):
    return (mu ** k) * math.exp(-mu) / math.factorial(int(k))

def bivariate_poisson_prob(home_goals, away_goals, lambda_home, lambda_away):
    """Probabilidade conjunta usando distribuição de Poisson bivariada"""
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
        # Obter ratings atuais
        rh = self.get_rating(home_team) + self.home_advantage
        ra = self.get_rating(away_team)
        
        # Calcular resultado
        home_win = 1 if home_score > away_score else 0
        draw = 1 if home_score == away_score else 0
        away_win = 1 if home_score < away_score else 0
        
        # Calcular expectativas
        expected_home = 1 / (1 + 10 ** ((ra - rh) / 400))
        expected_away = 1 / (1 + 10 ** ((rh - ra) / 400))
        
        # Atualizar ratings
        self.ratings[home_team] = self.get_rating(home_team) + self.k_factor * (
            (home_win + 0.5 * draw) - expected_home
        )
        self.ratings[away_team] = self.get_rating(away_team) + self.k_factor * (
            (away_win + 0.5 * draw) - expected_away
        )
    
    def win_probability(self, home_team, away_team):
        rh = self.get_rating(home_team) + self.home_advantage
        ra = self.get_rating(away_team)
        return {
            'home': 1 / (1 + 10 ** ((ra - rh) / 400)),
            'away': 1 / (1 + 10 ** ((rh - ra) / 400)),
            'draw': 1 - (1 / (1 + 10 ** ((ra - rh) / 400)) + 1 / (1 + 10 ** ((rh - ra) / 400)))
        }

# ▶️ Inicialização de sessão
if 'avg_goals_home' not in st.session_state:
    st.session_state.update({
        'avg_goals_home': 1.5,
        'avg_goals_away': 1.2,
        'avg_corners_home': 5.0,
        'avg_corners_away': 4.5,
        'win_rate_home': 50.0,
        'win_rate_away': 30.0,
        'league_id': 71,
        'league_name': "Campeonato Brasileiro Série A",
        'elo_system': FootballElo()
    })

st.title("⚽ Football Analyzer Pro+")
st.subheader("Análise Profissional: Inteligência de Apostas")
st.markdown("---")

# ▶️ Configurações na sidebar
st.sidebar.header("🔌 Configurações")
season = st.sidebar.number_input("Temporada", 2023, 2025, 2024)

# [Código de seleção de liga aqui - manter da versão anterior]

# ▶️ Função para buscar dados históricos
def fetch_team_history(team_id, league, season, last_n=5):
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }
    
    try:
        url = f"{API_URL}/fixtures"
        querystring = {
            "team": team_id,
            "league": league,
            "season": season,
            "last": last_n
        }
        response = requests.get(url, headers=headers, params=querystring)
        fixtures = response.json()
        return fixtures.get('response', [])
    except Exception as e:
        st.error(f"Erro ao buscar histórico: {str(e)}")
        return []

# ▶️ Modelo Avançado de Previsão
def advanced_prediction_model(home_team, away_team, home_data, away_data, elo_system, context_factors):
    """
    Modelo profissional integrando:
    - Poisson bivariado
    - Sistema Elo
    - Fatores contextuais
    - Desempenho recente
    """
    # Médias básicas
    lambda_home = home_data.get('avg_goals_home', 1.5) * context_factors['home_attack_factor']
    lambda_away = away_data.get('avg_goals_away', 1.2) * context_factors['away_attack_factor']
    
    # Ajustes defensivos
    home_defense_factor = 1 - (away_data.get('avg_goals_away', 1.2) / 5)  # Normalizado
    away_defense_factor = 1 - (home_data.get('avg_goals_home', 1.5) / 5)
    
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
    over_25_prob = 1 - (score_probs[0,0] + score_probs[0,1] + score_probs[1,0] + 
                         score_probs[1,1] + score_probs[2,0] + score_probs[0,2] +
                         score_probs[1,2] + score_probs[2,1] + score_probs[2,2])
    
    # Integrar sistema Elo
    elo_probs = elo_system.win_probability(home_team, away_team)
    
    # Combinação ponderada
    final_home = (home_win_prob * 0.6) + (elo_probs['home'] * 0.4)
    final_draw = (draw_prob * 0.6) + (elo_probs['draw'] * 0.4)
    final_away = (away_win_prob * 0.6) + (elo_probs['away'] * 0.4)
    
    # Ajuste de fatores contextuais
    final_home *= context_factors['home_motivation']
    final_away *= context_factors['away_motivation']
    
    # Normalizar novamente
    total = final_home + final_draw + final_away
    final_home /= total
    final_draw /= total
    final_away /= total
    
    return {
        'home_win': final_home,
        'draw': final_draw,
        'away_win': final_away,
        'over_25': over_25_prob,
        'score_probs': score_probs,
        'expected_home_goals': lambda_home_adj,
        'expected_away_goals': lambda_away_adj
    }

# ▶️ Função para visualização profissional
def plot_probability_grid(probs, home_team, away_team):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Dados para o gráfico
    outcomes = [f'Vitória {home_team}', 'Empate', f'Vitória {away_team}']
    probabilities = [probs['home_win'], probs['draw'], probs['away_win']]
    colors = ['#2ca02c', '#ff7f0e', '#1f77b4']
    
    # Criar gráfico de barras
    bars = ax.bar(outcomes, probabilities, color=colors)
    
    # Adicionar valores nas barras
    for bar, prob in zip(bars, probabilities):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{prob:.1%}', ha='center', va='bottom', fontsize=12)
    
    # Configurações do gráfico
    ax.set_ylim(0, 1)
    ax.set_ylabel('Probabilidade', fontsize=12)
    ax.set_title('Probabilidade de Resultado Final', fontsize=14)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adicionar informações de valor esperado
    goal_text = (
        f"Gols Esperados: {home_team} {probs['expected_home_goals']:.1f} - "
        f"{away_team} {probs['expected_away_goals']:.1f}\n"
        f"Prob. Over 2.5: {probs['over_25']:.1%}"
    )
    plt.figtext(0.5, 0.01, goal_text, ha="center", fontsize=11, 
                bbox={"facecolor":"orange", "alpha":0.2, "pad":5})
    
    st.pyplot(fig)

# ▶️ Análise de valor contra odds de mercado
def value_bet_analysis(probabilities, market_odds):
    """
    Identifica apostas com valor baseado nas odds de mercado
    """
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

# [Interface de entrada de dados - similar à anterior]

# ▶️ Seção de fatores contextuais
st.header("🎯 Fatores Contextuais Avançados")
col_context1, col_context2 = st.columns(2)

with col_context1:
    st.subheader(f"Fatores do {team_home}")
    home_attack_factor = st.slider("Fator de Ataque (Casa)", 0.8, 1.2, 1.0, 0.05,
                                  help="Ajuste baseado em desempenho recente")
    home_motivation = st.slider("Motivação", 0.8, 1.2, 1.0, 0.05,
                               help="Importância da partida para o time")
    
with col_context2:
    st.subheader(f"Fatores do {team_away}")
    away_attack_factor = st.slider("Fator de Ataque (Fora)", 0.8, 1.2, 1.0, 0.05,
                                  help="Ajuste baseado em desempenho recente")
    away_motivation = st.slider("Motivação", 0.8, 1.2, 1.0, 0.05,
                               help="Importância da partida para o time")

context_factors = {
    'home_attack_factor': home_attack_factor,
    'away_attack_factor': away_attack_factor,
    'home_motivation': home_motivation,
    'away_motivation': away_motivation
}

# ▶️ Botão para análise profissional
if st.button("🔍 Realizar Análise Profissional", type="primary"):
    if not team_home or not team_away:
        st.error("Por favor, preencha os nomes dos times!")
    else:
        with st.spinner("Executando modelo avançado..."):
            # Buscar dados se necessário
            if 'home_data' not in st.session_state:
                home_data = fetch_team_data(team_home, st.session_state.league_id, season)
                away_data = fetch_team_data(team_away, st.session_state.league_id, season)
            else:
                home_data = st.session_state.home_data
                away_data = st.session_state.away_data
            
            # Executar modelo profissional
            start_time = time.time()
            prediction = advanced_prediction_model(
                team_home,
                team_away,
                {
                    'avg_goals_home': st.session_state.avg_goals_home,
                    'avg_goals_away': st.session_state.avg_goals_away
                },
                {
                    'avg_goals_home': st.session_state.avg_goals_away,
                    'avg_goals_away': st.session_state.avg_goals_away
                },
                st.session_state.elo_system,
                context_factors
            )
            processing_time = time.time() - start_time
            
            st.success(f"Análise concluída em {processing_time:.2f} segundos")
            st.markdown("---")
            st.subheader("📊 Resultados da Análise Profissional")
            
            # Mostrar probabilidades
            col_res1, col_res2 = st.columns([2, 1])
            
            with col_res1:
                st.markdown("### 📈 Probabilidades de Resultado")
                plot_probability_grid({
                    'home_win': prediction['home_win'],
                    'draw': prediction['draw'],
                    'away_win': prediction['away_win'],
                    'over_25': prediction['over_25'],
                    'expected_home_goals': prediction['expected_home_goals'],
                    'expected_away_goals': prediction['expected_away_goals']
                }, team_home, team_away)
                
            with col_res2:
                st.markdown("### 🔢 Dados Numéricos")
                st.metric(f"Vitória {team_home}", f"{prediction['home_win']:.1%}")
                st.metric("Empate", f"{prediction['draw']:.1%}")
                st.metric(f"Vitória {team_away}", f"{prediction['away_win']:.1%}")
                st.metric("Over 2.5 Gols", f"{prediction['over_25']:.1%}")
                st.metric(f"Gols Esperados {team_home}", f"{prediction['expected_home_goals']:.1f}")
                st.metric(f"Gols Esperados {team_away}", f"{prediction['expected_away_goals']:.1f}")
            
            # Análise de valor
            st.markdown("---")
            st.subheader("💰 Análise de Valor vs. Mercado")
            
            st.info("""
            **Como interpretar:**
            - **Odd Justa**: Probabilidade convertida em odds (1/probabilidade)
            - **Valor**: Diferença entre odds de mercado e odds justa
            - **Value Bet**: Quando a odd de mercado é maior que a odd justa
            """)
            
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
                st.success("🎯 OPORTUNIDADES DE VALUE BET IDENTIFICADAS!")
                st.dataframe(value_df.style.format({
                    'Odd Justa': '{:.2f}',
                    'Odd Mercado': '{:.2f}',
                    'Valor (%)': '{:.1f}%'
                }).applymap(lambda x: 'background-color: lightgreen' if x > 0 else '', subset=['Valor (%)']))
            else:
                st.warning("⚠️ Nenhuma oportunidade de value bet identificada")
            
            # Recomendações estratégicas
            st.markdown("---")
            st.subheader("🎯 Recomendações Estratégicas")
            
            recommendations = []
            
            # Critério para over 2.5
            if prediction['over_25'] > 0.55 and prediction['over_25'] > (1/market_over):
                recommendations.append(f"**OVER 2.5 GOALS** (Prob: {prediction['over_25']:.1%}, Valor: {(market_over - 1/prediction['over_25'])/1/prediction['over_25']*100:.1f}%)")
            
            # Critério para vitória em casa
            if prediction['home_win'] > 0.5 and prediction['home_win'] > (1/market_home):
                recommendations.append(f"**VITÓRIA {team_home.upper()}** (Prob: {prediction['home_win']:.1%}, Valor: {(market_home - 1/prediction['home_win'])/1/prediction['home_win']*100:.1f}%)")
            
            # Critério para vitória fora
            if prediction['away_win'] > 0.4 and prediction['away_win'] > (1/market_away):
                recommendations.append(f"**VITÓRIA {team_away.upper()}** (Prob: {prediction['away_win']:.1%}, Valor: {(market_away - 1/prediction['away_win'])/1/prediction['away_win']*100:.1f}%)")
            
            if recommendations:
                st.success("#### 💡 Melhores Oportunidades:")
                for rec in recommendations:
                    st.markdown(f"- {rec}")
            else:
                st.info("#### ⚖️ Partida Equilibrada")
                st.markdown("- Considere apostas em mercados alternativos ou aguarde odds melhores")
            
            st.markdown("---")
            st.caption("⚠️ **Nota:** As recomendações são baseadas em modelos estatísticos. Considere fatores adicionais como escalações, condições climáticas e contexto da partida antes de apostar.")

st.markdown("---")
st.caption(f"Desenvolvido por Football Analyzer Pro+ • {datetime.now().year} • Modelo Profissional v1.2")
