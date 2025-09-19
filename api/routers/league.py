"""
League API Router
Endpoints para análisis de liga y jugadores diferenciales
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel

from core.models import Player, Differential, LeagueStats
from core.prediction_engine import PredictionEngine
from core.value_calculator import ValueRiskCalculator

router = APIRouter()
prediction_engine = PredictionEngine()
value_calculator = ValueRiskCalculator()

class LeagueRequest(BaseModel):
    """Request para análisis de liga"""
    league_id: str
    user_team_players: List[int]  # IDs de jugadores del usuario
    min_ownership: float = 0.0
    max_ownership: float = 100.0
    target_positions: Optional[List[str]] = None

@router.post("/differentials")
async def analyze_differentials(request: LeagueRequest):
    """
    Analizar jugadores diferenciales en la liga
    
    Identifica jugadores con baja propiedad pero alto potencial
    para obtener ventajas competitivas en la liga.
    """
    try:
        # Obtener jugadores del mercado
        all_players = _get_sample_market_players()
        
        # Filtrar por criterios
        filtered_players = all_players
        if request.target_positions:
            filtered_players = [p for p in filtered_players if p.position.value in request.target_positions]
        
        filtered_players = [
            p for p in filtered_players 
            if request.min_ownership <= p.ownership <= request.max_ownership
        ]
        
        # Excluir jugadores que ya tiene el usuario
        user_player_ids = set(request.user_team_players)
        available_players = [p for p in filtered_players if p.id not in user_player_ids]
        
        # Generar predicciones
        predictions = prediction_engine.predict_multiple_players(available_players)
        
        # Calcular puntuaciones diferenciales
        differentials = []
        for player, prediction in zip(available_players, predictions):
            differential_score = _calculate_differential_score(player, prediction)
            recommendation = _get_differential_recommendation(player, prediction, differential_score)
            
            differentials.append(Differential(
                player_id=player.id,
                ownership_percentage=player.ownership,
                expected_points=prediction.predicted_points,
                differential_score=differential_score,
                recommendation=recommendation
            ))
        
        # Ordenar por puntuación diferencial
        differentials.sort(key=lambda x: x.differential_score, reverse=True)
        
        # Categorizar diferenciales
        premium_differentials = [d for d in differentials if d.differential_score > 0.8 and d.ownership_percentage < 5]
        value_differentials = [d for d in differentials if d.differential_score > 0.6 and d.ownership_percentage < 15]
        budget_differentials = [d for d in differentials if d.differential_score > 0.4 and d.ownership_percentage < 25]
        
        # Preparar respuesta detallada
        detailed_differentials = []
        for diff in differentials[:20]:  # Top 20
            player = next(p for p in available_players if p.id == diff.player_id)
            prediction = next(p for p in predictions if p.player_id == diff.player_id)
            
            # Análisis de valor
            value_analysis = value_calculator.calculate_player_value(player, prediction)
            risk_analysis = value_calculator.calculate_risk_score(player)
            
            detailed_differentials.append({
                "differential_info": diff.dict(),
                "player_details": {
                    "id": player.id,
                    "name": player.name,
                    "team": player.team,
                    "position": player.position.value,
                    "price": player.price,
                    "ownership": player.ownership,
                    "form": player.form
                },
                "performance_metrics": {
                    "predicted_points": prediction.predicted_points,
                    "confidence": prediction.confidence,
                    "ema_points": prediction.ema_points,
                    "value_score": value_analysis,
                    "risk_score": risk_analysis["total"]
                },
                "differential_analysis": {
                    "potential_gain": _calculate_potential_gain(player, prediction),
                    "risk_reward_ratio": _calculate_risk_reward_ratio(value_analysis, risk_analysis["total"]),
                    "league_impact": _assess_league_impact(diff.differential_score, player.ownership)
                }
            })
        
        # Estadísticas de la liga (simuladas)
        league_stats = _get_sample_league_stats(request.league_id)
        
        return {
            "league_analysis": {
                "league_id": request.league_id,
                "total_differentials_found": len(differentials),
                "premium_differentials": len(premium_differentials),
                "value_differentials": len(value_differentials),
                "budget_differentials": len(budget_differentials)
            },
            "top_differentials": detailed_differentials[:10],
            "category_breakdowns": {
                "premium": [
                    {
                        "player_id": d.player_id,
                        "name": next(p.name for p in available_players if p.id == d.player_id),
                        "ownership": d.ownership_percentage,
                        "score": d.differential_score
                    }
                    for d in premium_differentials[:5]
                ],
                "value": [
                    {
                        "player_id": d.player_id,
                        "name": next(p.name for p in available_players if p.id == d.player_id),
                        "ownership": d.ownership_percentage,
                        "score": d.differential_score
                    }
                    for d in value_differentials[:5]
                ],
                "budget": [
                    {
                        "player_id": d.player_id,
                        "name": next(p.name for p in available_players if p.id == d.player_id),
                        "ownership": d.ownership_percentage,
                        "score": d.differential_score
                    }
                    for d in budget_differentials[:5]
                ]
            },
            "league_stats": league_stats.dict(),
            "strategic_advice": _generate_differential_advice(differentials, league_stats)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing differentials: {str(e)}")

@router.get("/stats/{league_id}")
async def get_league_stats(league_id: str):
    """
    Obtener estadísticas generales de la liga
    
    Proporciona métricas clave de rendimiento y posicionamiento en la liga.
    """
    try:
        league_stats = _get_sample_league_stats(league_id)
        
        # Análisis adicional de tendencias
        trends_analysis = {
            "average_weekly_score": 65,  # Puntuación media semanal
            "score_volatility": "media",  # Volatilidad de puntuaciones
            "top_scorer_consistency": 0.75,  # Consistencia del líder
            "competitive_balance": 0.8  # Balance competitivo (0-1)
        }
        
        # Recommendations basadas en posición
        position_advice = []
        if league_stats.your_rank <= 3:
            position_advice.append("Mantén estrategia conservadora - estás en zona de liderazgo")
            position_advice.append("Considera diferenciales de bajo riesgo para mantener ventaja")
        elif league_stats.your_rank <= league_stats.total_players // 2:
            position_advice.append("Posición sólida - puedes tomar riesgos calculados")
            position_advice.append("Busca oportunidades de valor para escalar posiciones")
        else:
            position_advice.append("Necesitas tomar más riesgos para escalar")
            position_advice.append("Enfócate en diferenciales de alto potencial")
        
        return {
            "league_stats": league_stats.dict(),
            "trends_analysis": trends_analysis,
            "position_advice": position_advice,
            "performance_metrics": {
                "points_per_gameweek": round(league_stats.average_points, 1),
                "gap_to_leader": league_stats.points_behind_leader,
                "rank_percentile": round((1 - (league_stats.your_rank / league_stats.total_players)) * 100, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching league stats: {str(e)}")

def _get_sample_market_players() -> List[Player]:
    """Obtener jugadores del mercado (reutilizado)"""
    from api.routers.analysis import _get_sample_market_players
    return _get_sample_market_players()

def _calculate_differential_score(player: Player, prediction: PlayerPrediction) -> float:
    """
    Calcular puntuación diferencial basada en potencial vs propiedad
    """
    # Factores que contribuyen a la puntuación diferencial
    expected_points_factor = min(prediction.predicted_points / 10, 1.0)  # Normalizar a 0-1
    ownership_factor = max(0, (100 - player.ownership) / 100)  # Menor propiedad = mayor diferencial
    confidence_factor = prediction.confidence
    value_factor = min(prediction.predicted_points / max(player.price, 0.1) / 2, 1.0)  # Relación puntos/precio
    
    # Ponderación de factores
    differential_score = (
        expected_points_factor * 0.4 +
        ownership_factor * 0.3 +
        confidence_factor * 0.2 +
        value_factor * 0.1
    )
    
    return round(differential_score, 3)

def _get_differential_recommendation(player: Player, prediction: PlayerPrediction, score: float) -> str:
    """Generar recomendación textual para diferencial"""
    if score > 0.8 and player.ownership < 5:
        return "Diferencial premium - muy recomendado"
    elif score > 0.6 and player.ownership < 15:
        return "Excelente diferencial - considera fuertemente"
    elif score > 0.4 and player.ownership < 25:
        return "Buen diferencial - opción interesante"
    elif score > 0.3:
        return "Diferencial moderado - evaluar según contexto"
    else:
        return "Diferencial limitado - no prioritario"

def _calculate_potential_gain(player: Player, prediction: PlayerPrediction) -> str:
    """Calcular ganancia potencial del diferencial"""
    if prediction.predicted_points > 6 and player.ownership < 10:
        return "Alto potencial de ganancia"
    elif prediction.predicted_points > 4 and player.ownership < 20:
        return "Potencial moderado de ganancia"
    else:
        return "Potencial limitado de ganancia"

def _calculate_risk_reward_ratio(value_score: float, risk_score: float) -> str:
    """Calcular ratio riesgo-recompensa"""
    if value_score > 0.7 and risk_score < 0.3:
        return "Excelente ratio riesgo-recompensa"
    elif value_score > 0.5 and risk_score < 0.5:
        return "Buen ratio riesgo-recompensa"
    elif value_score > 0.3:
        return "Ratio moderado riesgo-recompensa"
    else:
        return "Ratio desfavorable riesgo-recompensa"

def _assess_league_impact(differential_score: float, ownership: float) -> str:
    """Evaluar impacto potencial en la liga"""
    if differential_score > 0.7 and ownership < 5:
        return "Impacto muy alto en liga"
    elif differential_score > 0.5 and ownership < 15:
        return "Impacto alto en liga"
    elif differential_score > 0.3 and ownership < 30:
        return "Impacto moderado en liga"
    else:
        return "Impacto limitado en liga"

def _get_sample_league_stats(league_id: str) -> LeagueStats:
    """Generar estadísticas de liga de ejemplo"""
    return LeagueStats(
        league_id=league_id,
        average_points=1842,
        top_score=2156,
        your_rank=45,
        total_players=250,
        points_behind_leader=314
    )

def _generate_differential_advice(differentials: List[Differential], league_stats: LeagueStats) -> List[str]:
    """Generar consejos estratégicos sobre diferenciales"""
    advice = []
    
    # Análisis basado en posición en liga
    rank_percentile = league_stats.your_rank / league_stats.total_players
    
    if rank_percentile < 0.1:  # Top 10%
        advice.append("En posición de liderazgo - enfócate en diferenciales de bajo riesgo")
        advice.append("Evita cambios drásticos que puedan afectar tu ventaja")
    elif rank_percentile < 0.5:  # Top 50%
        advice.append("Posición sólida - puedes considerar diferenciales moderados")
        advice.append("Busca oportunidades para distanciarte del pelotón")
    else:  # Bottom 50%
        advice.append("Necesitas tomar más riesgos - considera diferenciales de alto potencial")
        advice.append("Los diferenciales premium pueden ser clave para escalar")
    
    # Análisis de diferenciales disponibles
    high_score_diffs = [d for d in differentials if d.differential_score > 0.7]
    if len(high_score_diffs) >= 3:
        advice.append(f"Se detectaron {len(high_score_diffs)} diferenciales de alta calidad")
    
    low_ownership_diffs = [d for d in differentials if d.ownership_percentage < 5]
    if low_ownership_diffs:
        advice.append(f"{len(low_ownership_diffs)} jugadores con propiedad muy baja disponibles")
    
    return advice