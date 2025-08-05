import streamlit as st
import pandas as pd

st.set_page_config(page_title="Football Analyzer Pro", layout="wide")

st.title("⚽ Football Analyzer Pro")
st.subheader("Análise avançada: Under/Over, Escanteios e Resultado Final")

st.markdown("---")

# Dados básicos
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

# Dados adicionais
st.markdown("### 📊 Detalhes Avançados")
col3, col4 = st.columns(2)
with col3:
    xg_home = st.number_input("xG Mandante", 0.0, 5.0, step=0.1)
    win_rate_home = st.number_input("Taxa de Vitórias Casa (%)", 0.0, 100.0, step=1.0)
with col4:
    xg_away = st.number_input("xG Visitante", 0.0, 5.0, step=0.1)
    win_rate_away = st.number_input("Taxa de Vitórias Fora (%)", 0.0, 100.0, step=1.0)

# Análise
if st.button("🔍 Analisar Partida"):
    st.markdown("---")
    st.subheader("📈 Resultados da Análise")

    # UNDER/OVER
    avg_goals_total = avg_goals_home + avg_goals_away
    st.markdown(f"### 🔸 Mercado Under/Over")
    st.write(f"Média total de gols: **{avg_goals_total:.2f}**")
    if avg_goals_total >= 2.7:
        st.success("✅ Tendência de Over 2.5 gols")
    elif avg_goals_total <= 2.0:
        st.warning("⚠️ Tendência de Under 2.5 gols")
    else:
        st.info("🔍 Jogo com tendência neutra (analisar ao vivo)")

    # ESCANTEIOS
    total_corners = avg_corners_home + avg_corners_away
    st.markdown("### 🔸 Mercado de Escanteios")
    st.write(f"Média total de escanteios: **{total_corners:.2f}**")
    if total_corners >= 10:
        st.success("✅ Tendência de Over 9.5 cantos")
    elif total_corners <= 8:
        st.warning("⚠️ Tendência de Under 9.5 cantos")
    else:
        st.info("🔍 Escanteios equilibrados (ver escalações e pressão ofensiva)")

    # RESULTADO FINAL
    st.markdown("### 🔸 Mercado de Resultado Final (1X2)")
    if win_rate_home > win_rate_away:
        st.success(f"✅ Tendência de vitória para o {team_home}")
    elif win_rate_away > win_rate_home:
        st.success(f"✅ Tendência de vitória para o {team_away}")
    else:
        st.info("🔍 Jogo equilibrado, possibilidade de empate")

    # Conclusão
    st.markdown("---")
    st.subheader("🎯 Sugestões:")
    st.markdown("- ✅ **Over 2.5 gols** se média total for alta e xG > 1.2 para ambos")
    st.markdown("- ✅ **Over 9.5 cantos** se total médio de cantos for > 10")
    st.markdown("- ✅ **Vitória mandante/visitante** com taxa de vitória acima de 60%")
    st.markdown("- 📌 Acompanhe ao vivo: posse de bola, chutes, cantos ao vivo para confirmação.")

---

### 🔧 PRÓXIMOS PASSOS (se quiser evoluir o app):
- [ ] Conectar com **API de dados reais (Sofascore, Footystats)**
- [ ] Adicionar **salvamento de análises**
- [ ] Exportar para **APK Android**
- [ ] Adicionar **IA preditiva automática**

---

📂 **Deseja que eu gere o arquivo `.py` ou `apk` agora?**  
Ou quer adicionar mais alguma funcionalidade antes?
