"""
Recommendations API Router
Endpoints para recomendaciones de intercambios y pujas
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel

from core.models import Team, Player, SwapRecommendation, BidRecommendation
from core.prediction_engine import PredictionEngine
from core.value_calculator import ValueRiskCalculator

router = APIRouter()
prediction_engine = PredictionEngine()
value_calculator = ValueRiskCalculator()

class SwapRequest(BaseModel):
    """Request para recomendaciones de intercambio"""
    current_team: Team
    budget_constraint: float = 0.0  # Presupuesto adicional disponible
    risk_tolerance: str = "medium"  # low, medium, high
    target_positions: Optional[List[str]] = None  # Posiciones específicas a mejorar

class BidRequest(BaseModel):
    """Request para recomendaciones de puja"""
    current_team: Team
    target_players: Optional[List[int]] = None  # IDs de jugadores específicos
    budget: float
    risk_tolerance: str = "medium"

@router.post("/swaps")
async def recommend_swaps(request: SwapRequest):
    """
    Recomendar intercambios de jugadores
    
    Analiza el equipo actual y sugiere intercambios para mejorar rendimiento,
    considerando presupuesto, riesgo y objetivos específicos.
    """
    try:
        current_team = request.current_team
        
        # Obtener jugadores disponibles en el mercado
        market_players = _get_sample_market_players()
        
        # Generar predicciones para equipo actual
        current_predictions = prediction_engine.predict_multiple_players(current_team.players)
        
        # Generar predicciones para mercado
        market_predictions = prediction_engine.predict_multiple_players(market_players)
        
        # Identificar jugadores del equipo con bajo rendimiento
        weak_players = []
        for player, prediction in zip(current_team.players, current_predictions):
            value = value_calculator.calculate_player_value(player, prediction)
            risks = value_calculator.calculate_risk_score(player)
            
            # Criterios para considerar intercambio
            if (prediction.predicted_points < 3.0 or 
                prediction.confidence < 0.5 or 
                value < 0.3 or 
                risks['total'] > 0.7):
                weak_players.append((player, prediction, value, risks['total']))
        
        # Generar recomendaciones de intercambio
        swap_recommendations = []
        
        for weak_player, weak_prediction, weak_value, weak_risk in weak_players:
            # Buscar mejores alternativas en la misma posición
            position_alternatives = [
                (p, pred) for p, pred in zip(market_players, market_predictions)
                if (p.position == weak_player.position and 
                    p.price <= weak_player.price + request.budget_constraint and
                    pred.predicted_points > weak_prediction.predicted_points)
            ]
            
            # Ordenar por potencial de mejora
            position_alternatives.sort(
                key=lambda x: x[1].predicted_points - weak_prediction.predicted_points,
                reverse=True
            )
            
            # Crear recomendaciones para las mejores opciones
            for alt_player, alt_prediction in position_alternatives[:3]:  # Top 3 alternativas
                points_gain = alt_prediction.predicted_points - weak_prediction.predicted_points
                alt_value = value_calculator.calculate_player_value(alt_player, alt_prediction)
                alt_risks = value_calculator.calculate_risk_score(alt_player)
                
                # Determinar nivel de riesgo del intercambio
                risk_level = _determine_swap_risk(weak_risk, alt_risks['total'], request.risk_tolerance)
                
                # Calcular confianza en la recomendación
                confidence = min(alt_prediction.confidence, 
                               (alt_value / max(weak_value, 0.1)) * 0.5)
                
                reason = f"Mejora esperada: +{points_gain:.1f} puntos. "
                if alt_value > weak_value * 1.2:
                    reason += "Excelente valor. "
                if alt_risks['total'] < weak_risk:
                    reason += "Menor riesgo. "
                if alt_player.ownership < weak_player.ownership:
                    reason += "Menor propiedad (diferencial)."
                
                swap_recommendations.append(SwapRecommendation(
                    player_out_id=weak_player.id,
                    player_in_id=alt_player.id,
                    reason=reason,
                    expected_points_gain=round(points_gain, 2),
                    risk_level=risk_level,
                    confidence=round(confidence, 2)
                ))
        
        # Ordenar por ganancia esperada y confianza
        swap_recommendations.sort(
            key=lambda x: (x.expected_points_gain * x.confidence),
            reverse=True
        )
        
        # Preparar respuesta detallada
        detailed_swaps = []
        for swap in swap_recommendations[:10]:  # Top 10 recomendaciones
            player_out = next(p for p in current_team.players if p.id == swap.player_out_id)
            player_in = next(p for p in market_players if p.id == swap.player_in_id)
            
            detailed_swaps.append({
                "swap_details": swap.dict(),
                "player_out": {
                    "id": player_out.id,
                    "name": player_out.name,
                    "price": player_out.price,
                    "predicted_points": next(p.predicted_points for p in current_predictions if p.player_id == player_out.id)
                },
                "player_in": {
                    "id": player_in.id,
                    "name": player_in.name,
                    "price": player_in.price,
                    "predicted_points": next(p.predicted_points for p in market_predictions if p.player_id == player_in.id)
                },
                "cost_difference": round(player_in.price - player_out.price, 2)
            })
        
        return {
            "swap_recommendations": detailed_swaps,
            "summary": {
                "total_recommendations": len(swap_recommendations),
                "weak_players_identified": len(weak_players),
                "budget_constraint": request.budget_constraint,
                "risk_tolerance": request.risk_tolerance
            },
            "general_advice": _generate_swap_advice(swap_recommendations, request.budget_constraint)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating swap recommendations: {str(e)}")

@router.post("/bids")
async def recommend_bids(request: BidRequest):
    """
    Recomendar pujas para jugadores
    
    Analiza jugadores objetivo y calcula pujas máximas recomendadas
    basadas en valor esperado, riesgo y presupuesto disponible.
    """
    try:
        # Obtener jugadores objetivo
        if request.target_players:
            market_players = [p for p in _get_sample_market_players() if p.id in request.target_players]
        else:
            market_players = _get_sample_market_players()
        
        if not market_players:
            return {"message": "No se encontraron jugadores objetivo"}
        
        # Generar predicciones
        predictions = prediction_engine.predict_multiple_players(market_players)
        
        # Generar recomendaciones de puja
        bid_recommendations = []
        
        for player, prediction in zip(market_players, predictions):
            # Calcular puja máxima
            bid_analysis = value_calculator.calculate_max_bid(
                player, prediction, request.budget, request.risk_tolerance
            )
            
            # Determinar si vale la pena pujar
            if bid_analysis["max_recommended"] > player.price:
                # Generar explicación detallada
                reasoning = _generate_bid_reasoning(player, prediction, bid_analysis)
                
                # Determinar evaluación de riesgo
                risk_assessment = _assess_bid_risk(bid_analysis["risk_score"], request.risk_tolerance)
                
                bid_recommendations.append(BidRecommendation(
                    player_id=player.id,
                    max_bid=bid_analysis["max_recommended"],
                    expected_return=prediction.predicted_points,
                    risk_assessment=risk_assessment,
                    reasoning=reasoning
                ))
        
        # Ordenar por valor esperado ajustado por riesgo
        bid_recommendations.sort(
            key=lambda x: x.expected_return / max(x.max_bid, 0.1),
            reverse=True
        )
        
        # Preparar respuesta detallada
        detailed_bids = []
        total_cost = 0
        
        for bid in bid_recommendations:
            player = next(p for p in market_players if p.id == bid.player_id)
            
            # Verificar si aún hay presupuesto
            if total_cost + bid.max_bid <= request.budget:
                affordable = True
                total_cost += bid.max_bid
            else:
                affordable = False
            
            detailed_bids.append({
                "bid_details": bid.dict(),
                "player_info": {
                    "id": player.id,
                    "name": player.name,
                    "position": player.position.value,
                    "current_price": player.price,
                    "ownership": player.ownership
                },
                "value_analysis": value_calculator.calculate_max_bid(
                    player, 
                    next(p for p in predictions if p.player_id == player.id),
                    request.budget,
                    request.risk_tolerance
                ),
                "affordable": affordable
            })
        
        return {
            "bid_recommendations": detailed_bids,
            "budget_summary": {
                "total_budget": request.budget,
                "recommended_spend": round(total_cost, 2),
                "remaining_budget": round(request.budget - total_cost, 2),
                "budget_utilization": round((total_cost / request.budget) * 100, 1) if request.budget > 0 else 0
            },
            "risk_profile": request.risk_tolerance,
            "general_advice": _generate_bid_advice(bid_recommendations, request.budget)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating bid recommendations: {str(e)}")

def _get_sample_market_players() -> List[Player]:
    """Obtener datos de ejemplo del mercado (reutilizado de analysis.py)"""
    from api.routers.analysis import _get_sample_market_players
    return _get_sample_market_players()

def _determine_swap_risk(current_risk: float, new_risk: float, tolerance: str) -> str:
    """Determinar nivel de riesgo del intercambio"""
    risk_increase = new_risk - current_risk
    
    if risk_increase <= -0.2:
        return "bajo"
    elif risk_increase <= 0.1:
        return "medio"
    else:
        return "alto"

def _generate_swap_advice(swaps: List[SwapRecommendation], budget: float) -> List[str]:
    """Generar consejos generales sobre intercambios"""
    advice = []
    
    if not swaps:
        advice.append("Tu equipo parece sólido, no se identificaron intercambios urgentes")
    elif len(swaps) > 5:
        advice.append("Se identificaron múltiples oportunidades de mejora - prioriza por ganancia esperada")
    
    high_confidence_swaps = [s for s in swaps if s.confidence > 0.7]
    if high_confidence_swaps:
        advice.append(f"{len(high_confidence_swaps)} intercambios tienen alta confianza")
    
    if budget > 3.0:
        advice.append("Con tu presupuesto puedes considerar mejoras premium")
    elif budget < 1.0:
        advice.append("Presupuesto limitado - enfócate en intercambios laterales")
    
    return advice

def _generate_bid_reasoning(player: Player, prediction: PlayerPrediction, analysis: Dict) -> str:
    """Generar explicación para recomendación de puja"""
    reasons = []
    
    if analysis["value_score"] > 0.8:
        reasons.append("Excelente relación valor/precio")
    
    if prediction.confidence > 0.8:
        reasons.append("Alta confianza en predicción")
    
    if player.ownership < 15:
        reasons.append("Baja propiedad - potencial diferencial")
    
    if prediction.predicted_points > 5:
        reasons.append("Alto potencial de puntos")
    
    if analysis["risk_score"] < 0.3:
        reasons.append("Riesgo bajo")
    
    return ". ".join(reasons) if reasons else "Oportunidad interesante basada en análisis general"

def _assess_bid_risk(risk_score: float, tolerance: str) -> str:
    """Evaluar riesgo de la puja"""
    if risk_score < 0.3:
        return "Riesgo bajo - inversión segura"
    elif risk_score < 0.5:
        return "Riesgo moderado - analizar cuidadosamente"
    elif risk_score < 0.7:
        return "Riesgo elevado - solo para perfiles agresivos"
    else:
        return "Riesgo muy alto - no recomendado"

def _generate_bid_advice(bids: List[BidRecommendation], budget: float) -> List[str]:
    """Generar consejos generales sobre pujas"""
    advice = []
    
    if not bids:
        advice.append("No se encontraron oportunidades de puja atractivas en este momento")
    
    low_risk_bids = [b for b in bids if "bajo" in b.risk_assessment.lower()]
    if low_risk_bids:
        advice.append(f"{len(low_risk_bids)} pujas de bajo riesgo disponibles")
    
    total_recommended = sum(b.max_bid for b in bids)
    if total_recommended > budget * 1.5:
        advice.append("Muchas oportunidades detectadas - prioriza por mayor retorno esperado")
    
    return advice