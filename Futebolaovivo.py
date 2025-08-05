import streamlit as st
import requests
import math
import time

st.set_page_config(page_title="Football Analyzer Pro", layout="wide")

# Configurações da API
API_HOST = "api-football-v1.p.rapidapi.com"
API_URL = "https://api-football-v1.p.rapidapi.com/v3"

# ▶️ Implementação alternativa de Poisson (caso SciPy não esteja disponível)
def poisson_pdf(k, mu):
    """Calcula a probabilidade Poisson sem dependências externas"""
    return (mu ** k) * math.exp(-mu) / math.factorial(k)

def poisson_cdf(k, mu):
    """Calcula a função de distribuição acumulada Poisson"""
    cdf = 0.0
    for i in range(0, k + 1):
        cdf += poisson_pdf(i, mu)
    return cdf

# ▶️ Inicialização de sessão
if 'avg_goals_home' not in st.session_state:
    st.session_state.update({
        'avg_goals_home': 1.5,
        'avg_goals_away': 1.2,
        'avg_corners_home': 5.0,
        'avg_corners_away': 4.5,
        'win_rate_home': 50.0,
        'win_rate_away': 30.0
    })

st.title("⚽ Football Analyzer Pro")
st.subheader("Análise Avançada com Dados Automáticos de API")
st.markdown("---")

# ▶️ Configurações de API na sidebar
st.sidebar.header("🔌 Configurações da API")
api_key = st.sidebar.text_input("Chave API-Football", type="password", help="Obtenha em: https://www.api-football.com/")
season = st.sidebar.number_input("Temporada", 2023, 2025, 2024)
league_id = st.sidebar.number_input("ID da Liga", value=71, help="Ex: 71=Brasileirão, 39=Premier League, 140=La Liga")

