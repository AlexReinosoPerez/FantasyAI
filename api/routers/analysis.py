"""
Analysis API Router
Endpoints para análisis de equipo y mercado
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
import json

from core.models import Team, Player, MarketData, PlayerPrediction
from core.prediction_engine import PredictionEngine
from core.value_calculator import ValueRiskCalculator

router = APIRouter()
prediction_engine = PredictionEngine()
value_calculator = ValueRiskCalculator()

@router.post("/myteam")
async def analyze_my_team(team: Team):
    """
    Analizar el equipo del usuario
    
    Proporciona análisis detallado del equipo incluyendo:
    - Predicciones de puntos para cada jugador
    - Análisis de valor y riesgo
    - Recomendaciones de mejora
    """
    try:
        # Generar predicciones para todos los jugadores
        predictions = prediction_engine.predict_multiple_players(team.players)
        
        # Calcular métricas del equipo
        total_predicted_points = sum(pred.predicted_points for pred in predictions)
        avg_confidence = sum(pred.confidence for pred in predictions) / len(predictions)
        
        # Análisis de valor por posición
        position_analysis = {}
        for position in ["POR", "DEF", "CEN", "DEL"]:
            position_players = [p for p in team.players if p.position.value == position]
            if position_players:
                position_predictions = [pred for pred in predictions if any(p.id == pred.player_id for p in position_players)]
                position_analysis[position] = {
                    "player_count": len(position_players),
                    "total_value": sum(p.price for p in position_players),
                    "predicted_points": sum(pred.predicted_points for pred in position_predictions),
                    "avg_confidence": sum(pred.confidence for pred in position_predictions) / len(position_predictions)
                }
        
        # Identificar jugadores problemáticos
        low_performers = []
        for player, prediction in zip(team.players, predictions):
            if prediction.predicted_points < 2.0 or prediction.confidence < 0.4:
                low_performers.append({
                    "player_id": player.id,
                    "name": player.name,
                    "issue": "Bajo rendimiento esperado" if prediction.predicted_points < 2.0 else "Baja confianza en predicción",
                    "predicted_points": prediction.predicted_points,
                    "confidence": prediction.confidence
                })
        
        # Recomendaciones generales
        recommendations = []
        if total_predicted_points < 40:
            recommendations.append("Considera reforzar el equipo - puntuación esperada baja")
        if avg_confidence < 0.6:
            recommendations.append("Muchos jugadores con predicciones inciertas - considera cambios")
        if team.budget > 5.0:
            recommendations.append(f"Tienes {team.budget}M disponibles - considera invertir en mejores jugadores")
        
        return {
            "team_summary": {
                "total_value": team.total_value,
                "budget_available": team.budget,
                "formation": team.formation,
                "total_predicted_points": round(total_predicted_points, 2),
                "average_confidence": round(avg_confidence, 2)
            },
            "position_analysis": position_analysis,
            "player_predictions": [
                {
                    "player_id": pred.player_id,
                    "player_name": next(p.name for p in team.players if p.id == pred.player_id),
                    "predicted_points": pred.predicted_points,
                    "confidence": pred.confidence,
                    "ema_points": pred.ema_points,
                    "fixture_adjusted": pred.fixture_adjusted_points
                }
                for pred in predictions
            ],
            "issues_identified": low_performers,
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing team: {str(e)}")

@router.get("/market")
async def analyze_market(
    position: Optional[str] = Query(None, description="Filtrar por posición (POR, DEF, CEN, DEL)"),
    min_price: Optional[float] = Query(None, description="Precio mínimo en millones"),
    max_price: Optional[float] = Query(None, description="Precio máximo en millones"),
    max_ownership: Optional[float] = Query(None, description="Máximo porcentaje de propiedad")
):
    """
    Analizar el mercado de fichajes
    
    Proporciona análisis del mercado incluyendo:
    - Mejores oportunidades de valor
    - Jugadores con buen potencial
    - Análisis de tendencias de precios
    """
    try:
        # Datos de ejemplo del mercado (en implementación real vendría de BD/API)
        market_players = _get_sample_market_players()
        
        # Aplicar filtros
        filtered_players = market_players
        if position:
            filtered_players = [p for p in filtered_players if p.position.value == position]
        if min_price:
            filtered_players = [p for p in filtered_players if p.price >= min_price]
        if max_price:
            filtered_players = [p for p in filtered_players if p.price <= max_price]
        if max_ownership:
            filtered_players = [p for p in filtered_players if p.ownership <= max_ownership]
        
        # Generar predicciones
        predictions = prediction_engine.predict_multiple_players(filtered_players)
        
        # Análisis de valor
        player_comparisons = value_calculator.compare_players(filtered_players, predictions)
        
        # Identificar tendencias
        rising_stars = [p for p in player_comparisons if p['composite_score'] > 0.7 and filtered_players[player_comparisons.index(p)].ownership < 20]
        value_picks = [p for p in player_comparisons if p['value_score'] > 0.8]
        differential_picks = [p for p in player_comparisons if filtered_players[player_comparisons.index(p)].ownership < 10 and p['predicted_points'] > 4]
        
        return {
            "market_summary": {
                "total_players_analyzed": len(filtered_players),
                "average_price": round(sum(p.price for p in filtered_players) / len(filtered_players), 2) if filtered_players else 0,
                "average_ownership": round(sum(p.ownership for p in filtered_players) / len(filtered_players), 2) if filtered_players else 0
            },
            "top_opportunities": player_comparisons[:10],  # Top 10 mejores oportunidades
            "rising_stars": rising_stars[:5],  # Top 5 estrellas emergentes
            "value_picks": value_picks[:5],    # Top 5 mejores valores
            "differential_picks": differential_picks[:5],  # Top 5 diferenciales
            "filters_applied": {
                "position": position,
                "min_price": min_price,
                "max_price": max_price,
                "max_ownership": max_ownership
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing market: {str(e)}")

def _get_sample_market_players() -> List[Player]:
    """Generar datos de ejemplo del mercado"""
    # En implementación real, esto vendría de una base de datos o API externa
    sample_players = [
        Player(
            id=1, name="Vinicius Jr", team="Real Madrid", position="DEL",
            price=12.5, points=180, avg_points=6.5, form=[8, 6, 9, 7, 8],
            ownership=45.2, fixture_difficulty=2
        ),
        Player(
            id=2, name="Pedri", team="Barcelona", position="CEN", 
            price=8.5, points=120, avg_points=4.8, form=[5, 4, 6, 5, 3],
            ownership=22.1, fixture_difficulty=3
        ),
        Player(
            id=3, name="Militão", team="Real Madrid", position="DEF",
            price=6.5, points=95, avg_points=3.8, form=[4, 5, 3, 4, 6],
            ownership=18.5, fixture_difficulty=2
        ),
        Player(
            id=4, name="Ter Stegen", team="Barcelona", position="POR",
            price=5.5, points=110, avg_points=4.4, form=[6, 4, 5, 6, 5],
            ownership=35.8, fixture_difficulty=3
        ),
        Player(
            id=5, name="Mikel Oyarzabal", team="Real Sociedad", position="DEL",
            price=7.8, points=140, avg_points=5.6, form=[7, 5, 8, 6, 7],
            ownership=12.3, fixture_difficulty=4
        ),
        Player(
            id=6, name="Koke", team="Atlético Madrid", position="CEN",
            price=6.2, points=85, avg_points=3.4, form=[3, 4, 2, 5, 4],
            ownership=8.7, fixture_difficulty=5
        ),
        Player(
            id=7, name="Jules Koundé", team="Barcelona", position="DEF",
            price=6.8, points=102, avg_points=4.1, form=[5, 3, 4, 5, 4],
            ownership=25.6, fixture_difficulty=3
        ),
        Player(
            id=8, name="Iago Aspas", team="Celta Vigo", position="DEL",
            price=9.2, points=155, avg_points=6.2, form=[6, 8, 5, 7, 6],
            ownership=15.4, fixture_difficulty=1
        )
    ]
    
    return sample_players