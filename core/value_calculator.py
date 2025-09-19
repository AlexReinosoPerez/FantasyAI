"""
Value and Risk Calculator for Fantasy LaLiga Assistant
Calculadora de valor, riesgo y pujas máximas
"""

import numpy as np
from typing import Dict, List, Tuple
from core.models import Player, PlayerPrediction, MarketData

class ValueRiskCalculator:
    """Calculadora de valor, riesgo y recomendaciones de puja"""
    
    def __init__(self):
        """Inicializar calculadora con parámetros de riesgo"""
        self.risk_weights = {
            'price_volatility': 0.3,
            'form_consistency': 0.25,
            'injury_risk': 0.2,
            'rotation_risk': 0.15,
            'fixture_difficulty': 0.1
        }
        
    def calculate_player_value(self, player: Player, prediction: PlayerPrediction) -> float:
        """
        Calcular el valor intrínseco de un jugador
        
        Args:
            player: Datos del jugador
            prediction: Predicción de puntos
            
        Returns:
            Valor calculado en millones
        """
        # Valor base = puntos esperados / precio (eficiencia)
        if player.price <= 0:
            return 0.0
            
        base_efficiency = prediction.predicted_points / player.price
        
        # Ajustes por factores adicionales
        ownership_factor = max(0.5, 1 - (player.ownership / 100))  # Menor propiedad = más valor potencial
        form_factor = self._calculate_form_factor(player)
        consistency_factor = self._calculate_consistency_factor(player)
        
        # Valor final ajustado
        adjusted_value = base_efficiency * ownership_factor * form_factor * consistency_factor
        
        return round(adjusted_value, 3)
    
    def calculate_risk_score(self, player: Player, market_data: MarketData = None) -> Dict[str, float]:
        """
        Calcular puntuación de riesgo detallada
        
        Args:
            player: Datos del jugador
            market_data: Datos de mercado (opcional)
            
        Returns:
            Diccionario con puntuaciones de riesgo por categoría
        """
        risks = {}
        
        # Riesgo por volatilidad de precio
        risks['price_volatility'] = self._calculate_price_volatility_risk(market_data) if market_data else 0.3
        
        # Riesgo por inconsistencia de forma
        risks['form_consistency'] = self._calculate_form_consistency_risk(player)
        
        # Riesgo de lesión
        risks['injury_risk'] = self._calculate_injury_risk(player)
        
        # Riesgo de rotación
        risks['rotation_risk'] = self._calculate_rotation_risk(player)
        
        # Riesgo por dificultad de fixtures
        risks['fixture_difficulty'] = self._calculate_fixture_risk(player)
        
        # Riesgo total ponderado
        total_risk = sum(risks[key] * self.risk_weights[key] for key in risks)
        risks['total'] = round(total_risk, 3)
        
        return risks
    
    def calculate_max_bid(self, player: Player, prediction: PlayerPrediction, 
                         budget: float, risk_tolerance: str = "medium") -> Dict[str, float]:
        """
        Calcular puja máxima recomendada
        
        Args:
            player: Datos del jugador
            prediction: Predicción de puntos
            budget: Presupuesto disponible
            risk_tolerance: Tolerancia al riesgo ("low", "medium", "high")
            
        Returns:
            Diccionario con recomendaciones de puja
        """
        # Calcular valor intrínseco
        intrinsic_value = self.calculate_player_value(player, prediction)
        
        # Calcular riesgo
        risk_scores = self.calculate_risk_score(player)
        total_risk = risk_scores['total']
        
        # Factores de tolerancia al riesgo
        risk_multipliers = {
            "low": 0.7,    # Conservador
            "medium": 0.85, # Moderado
            "high": 1.0     # Agresivo
        }
        
        risk_multiplier = risk_multipliers.get(risk_tolerance, 0.85)
        
        # Puja base ajustada por riesgo
        base_bid = player.price * intrinsic_value * risk_multiplier
        
        # Ajustar por confianza en la predicción
        confidence_factor = prediction.confidence
        confidence_adjusted_bid = base_bid * confidence_factor
        
        # Limitar por presupuesto disponible
        max_affordable = min(confidence_adjusted_bid, budget * 0.3)  # Máximo 30% del presupuesto
        
        # Puja mínima (precio actual + margen)
        min_bid = player.price * 1.05  # 5% sobre precio actual
        
        return {
            "max_recommended": round(max_affordable, 2),
            "conservative": round(min_bid, 2),
            "aggressive": round(confidence_adjusted_bid, 2),
            "value_score": round(intrinsic_value, 3),
            "risk_score": total_risk,
            "confidence": prediction.confidence
        }
    
    def compare_players(self, players: List[Player], predictions: List[PlayerPrediction]) -> List[Dict]:
        """
        Comparar múltiples jugadores por valor y riesgo
        
        Args:
            players: Lista de jugadores
            predictions: Lista de predicciones correspondientes
            
        Returns:
            Lista ordenada por mejor valor/riesgo
        """
        comparisons = []
        
        for player, prediction in zip(players, predictions):
            value = self.calculate_player_value(player, prediction)
            risks = self.calculate_risk_score(player)
            
            # Puntuación compuesta (valor ajustado por riesgo)
            composite_score = value * (1 - risks['total'])
            
            comparisons.append({
                "player_id": player.id,
                "name": player.name,
                "position": player.position.value,
                "price": player.price,
                "predicted_points": prediction.predicted_points,
                "value_score": value,
                "risk_score": risks['total'],
                "composite_score": round(composite_score, 3),
                "recommendation": self._get_recommendation(composite_score, risks['total'])
            })
        
        # Ordenar por puntuación compuesta (descendente)
        return sorted(comparisons, key=lambda x: x['composite_score'], reverse=True)
    
    def _calculate_form_factor(self, player: Player) -> float:
        """Calcular factor de forma reciente"""
        if not player.form or len(player.form) < 2:
            return 1.0
            
        recent_avg = np.mean(player.form[-3:]) if len(player.form) >= 3 else np.mean(player.form)
        season_avg = player.avg_points if player.avg_points > 0 else np.mean(player.form)
        
        if season_avg <= 0:
            return 1.0
            
        form_ratio = recent_avg / season_avg
        return min(1.5, max(0.5, form_ratio))  # Limitar entre 0.5 y 1.5
    
    def _calculate_consistency_factor(self, player: Player) -> float:
        """Calcular factor de consistencia"""
        if not player.form or len(player.form) < 3:
            return 1.0
            
        variance = np.var(player.form)
        
        # Menor varianza = mayor consistencia = mayor factor
        if variance <= 1:
            return 1.2
        elif variance <= 3:
            return 1.1
        elif variance <= 6:
            return 1.0
        else:
            return 0.9
    
    def _calculate_price_volatility_risk(self, market_data: MarketData) -> float:
        """Calcular riesgo por volatilidad de precio"""
        if not market_data:
            return 0.3
            
        price_change_magnitude = abs(market_data.price_change)
        
        if price_change_magnitude > 0.5:
            return 0.8  # Alto riesgo
        elif price_change_magnitude > 0.2:
            return 0.5  # Riesgo medio
        else:
            return 0.2  # Bajo riesgo
    
    def _calculate_form_consistency_risk(self, player: Player) -> float:
        """Calcular riesgo por inconsistencia de forma"""
        if not player.form or len(player.form) < 3:
            return 0.5
            
        variance = np.var(player.form)
        
        if variance <= 2:
            return 0.1  # Muy consistente
        elif variance <= 5:
            return 0.3  # Moderadamente consistente
        elif variance <= 10:
            return 0.6  # Inconsistente
        else:
            return 0.9  # Muy inconsistente
    
    def _calculate_injury_risk(self, player: Player) -> float:
        """Calcular riesgo de lesión"""
        status_risks = {
            "disponible": 0.1,
            "duda": 0.6,
            "lesionado": 0.9,
            "sancionado": 0.3
        }
        return status_risks.get(player.status.value, 0.1)
    
    def _calculate_rotation_risk(self, player: Player) -> float:
        """Calcular riesgo de rotación"""
        # Basado en probabilidad de ser titular
        if hasattr(player, 'starter_probability'):
            return 1 - player.starter_probability
        
        # Estimación basada en precio y posición
        if player.price > 8.0:
            return 0.1  # Jugadores caros raramente rotan
        elif player.price > 5.0:
            return 0.3  # Jugadores medios rotación moderada
        else:
            return 0.6  # Jugadores baratos alta rotación
    
    def _calculate_fixture_risk(self, player: Player) -> float:
        """Calcular riesgo por dificultad de fixtures"""
        difficulty = getattr(player, 'fixture_difficulty', 3)
        
        # Convertir dificultad (1-5) a riesgo (0-1)
        return (difficulty - 1) / 4
    
    def _get_recommendation(self, composite_score: float, risk_score: float) -> str:
        """Generar recomendación textual"""
        if composite_score > 0.8 and risk_score < 0.3:
            return "Compra fuerte"
        elif composite_score > 0.6 and risk_score < 0.5:
            return "Compra"
        elif composite_score > 0.4:
            return "Considerar"
        elif risk_score > 0.7:
            return "Evitar - Alto riesgo"
        else:
            return "No recomendado"