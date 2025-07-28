import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIG --- #
st.set_page_config(page_title="Sugestões Futebol Inteligente", page_icon="⚽", layout="wide")
st.title("⚽ Consulta Inteligente de Jogos - API-Football (RapidAPI)")

# API Key Input
API_KEY = st.text_input("Digite sua API Key da RapidAPI", type="password").strip()
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

# Headers for API requests
headers = {
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
    "x-rapidapi-key": API_KEY
}

# --- FUNÇÕES --- #

@st.cache_data(ttl=3600) # Cache data for 1 hour to avoid redundant API calls
def buscar_jogos(data, headers):
    """
    Busca jogos de futebol para uma data específica na API-Football.
    """
    if not headers.get("x-rapidapi-key"):
        return {"error": "API Key não fornecida. Por favor, insira sua chave."}

    url = f"{BASE_URL}/fixtures"
    params = {"date": data}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return r.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 403:
            return {"error": "API Key inválida ou limites de requisição excedidos. Verifique sua chave."}
        elif status_code == 404:
            return {"error": f"Nenhum dado encontrado para a data {data}."}
        else:
            return {"error": f"Erro HTTP ao buscar jogos: {e}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Erro de conexão. Verifique sua internet."}
    except requests.exceptions.Timeout:
        return {"error": "Tempo limite da requisição excedido."}
    except Exception as e:
        return {"error": f"Ocorreu um erro inesperado: {e}"}

@st.cache_data(ttl=3600) # Cache data for 1 hour
def buscar_stats(time_id, liga_id, temporada, headers):
    """
    Busca estatísticas de um time para uma liga e temporada específicas.
    """
    if not headers.get("x-rapidapi-key"):
        return {"error": "API Key não fornecida. Por favor, insira sua chave."}

    url = f"{BASE_URL}/teams/statistics"
    params = {"team": time_id, "league": liga_id, "season": temporada}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 403:
            return {"error": "API Key inválida ou limites de requisição excedidos. Verifique sua chave."}
        else:
            return {"error": f"Erro HTTP ao buscar estatísticas: {e}. Time ID: {time_id}, Liga ID: {liga_id}, Temporada: {temporada}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Erro de conexão ao buscar estatísticas. Verifique sua internet."}
    except requests.exceptions.Timeout:
        return {"error": "Tempo limite da requisição de estatísticas excedido."}
    except Exception as e:
        return {"error": f"Ocorreu um erro inesperado ao buscar estatísticas: {e}"}

