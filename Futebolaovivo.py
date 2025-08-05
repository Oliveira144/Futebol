import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Analyzer Pro", layout="wide")

st.title("⚽ Football Analyzer Pro")
st.subheader("Análise Avançada: Under/Over, Escanteios e Resultado Final")
st.markdown("---")

# ▶️ Entrada de dados
st.header("📋 Informações da Partida")
col1, col2 = st.columns(2)

with col1:
    team_home = st.text_input("Time Mandante")
    avg_goals_home = st.number_input("Média de Gols Marcados (Casa)", 0.0, 10.0, step=0.1)
    avg_corners_home = st.number_input("Média de Escanteios (Casa)", 0.0, 20.0, step=0.1)

with col2:
    team_away = st.text_input("Time Visitante")
    avg_goals_away = st.number_input("Média de Gols Marcados (Fora)", 0.0, 10.0, step=0.1)
    avg_corners_away = st.number_input("Média de Escanteios (Fora)", 0.0, 20.0, step=0.1)

st.markdown("### 📊 Dados Avançados")
col3, col4 = st.columns(2)

with col3:
    xg_home = st.number_input("xG Mandante", 0.0, 5.0, step=0.1)
    win_rate_home = st.number_input("Taxa de Vitórias Casa (%)", 0.0, 100.0, step=1.0)

with col4:
    xg_away = st.number_input("xG Visitante", 0.0, 5.0, step=0.1)
    win_rate_away = st.number_input("Taxa de Vitórias Fora (%)", 0.0, 100.0, step=1.0)

# ▶️ Processar Análise
if st.button("🔍 Analisar Partida"):
    st.markdown("---")
    st.subheader("📈 Resultados da Análise")

    # Análise de Gols (Under/Over)
    st.markdown("### ⚽ Under/Over")
    avg_goals_total = avg_goals_home + avg_goals_away
    st.write(f"Média total de gols esperados: **{avg_goals_total:.2f}**")

    if avg_goals_total >= 2.7 and xg_home > 1.2 and xg_away > 1.2:
        st.success("✅ Forte tendência de Over 2.5 gols")
    elif avg_goals_total <= 2.0:
        st.warning("⚠️ Tendência de Under 2.5 gols")
    else:
        st.info("🔍 Zona neutra: analisar ao vivo")

    # Análise de Escanteios
    st.markdown("### 🥅 Escanteios")
    total_corners = avg_corners_home + avg_corners_away
    st.write(f"Média total de escanteios esperados: **{total_corners:.2f}**")

    if total_corners >= 10:
        st.success("✅ Boa tendência de Over 9.5 escanteios")
    elif total_corners <= 8:
        st.warning("⚠️ Tendência de Under 9.5 escanteios")
    else:
        st.info("🔍 Média de cantos equilibrada")

    # Análise de Resultado Final
    st.markdown("### 🧮 Resultado Final (1X2)")
    if win_rate_home > win_rate_away and win_rate_home >= 60:
        st.success(f"✅ Tendência de vitória do {team_home}")
    elif win_rate_away > win_rate_home and win_rate_away >= 60:
        st.success(f"✅ Tendência de vitória do {team_away}")
    else:
        st.info("🔍 Jogo equilibrado ou sem favorito claro")

    # Conclusão
    st.markdown("---")
    st.subheader("🎯 Sugestões com base nos dados:")
    if avg_goals_total >= 2.7:
        st.markdown("- **Over 2.5 gols** como principal linha de gols")
    if total_corners >= 10:
        st.markdown("- **Over 9.5 escanteios** com consistência estatística")
    if win_rate_home >= 60 or win_rate_away >= 60:
        st.markdown("- **Back no favorito** com taxa de vitória alta")
    st.markdown("- 📌 *Sugestões devem ser reforçadas com análise ao vivo.*")

st.markdown("---")
st.caption("Desenvolvido por Football Analyzer Pro • Streamlit App")