# ▶️ Função para buscar dados da API
def fetch_team_data(api_key, team_name, league, season):
    """Busca estatísticas do time na API-Football"""
    if not api_key or not team_name:
        return None
        
    headers = {
        "X-RapidAPI-Key": api_key,
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

# ▶️ Função de análise aprimorada
def analyze_match(home_data, away_data):
    """Realiza análise estatística dos dados"""
    results = {}
    
    try:
        # Processar dados do mandante
        home_stats = home_data.get('goals', {})
        home_corners = home_data.get('corners', {})
        home_fixtures = home_data.get('fixtures', {})
        
        # Processar dados do visitante
        away_stats = away_data.get('goals', {})
        away_corners = away_data.get('corners', {})
        away_fixtures = away_data.get('fixtures', {})
        
        # Calcular médias
        avg_goals_home = home_stats.get('for', {}).get('average', {}).get('home', 0)
        avg_goals_away = away_stats.get('for', {}).get('average', {}).get('away', 0)
        avg_corners_home = home_corners.get('for', {}).get('average', {}).get('home', 0)
        avg_corners_away = away_corners.get('for', {}).get('average', {}).get('away', 0)
        
        # Calcular taxas de vitória
        home_wins = home_fixtures.get('wins', {}).get('home', 0)
        home_played = home_fixtures.get('played', {}).get('home', 1)  # Evitar divisão por zero
        win_rate_home = (home_wins / home_played) * 100 if home_played else 0
        
        away_wins = away_fixtures.get('wins', {}).get('away', 0)
        away_played = away_fixtures.get('played', {}).get('away', 1)
        win_rate_away = (away_wins / away_played) * 100 if away_played else 0
        
        # Análise de gols
        avg_goals_total = avg_goals_home + avg_goals_away
        
        # Usar implementação própria de Poisson
        prob_over_25 = 1 - poisson_cdf(2, avg_goals_total) if avg_goals_total else 0
        
        # Análise de escanteios
        total_corners = avg_corners_home + avg_corners_away
        
        # Resultados
        results = {
            'avg_goals_home': avg_goals_home,
            'avg_goals_away': avg_goals_away,
            'avg_goals_total': avg_goals_total,
            'prob_over_25': prob_over_25,
            'avg_corners_home': avg_corners_home,
            'avg_corners_away': avg_corners_away,
            'total_corners': total_corners,
            'win_rate_home': win_rate_home,
            'win_rate_away': win_rate_away,
            'home_wins': home_wins,
            'away_wins': away_wins
        }
    except Exception as e:
        st.error(f"Erro na análise: {str(e)}")
    
    return results

# ▶️ Entrada de dados
st.header("📋 Informações da Partida")
col1, col2 = st.columns(2)

with col1:
    team_home = st.text_input("Time Mandante")
    avg_goals_home = st.number_input("Média de Gols Marcados (Casa)", 0.0, 10.0, step=0.1, 
                                    value=st.session_state.get('avg_goals_home', 1.5))
    avg_corners_home = st.number_input("Média de Escanteios (Casa)", 0.0, 20.0, step=0.1,
                                     value=st.session_state.get('avg_corners_home', 5.0))

with col2:
    team_away = st.text_input("Time Visitante")
    avg_goals_away = st.number_input("Média de Gols Marcados (Fora)", 0.0, 10.0, step=0.1,
                                    value=st.session_state.get('avg_goals_away', 1.2))
    avg_corners_away = st.number_input("Média de Escanteios (Fora)", 0.0, 20.0, step=0.1,
                                     value=st.session_state.get('avg_corners_away', 4.5))

st.markdown("### 📊 Dados Avançados")
col3, col4 = st.columns(2)

with col3:
    win_rate_home = st.number_input("Taxa de Vitórias Casa (%)", 0.0, 100.0, step=1.0,
                                  value=st.session_state.get('win_rate_home', 50.0))

with col4:
    win_rate_away = st.number_input("Taxa de Vitórias Fora (%)", 0.0, 100.0, step=1.0,
                                  value=st.session_state.get('win_rate_away', 30.0))

# ▶️ Botão para buscar dados automáticos
if st.button("🔄 Buscar Dados Automáticos", help="Busca estatísticas atualizadas da API") and api_key:
    with st.spinner(f"Buscando dados para {team_home} e {team_away}..."):
        home_data = fetch_team_data(api_key, team_home, league_id, season)
        away_data = fetch_team_data(api_key, team_away, league_id, season)
        
        if home_data and away_data:
            analysis = analyze_match(home_data, away_data)
            
            # Atualizar campos com dados da API
            st.session_state.avg_goals_home = analysis.get('avg_goals_home', 1.5)
            st.session_state.avg_goals_away = analysis.get('avg_goals_away', 1.2)
            st.session_state.avg_corners_home = analysis.get('avg_corners_home', 5.0)
            st.session_state.avg_corners_away = analysis.get('avg_corners_away', 4.5)
            st.session_state.win_rate_home = analysis.get('win_rate_home', 50.0)
            st.session_state.win_rate_away = analysis.get('win_rate_away', 30.0)
            
            st.success("Dados atualizados com sucesso!")
            time.sleep(1)
            st.rerun()

# ▶️ Processar Análise
if st.button("🔍 Analisar Partida"):
    if not team_home or not team_away:
        st.error("Por favor, preencha os nomes dos times!")
    else:
        st.markdown("---")
        st.subheader("📈 Resultados da Análise")
        
        # Calcular totais
        avg_goals_total = st.session_state.avg_goals_home + st.session_state.avg_goals_away
        total_corners = st.session_state.avg_corners_home + st.session_state.avg_corners_away
        
        # Análise de Gols (Under/Over)
        st.markdown("### ⚽ Under/Over")
        st.write(f"Média total de gols esperados: **{avg_goals_total:.2f}**")
        
        # Cálculo de probabilidade com Poisson
        prob_over_25 = 1 - poisson_cdf(2, avg_goals_total)  # P(X > 2) = 1 - P(X <= 2)
        
        if prob_over_25 >= 0.65:  # 65% de probabilidade
            st.success(f"✅ Forte tendência de Over 2.5 gols (Prob: {prob_over_25:.0%})")
        elif prob_over_25 <= 0.35:
            st.warning(f"⚠️ Tendência de Under 2.5 gols (Prob: {1 - prob_over_25:.0%})")
        else:
            st.info(f"🔍 Zona neutra: Over 2.5 ({prob_over_25:.0%}) | Under 2.5 ({(1 - prob_over_25):.0%})")

        # Análise de Escanteios
        st.markdown("### 🥅 Escanteios")
        st.write(f"Média total de escanteios esperados: **{total_corners:.2f}**")
        
        if total_corners >= 10.5:
            st.success("✅ Boa tendência de Over 10.5 escanteios")
        elif total_corners <= 8.5:
            st.warning("⚠️ Tendência de Under 8.5 escanteios")
        else:
            st.info("🔍 Média de cantos equilibrada")

        # Análise de Resultado Final
        st.markdown("### 🧮 Resultado Final (1X2)")
        home_win_prob = st.session_state.win_rate_home / 100
        away_win_prob = st.session_state.win_rate_away / 100
        
        if st.session_state.win_rate_home > st.session_state.win_rate_away and st.session_state.win_rate_home >= 60:
            st.success(f"✅ Tendência de vitória do {team_home} ({st.session_state.win_rate_home:.0f}%)")
        elif st.session_state.win_rate_away > st.session_state.win_rate_home and st.session_state.win_rate_away >= 60:
            st.success(f"✅ Tendência de vitória do {team_away} ({st.session_state.win_rate_away:.0f}%)")
        else:
            draw_prob = 1 - (home_win_prob + away_win_prob)
            st.info(f"🔍 Jogo equilibrado: {team_home} ({home_win_prob:.0%}) | Empate ({draw_prob:.0%}) | {team_away} ({away_win_prob:.0%})")

        # Conclusão
        st.markdown("---")
        st.subheader("🎯 Sugestões com base nos dados:")
        
        suggestions = []
        if prob_over_25 >= 0.6:
            suggestions.append(f"- **Over 2.5 gols** (Probabilidade: {prob_over_25:.0%})")
        if total_corners >= 10.5:
            suggestions.append(f"- **Over 10.5 escanteios** (Média: {total_corners:.1f})")
        if st.session_state.win_rate_home >= 60:
            suggestions.append(f"- **Vitória do {team_home}** (Taxa: {st.session_state.win_rate_home:.0f}%)")
        if st.session_state.win_rate_away >= 60:
            suggestions.append(f"- **Vitória do {team_away}** (Taxa: {st.session_state.win_rate_away:.0f}%)")
        
        if suggestions:
            for suggestion in suggestions:
                st.markdown(suggestion)
        else:
            st.markdown("- ⚖️ Partida equilibrada - considere análises adicionais")
        
        st.markdown("---")
        st.markdown("📌 *Sugestões devem ser validadas com análise ao vivo e contexto atual*")

st.markdown("---")
st.caption("Desenvolvido por Football Analyzer Pro • Dados: API-Football • Streamlit App")
