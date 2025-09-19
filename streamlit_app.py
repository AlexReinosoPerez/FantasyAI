"""
Fantasy LaLiga Assistant - Streamlit Frontend
Interfaz de usuario para el asistente de Fantasy LaLiga
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List

# Configuración de la página
st.set_page_config(
    page_title="Fantasy LaLiga Assistant",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL base de la API
API_BASE_URL = "http://localhost:8000"

def main():
    """Función principal de la aplicación Streamlit"""
    st.title("⚽ Fantasy LaLiga Assistant")
    st.markdown("**Asistente inteligente para Fantasy LaLiga con predicciones y recomendaciones**")
    
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    page = st.sidebar.selectbox(
        "Selecciona una sección:",
        ["🏠 Inicio", "👥 Mi Equipo", "📈 Análisis de Mercado", 
         "🔄 Recomendaciones", "🏆 Liga y Diferenciales"]
    )
    
    # Cargar datos de ejemplo
    if 'sample_team' not in st.session_state:
        st.session_state.sample_team = load_sample_team()
    
    # Renderizar página seleccionada
    if page == "🏠 Inicio":
        show_home_page()
    elif page == "👥 Mi Equipo":
        show_team_analysis()
    elif page == "📈 Análisis de Mercado":
        show_market_analysis()
    elif page == "🔄 Recomendaciones":
        show_recommendations()
    elif page == "🏆 Liga y Diferenciales":
        show_league_analysis()

def show_home_page():
    """Página de inicio con información general"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Bienvenido al Fantasy LaLiga Assistant")
        st.markdown("""
        ### 🎯 Características principales:
        
        **📊 Análisis Predictivo:**
        - Predicciones de puntos usando EMA (Media Móvil Exponencial)
        - Análisis de dificultad de fixtures
        - Probabilidad de titularidad
        
        **💰 Análisis de Valor:**
        - Cálculo de valor intrínseco de jugadores
        - Evaluación de riesgo detallada
        - Recomendaciones de puja máxima
        
        **🔄 Recomendaciones Inteligentes:**
        - Sugerencias de intercambios
        - Identificación de oportunidades
        - Análisis de jugadores diferenciales
        
        **🏆 Análisis de Liga:**
        - Comparación con rivales
        - Estrategias según posición
        - Identificación de diferenciales premium
        """)
        
        # Verificar estado de la API
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API conectada correctamente")
            else:
                st.error("❌ Error de conexión con la API")
        except:
            st.warning("⚠️ No se pudo conectar con la API. Asegúrate de que esté ejecutándose en el puerto 8000")
    
    with col2:
        st.header("Enlaces rápidos")
        if st.button("🚀 Analizar mi equipo", type="primary"):
            st.session_state.page = "👥 Mi Equipo"
            st.rerun()
        
        if st.button("📈 Ver mercado"):
            st.session_state.page = "📈 Análisis de Mercado"
            st.rerun()
            
        if st.button("💡 Obtener recomendaciones"):
            st.session_state.page = "🔄 Recomendaciones"
            st.rerun()