def gerar_sugestao(mercado, stats_home, stats_away, jogo_detalhes=None):
    """
    Gera sugestões de aposta com base nas estatísticas dos times e no mercado escolhido.
    """
    sugestao = "⚠ Dados insuficientes para esta sugestão."

    if not stats_home or stats_home.get("error") or not stats_away or stats_away.get("error"):
        return "⚠ Não foi possível obter estatísticas de um ou ambos os times. Sugestão indisponível."

    try:
        home_stats_res = stats_home.get("response")
        away_stats_res = stats_away.get("response")

        if not home_stats_res or not away_stats_res:
            return "⚠ Dados de estatísticas incompletos. Sugestão indisponível."

        # Extraindo informações relevantes do jogo para contexto
        home_name = jogo_detalhes["teams"]["home"]["name"] if jogo_detalhes else "Time Casa"
        away_name = jogo_detalhes["teams"]["away"]["name"] if jogo_detalhes else "Time Visitante"

        if mercado == "Vitória (1X2)":
            # Usando a forma (ganhos/empates/derrotas) ou desempenho geral
            # Para uma análise mais aprofundada, seria ideal considerar a forma recente (últimos 5-10 jogos)
            home_wins = home_stats_res["fixtures"]["wins"]["total"]
            away_wins = away_stats_res["fixtures"]["wins"]["total"]
            
            home_played = home_stats_res["fixtures"]["played"]["total"]
            away_played = away_stats_res["fixtures"]["played"]["total"]

            if home_played == 0 or away_played == 0:
                sugestao = "⚠ Dados de jogos jogados insuficientes para a sugestão de vitória."
            else:
                home_win_ratio = home_wins / home_played
                away_win_ratio = away_wins / away_played

                if home_win_ratio > away_win_ratio:
                    sugestao = f"✅ Sugestão: **Vitória do {home_name}** (Taxa de vitória superior)"
                elif away_win_ratio > home_win_ratio:
                    sugestao = f"✅ Sugestão: **Vitória do {away_name}** (Taxa de vitória superior)"
                else:
                    sugestao = "ℹ️ Sugestão: **Empate** ou equilíbrio de forças (Taxas de vitória similares)"

        elif mercado == "Over/Under Gols":
            # Média de gols marcados E sofridos para uma visão mais completa
            media_gols_marcados_home = float(home_stats_res["goals"]["for"]["average"]["total"])
            media_gols_sofridos_home = float(home_stats_res["goals"]["against"]["average"]["total"])
            media_gols_marcados_away = float(away_stats_res["goals"]["for"]["average"]["total"])
            media_gols_sofridos_away = float(away_stats_res["goals"]["against"]["average"]["total"])

            # Média total esperada de gols no jogo
            media_total_esperada = (media_gols_marcados_home + media_gols_sofridos_home + \
                                    media_gols_marcados_away + media_gols_sofridos_away) / 2 # Simplificação

            if media_total_esperada > 2.5:
                sugestao = f"✅ Sugestão: **Over 2.5 Gols** (Média esperada de {media_total_esperada:.2f} gols)"
            else:
                sugestao = f"✅ Sugestão: **Under 2.5 Gols** (Média esperada de {media_total_esperada:.2f} gols)"

        elif mercado == "Escanteios":
            # NOTA: A API-Football v3 não fornece estatísticas diretas de escanteios por time em 'teams/statistics'.
            # Esta seção é um exemplo de como seria se os dados estivessem disponíveis.
            # No código original, a lógica era uma estimativa fixa.
            # Para uma sugestão real, você precisaria de dados de escanteios (ex: endpoint de estatísticas de fixture ou dados de uma fonte alternativa).
            sugestao = "⚠ Não foi possível calcular escanteios com os dados de estatísticas atuais da API. (Exemplo: Se a API fornecesse 'corners_for', 'corners_against')"
            # Exemplo de como seria se os dados de escanteios estivessem disponíveis na API:
            # try:
            #     home_corners_avg = float(home_stats_res["corners"]["for"]["average"]["total"])
            #     away_corners_avg = float(away_stats_res["corners"]["for"]["average"]["total"])
            #     total_corners_avg = home_corners_avg + away_corners_avg
            #     if total_corners_avg > 9.5:
            #         sugestao = f"✅ Sugestão: Over 9.5 Escanteios (Média: {total_corners_avg:.2f})"
            #     else:
            #         sugestao = f"✅ Sugestão: Under 9.5 Escanteios (Média: {total_corners_avg:.2f})"
            # except KeyError:
            #     sugestao = "⚠ Dados de escanteios não disponíveis para este time/liga."

        elif mercado == "Gol HT/FT":
            # Lógica para HT/FT geralmente envolve desempenho em primeiros e segundos tempos.
            # A API-Football tem 'form' e 'fixtures/halfTime/wins' que poderiam ser usados.
            home_ht_wins = home_stats_res["fixtures"]["wins"]["halfTime"]["total"]
            away_ht_wins = away_stats_res["fixtures"]["wins"]["halfTime"]["total"]

            if home_ht_wins > away_ht_wins:
                sugestao = f"✅ Sugestão: **{home_name} vence HT e FT** (Mais vitórias no primeiro tempo)"
            elif away_ht_wins > home_ht_wins:
                sugestao = f"✅ Sugestão: **{away_name} vence HT e FT** (Mais vitórias no primeiro tempo)"
            else:
                sugestao = "ℹ️ Sugestão: **Sem clara vantagem para HT/FT**"

        elif mercado == "Placar Exato":
            sugestao = "🔍 **Placar Exato é muito volátil para uma sugestão simples**. Considere a média de gols e o desempenho defensivo/ofensivo para uma aposta mais informada."
            # Para placar exato, seriam necessários modelos preditivos mais avançados (Poisson Distribution, etc.)
            # e dados mais granulares como gols sofridos/marcados em casa/fora.

    except KeyError as ke:
        sugestao = f"⚠ Erro ao acessar dados da API (Chave ausente: {ke}). Sugestão indisponível."
    except Exception as e:
        sugestao = f"⚠ Não foi possível calcular sugestão para esse mercado devido a um erro: {e}."
    
    return sugestao