def show_team_analysis():
    """Análisis del equipo del usuario"""
    st.header("👥 Análisis de Mi Equipo")
    
    # Mostrar equipo actual
    team_data = st.session_state.sample_team
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Valor Total", f"{team_data['total_value']:.1f}M")
    with col2:
        st.metric("Presupuesto", f"{team_data['budget']:.1f}M")
    with col3:
        st.metric("Formación", team_data['formation'])
    
    # Tabla de jugadores
    st.subheader("Plantilla Actual")
    players_df = pd.DataFrame(team_data['players'])
    
    # Formatear datos para mejor visualización
    display_df = players_df[['name', 'team', 'position', 'price', 'points', 'avg_points', 'ownership']].copy()
    display_df['price'] = display_df['price'].apply(lambda x: f"{x:.1f}M")
    display_df['ownership'] = display_df['ownership'].apply(lambda x: f"{x:.1f}%")
    display_df.columns = ['Jugador', 'Equipo', 'Pos', 'Precio', 'Puntos', 'Media', 'Propiedad']
    
    st.dataframe(display_df, use_container_width=True)
    
    # Análisis con API
    if st.button("🔍 Analizar Equipo", type="primary"):
        with st.spinner("Analizando equipo..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analysis/myteam",
                    json=team_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    analysis = response.json()
                    show_team_analysis_results(analysis)
                else:
                    st.error(f"Error en análisis: {response.status_code}")
            except Exception as e:
                st.error(f"Error conectando con API: {str(e)}")

def show_team_analysis_results(analysis: Dict):
    """Mostrar resultados del análisis del equipo"""
    st.subheader("📊 Resultados del Análisis")
    
    # Métricas principales
    summary = analysis['team_summary']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Puntos Predichos", f"{summary['total_predicted_points']:.1f}")
    with col2:
        st.metric("Confianza Media", f"{summary['average_confidence']:.1%}")
    with col3:
        st.metric("Valor Total", f"{summary['total_value']:.1f}M")
    with col4:
        st.metric("Presupuesto", f"{summary['budget_available']:.1f}M")
    
    # Análisis por posición
    st.subheader("📈 Análisis por Posición")
    pos_analysis = analysis['position_analysis']
    
    if pos_analysis:
        pos_df = pd.DataFrame.from_dict(pos_analysis, orient='index')
        pos_df.index.name = 'Posición'
        st.dataframe(pos_df.round(2))
        
        # Gráfico de puntos predichos por posición
        fig = px.bar(
            x=pos_df.index,
            y=pos_df['predicted_points'],
            title="Puntos Predichos por Posición",
            labels={'x': 'Posición', 'y': 'Puntos Predichos'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Predicciones individuales
    st.subheader("🎯 Predicciones por Jugador")
    predictions_df = pd.DataFrame(analysis['player_predictions'])
    predictions_df = predictions_df.round(2)
    st.dataframe(predictions_df, use_container_width=True)
    
    # Problemas identificados
    if analysis['issues_identified']:
        st.subheader("⚠️ Problemas Identificados")
        for issue in analysis['issues_identified']:
            st.warning(f"**{issue['name']}**: {issue['issue']}")
    
    # Recomendaciones
    if analysis['recommendations']:
        st.subheader("💡 Recomendaciones")
        for rec in analysis['recommendations']:
            st.info(rec)

def show_market_analysis():
    """Análisis del mercado de fichajes"""
    st.header("📈 Análisis de Mercado")
    
    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        position_filter = st.selectbox(
            "Posición",
            ["Todas", "POR", "DEF", "CEN", "DEL"]
        )
    
    with col2:
        min_price = st.number_input("Precio mínimo (M)", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
    
    with col3:
        max_price = st.number_input("Precio máximo (M)", min_value=0.0, max_value=20.0, value=20.0, step=0.5)
    
    with col4:
        max_ownership = st.number_input("Máx. propiedad (%)", min_value=0.0, max_value=100.0, value=100.0, step=5.0)
    
    if st.button("🔍 Analizar Mercado", type="primary"):
        with st.spinner("Analizando mercado..."):
            try:
                # Preparar parámetros
                params = {}
                if position_filter != "Todas":
                    params['position'] = position_filter
                if min_price > 0:
                    params['min_price'] = min_price
                if max_price < 20:
                    params['max_price'] = max_price
                if max_ownership < 100:
                    params['max_ownership'] = max_ownership
                
                response = requests.get(
                    f"{API_BASE_URL}/analysis/market",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    market_analysis = response.json()
                    show_market_analysis_results(market_analysis)
                else:
                    st.error(f"Error en análisis: {response.status_code}")
            except Exception as e:
                st.error(f"Error conectando con API: {str(e)}")

def show_market_analysis_results(analysis: Dict):
    """Mostrar resultados del análisis de mercado"""
    st.subheader("📊 Resumen del Mercado")
    
    summary = analysis['market_summary']
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Jugadores Analizados", summary['total_players_analyzed'])
    with col2:
        st.metric("Precio Promedio", f"{summary['average_price']:.1f}M")
    with col3:
        st.metric("Propiedad Promedio", f"{summary['average_ownership']:.1f}%")
    
    # Top oportunidades
    st.subheader("🎯 Top Oportunidades")
    opportunities_df = pd.DataFrame(analysis['top_opportunities'])
    if not opportunities_df.empty:
        display_cols = ['name', 'position', 'price', 'predicted_points', 'value_score', 'composite_score', 'recommendation']
        st.dataframe(opportunities_df[display_cols].round(2), use_container_width=True)
    
    # Categorías especiales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⭐ Estrellas Emergentes")
        if analysis['rising_stars']:
            for star in analysis['rising_stars']:
                st.success(f"**{star['name']}** - Puntuación: {star['composite_score']:.2f}")
        else:
            st.info("No se encontraron estrellas emergentes con los filtros actuales")
    
    with col2:
        st.subheader("💎 Mejores Valores")
        if analysis['value_picks']:
            for pick in analysis['value_picks']:
                st.success(f"**{pick['name']}** - Valor: {pick['value_score']:.2f}")
        else:
            st.info("No se encontraron valores destacados con los filtros actuales")

def show_recommendations():
    """Mostrar recomendaciones de intercambios y pujas"""
    st.header("🔄 Recomendaciones")
    
    tab1, tab2 = st.tabs(["Intercambios", "Pujas"])
    
    with tab1:
        show_swap_recommendations()
    
    with tab2:
        show_bid_recommendations()

def show_swap_recommendations():
    """Recomendaciones de intercambios"""
    st.subheader("🔄 Recomendaciones de Intercambios")
    
    col1, col2 = st.columns(2)
    with col1:
        budget_constraint = st.number_input("Presupuesto adicional (M)", min_value=0.0, max_value=10.0, value=1.0)
    with col2:
        risk_tolerance = st.selectbox("Tolerancia al riesgo", ["low", "medium", "high"], index=1)
    
    if st.button("💡 Generar Recomendaciones de Intercambio", type="primary"):
        with st.spinner("Generando recomendaciones..."):
            try:
                team_data = st.session_state.sample_team
                request_data = {
                    "current_team": team_data,
                    "budget_constraint": budget_constraint,
                    "risk_tolerance": risk_tolerance
                }
                
                response = requests.post(
                    f"{API_BASE_URL}/recommend/swaps",
                    json=request_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    recommendations = response.json()
                    show_swap_results(recommendations)
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_swap_results(recommendations: Dict):
    """Mostrar resultados de recomendaciones de intercambio"""
    st.subheader("📋 Recomendaciones de Intercambio")
    
    # Resumen
    summary = recommendations['summary']
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Recomendaciones", summary['total_recommendations'])
    with col2:
        st.metric("Jugadores Débiles", summary['weak_players_identified'])
    with col3:
        st.metric("Tolerancia al Riesgo", summary['risk_tolerance'])
    
    # Recomendaciones detalladas
    if recommendations['swap_recommendations']:
        for i, swap in enumerate(recommendations['swap_recommendations'][:5]):  # Top 5
            with st.expander(f"Intercambio {i+1}: {swap['player_out']['name']} → {swap['player_in']['name']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Jugador a vender:**")
                    st.write(f"• {swap['player_out']['name']}")
                    st.write(f"• Precio: {swap['player_out']['price']:.1f}M")
                    st.write(f"• Puntos predichos: {swap['player_out']['predicted_points']:.1f}")
                
                with col2:
                    st.write("**Jugador a comprar:**")
                    st.write(f"• {swap['player_in']['name']}")
                    st.write(f"• Precio: {swap['player_in']['price']:.1f}M")
                    st.write(f"• Puntos predichos: {swap['player_in']['predicted_points']:.1f}")
                
                st.write(f"**Ganancia esperada:** +{swap['swap_details']['expected_points_gain']} puntos")
                st.write(f"**Costo:** {swap['cost_difference']:+.1f}M")
                st.write(f"**Riesgo:** {swap['swap_details']['risk_level']}")
                st.write(f"**Razón:** {swap['swap_details']['reason']}")
    else:
        st.info("No se encontraron recomendaciones de intercambio en este momento")
    
    # Consejos generales
    if recommendations['general_advice']:
        st.subheader("💡 Consejos Generales")
        for advice in recommendations['general_advice']:
            st.info(advice)

def show_bid_recommendations():
    """Recomendaciones de pujas"""
    st.subheader("💰 Recomendaciones de Pujas")
    
    col1, col2 = st.columns(2)
    with col1:
        budget = st.number_input("Presupuesto disponible (M)", min_value=0.0, max_value=50.0, value=10.0)
    with col2:
        risk_tolerance = st.selectbox("Tolerancia al riesgo", ["low", "medium", "high"], index=1, key="bid_risk")
    
    if st.button("💡 Generar Recomendaciones de Puja", type="primary"):
        with st.spinner("Generando recomendaciones..."):
            try:
                team_data = st.session_state.sample_team
                request_data = {
                    "current_team": team_data,
                    "budget": budget,
                    "risk_tolerance": risk_tolerance
                }
                
                response = requests.post(
                    f"{API_BASE_URL}/recommend/bids",
                    json=request_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    recommendations = response.json()
                    show_bid_results(recommendations)
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_bid_results(recommendations: Dict):
    """Mostrar resultados de recomendaciones de puja"""
    st.subheader("📋 Recomendaciones de Puja")
    
    # Resumen de presupuesto
    budget_summary = recommendations['budget_summary']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Presupuesto Total", f"{budget_summary['total_budget']:.1f}M")
    with col2:
        st.metric("Gasto Recomendado", f"{budget_summary['recommended_spend']:.1f}M")
    with col3:
        st.metric("Presupuesto Restante", f"{budget_summary['remaining_budget']:.1f}M")
    with col4:
        st.metric("Utilización", f"{budget_summary['budget_utilization']:.1f}%")
    
    # Recomendaciones de puja
    if recommendations['bid_recommendations']:
        st.subheader("🎯 Pujas Recomendadas")
        
        for i, bid in enumerate(recommendations['bid_recommendations'][:5]):
            with st.expander(f"Puja {i+1}: {bid['player_info']['name']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Información del Jugador:**")
                    st.write(f"• Nombre: {bid['player_info']['name']}")
                    st.write(f"• Posición: {bid['player_info']['position']}")
                    st.write(f"• Precio actual: {bid['player_info']['current_price']:.1f}M")
                    st.write(f"• Propiedad: {bid['player_info']['ownership']:.1f}%")
                
                with col2:
                    st.write("**Análisis de Puja:**")
                    st.write(f"• Puja máxima: {bid['bid_details']['max_bid']:.1f}M")
                    st.write(f"• Puntos esperados: {bid['bid_details']['expected_return']:.1f}")
                    st.write(f"• Evaluación de riesgo: {bid['bid_details']['risk_assessment']}")
                    st.write(f"• Asequible: {'✅' if bid['affordable'] else '❌'}")
                
                st.write(f"**Justificación:** {bid['bid_details']['reasoning']}")
    else:
        st.info("No se encontraron oportunidades de puja atractivas")

def show_league_analysis():
    """Análisis de liga y diferenciales"""
    st.header("🏆 Liga y Diferenciales")
    
    # Configuración de liga
    col1, col2 = st.columns(2)
    with col1:
        league_id = st.text_input("ID de Liga", value="liga_ejemplo_123")
    with col2:
        target_positions = st.multiselect(
            "Posiciones objetivo",
            ["POR", "DEF", "CEN", "DEL"],
            default=["DEL", "CEN"]
        )
    
    # Filtros de propiedad
    col1, col2 = st.columns(2)
    with col1:
        min_ownership = st.slider("Propiedad mínima (%)", 0, 100, 0)
    with col2:
        max_ownership = st.slider("Propiedad máxima (%)", 0, 100, 30)
    
    if st.button("🔍 Analizar Diferenciales", type="primary"):
        with st.spinner("Analizando diferenciales..."):
            try:
                team_data = st.session_state.sample_team
                player_ids = [p['id'] for p in team_data['players']]
                
                request_data = {
                    "league_id": league_id,
                    "user_team_players": player_ids,
                    "min_ownership": min_ownership,
                    "max_ownership": max_ownership,
                    "target_positions": target_positions if target_positions else None
                }
                
                response = requests.post(
                    f"{API_BASE_URL}/league/differentials",
                    json=request_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    analysis = response.json()
                    show_differential_results(analysis)
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_differential_results(analysis: Dict):
    """Mostrar resultados de análisis de diferenciales"""
    st.subheader("📊 Análisis de Diferenciales")
    
    # Resumen
    league_analysis = analysis['league_analysis']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Diferenciales", league_analysis['total_differentials_found'])
    with col2:
        st.metric("Premium", league_analysis['premium_differentials'])
    with col3:
        st.metric("Valor", league_analysis['value_differentials'])
    with col4:
        st.metric("Presupuesto", league_analysis['budget_differentials'])
    
    # Top diferenciales
    st.subheader("🎯 Top Diferenciales")
    if analysis['top_differentials']:
        for i, diff in enumerate(analysis['top_differentials'][:5]):
            with st.expander(f"{i+1}. {diff['player_details']['name']} ({diff['player_details']['position']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Información Básica:**")
                    st.write(f"• Equipo: {diff['player_details']['team']}")
                    st.write(f"• Precio: {diff['player_details']['price']:.1f}M")
                    st.write(f"• Propiedad: {diff['player_details']['ownership']:.1f}%")
                
                with col2:
                    st.write("**Métricas de Rendimiento:**")
                    st.write(f"• Puntos predichos: {diff['performance_metrics']['predicted_points']:.1f}")
                    st.write(f"• Confianza: {diff['performance_metrics']['confidence']:.1%}")
                    st.write(f"• Puntuación valor: {diff['performance_metrics']['value_score']:.2f}")
                
                with col3:
                    st.write("**Análisis Diferencial:**")
                    st.write(f"• Puntuación: {diff['differential_info']['differential_score']:.2f}")
                    st.write(f"• Impacto liga: {diff['differential_analysis']['league_impact']}")
                    st.write(f"• Recomendación: {diff['differential_info']['recommendation']}")
    
    # Estadísticas de liga
    if 'league_stats' in analysis:
        st.subheader("📈 Estadísticas de Liga")
        stats = analysis['league_stats']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tu Posición", f"{stats['your_rank']}")
        with col2:
            st.metric("Total Jugadores", f"{stats['total_players']}")
        with col3:
            st.metric("Puntos Atrás", f"{stats['points_behind_leader']}")
        with col4:
            st.metric("Puntos Promedio", f"{stats['average_points']}")
    
    # Consejos estratégicos
    if analysis['strategic_advice']:
        st.subheader("💡 Consejos Estratégicos")
        for advice in analysis['strategic_advice']:
            st.info(advice)

def load_sample_team():
    """Cargar equipo de ejemplo"""
    try:
        with open('/home/runner/work/FantasyAI/FantasyAI/data/sample_team.json', 'r') as f:
            team_data = json.load(f)
        
        # Calcular valor total
        total_value = sum(player['price'] for player in team_data['players'])
        team_data['total_value'] = total_value
        
        return team_data
    except:
        # Equipo básico de fallback
        return {
            "user_id": "demo_user",
            "formation": "4-4-2",
            "budget": 5.0,
            "total_value": 85.0,
            "players": []
        }

if __name__ == "__main__":
    main()