# --- INTERFACE --- #
if API_KEY:
    st.subheader("📅 Escolha a Data")
    data_escolhida = st.date_input("Selecione uma data", value=datetime.now().date())

    col1, col2 = st.columns(2)
    with col1:
        buscar_data = st.button("🔍 Buscar Jogos")
    with col2:
        buscar_amanha = st.button("📅 Jogos de Amanhã")

    dados = None
    if buscar_data:
        data_formatada = data_escolhida.strftime("%Y-%m-%d")
        with st.spinner(f"Buscando jogos para {data_formatada}..."):
            dados = buscar_jogos(data_formatada, headers)
    elif buscar_amanha: # Use elif para evitar buscas duplas se ambos forem clicados (raro, mas possível)
        data_amanha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        with st.spinner("Buscando jogos de amanhã..."):
            dados = buscar_jogos(data_amanha, headers)
    
    # Se a API Key foi inserida e o usuário não clicou em buscar ainda, não exibir nada
    if not (buscar_data or buscar_amanha) and not st.session_state.get('jogos_carregados'):
        st.info("Insira sua API Key e selecione uma data para buscar jogos.")
        
    # Processa os dados da busca
    if dados:
        if dados.get("error"):
            st.error(f"Erro na busca de jogos: {dados['error']}")
        elif dados.get("response"):
            jogos = []
            for jogo in dados["response"]:
                jogos.append({
                    "ID": jogo["fixture"]["id"],
                    "Liga": jogo["league"]["name"],
                    "Temporada": jogo["league"]["season"], # Adicionado para uso futuro nas estatísticas
                    "Casa": jogo["teams"]["home"]["name"],
                    "Visitante": jogo["teams"]["away"]["name"],
                    "Hora": datetime.fromisoformat(jogo["fixture"]["date"].replace("Z", "+00:00")).strftime("%H:%M")
                })
            
            if jogos:
                df = pd.DataFrame(jogos)
                st.dataframe(df, use_container_width=True)

                st.session_state['jogos_carregados'] = True # Sinaliza que jogos foram carregados
                st.session_state['dados_jogos_completos'] = dados # Salva os dados completos para fácil acesso

                jogo_id = st.selectbox("Selecione o ID do Jogo para Análise", df["ID"].tolist())
                mercado = st.selectbox("Escolha o Mercado de Aposta", 
                                       ["Vitória (1X2)", "Over/Under Gols", "Escanteios", "Gol HT/FT", "Placar Exato"])

                if st.button("🔍 Gerar Sugestão de Aposta"):
                    with st.spinner("Analisando dados para gerar sugestão..."):
                        # Pega o jogo completo dos dados originais para não perder detalhes
                        jogo_selecionado_completo = next((item for item in st.session_state['dados_jogos_completos']["response"] if item["fixture"]["id"] == jogo_id), None)

                        if jogo_selecionado_completo:
                            home_id = jogo_selecionado_completo["teams"]["home"]["id"]
                            away_id = jogo_selecionado_completo["teams"]["away"]["id"]
                            liga_id = jogo_selecionado_completo["league"]["id"]
                            temporada = jogo_selecionado_completo["league"]["season"]

                            stats_home = buscar_stats(home_id, liga_id, temporada, headers)
                            stats_away = buscar_stats(away_id, liga_id, temporada, headers)

                            sugestao = gerar_sugestao(mercado, stats_home, stats_away, jogo_selecionado_completo)
                            st.success(sugestao)
                        else:
                            st.error("Erro: Jogo selecionado não encontrado nos dados originais.")
            else:
                st.warning("Nenhum jogo encontrado para a data selecionada.")
                st.session_state['jogos_carregados'] = False
        else:
            st.warning("Nenhum jogo encontrado para a data selecionada.")
            st.session_state['jogos_carregados'] = False
elif not API_KEY:
    st.warning("Por favor, digite sua API Key da RapidAPI para continuar.")

