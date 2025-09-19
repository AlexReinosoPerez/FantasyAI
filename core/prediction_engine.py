"""
Prediction Engine for Fantasy LaLiga Assistant
Motor de predicciones con EMA, análisis de fixtures y probabilidad de titularidad
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from core.models import Player, Fixture, PlayerPrediction

class PredictionEngine:
    """Motor de predicciones para jugadores de Fantasy LaLiga"""
    
    def __init__(self, alpha: float = 0.3):
        """
        Inicializar motor de predicciones
        
        Args:
            alpha: Factor de suavizado para EMA (0-1). Valores más altos dan más peso a datos recientes
        """
        self.alpha = alpha
        self.fixture_multipliers = {
            1: 1.3,   # Muy fácil
            2: 1.15,  # Fácil  
            3: 1.0,   # Neutral
            4: 0.85,  # Difícil
            5: 0.7    # Muy difícil
        }
        
    def calculate_ema_points(self, recent_points: List[int], current_avg: float) -> float:
        """
        Calcular la media móvil exponencial de puntos
        
        Args:
            recent_points: Lista de puntos de las últimas jornadas
            current_avg: Media actual de puntos por jornada
            
        Returns:
            EMA calculada
        """
        if not recent_points:
            return current_avg
            
        ema = current_avg
        for points in recent_points:
            ema = self.alpha * points + (1 - self.alpha) * ema
            
        return round(ema, 2)
    
    def adjust_for_fixture_difficulty(self, base_points: float, difficulty: int) -> float:
        """
        Ajustar puntos predichos según dificultad del partido
        
        Args:
            base_points: Puntos base predichos
            difficulty: Dificultad del partido (1-5)
            
        Returns:
            Puntos ajustados por dificultad
        """
        multiplier = self.fixture_multipliers.get(difficulty, 1.0)
        return round(base_points * multiplier, 2)
    
    def calculate_starter_probability(self, player: Player, team_form: List[int] = None) -> float:
        """
        Calcular probabilidad de que el jugador sea titular
        
        Args:
            player: Jugador a analizar
            team_form: Forma reciente del equipo (opcional)
            
        Returns:
            Probabilidad de ser titular (0-1)
        """
        base_prob = 0.8  # Probabilidad base
        
        # Ajustar por forma reciente del jugador
        if player.form:
            recent_avg = np.mean(player.form[-3:]) if len(player.form) >= 3 else np.mean(player.form)
            if recent_avg > player.avg_points:
                base_prob += 0.1
            elif recent_avg < player.avg_points * 0.5:
                base_prob -= 0.2
                
        # Ajustar por estado del jugador
        status_adjustments = {
            "disponible": 0.0,
            "duda": -0.3,
            "lesionado": -0.8,
            "sancionado": -1.0
        }
        base_prob += status_adjustments.get(player.status.value, 0.0)
        
        # Ajustar por precio/calidad
        if player.price > 8.0:  # Jugadores caros suelen ser más titulares
            base_prob += 0.1
        elif player.price < 4.0:  # Jugadores baratos menos probable que sean titulares
            base_prob -= 0.1
            
        return max(0.0, min(1.0, round(base_prob, 2)))
    
    def predict_player_points(self, player: Player, fixture: Fixture = None) -> PlayerPrediction:
        """
        Generar predicción completa para un jugador
        
        Args:
            player: Jugador a analizar
            fixture: Próximo partido (opcional)
            
        Returns:
            Predicción completa del jugador
        """
        # Calcular EMA
        ema_points = self.calculate_ema_points(player.form, player.avg_points)
        
        # Determinar dificultad del fixture
        difficulty = 3  # Neutral por defecto
        if fixture:
            # Determinar si juega en casa o fuera basándose en el equipo del jugador
            difficulty = fixture.difficulty_home if player.team == fixture.team_home else fixture.difficulty_away
        elif hasattr(player, 'fixture_difficulty'):
            difficulty = player.fixture_difficulty
            
        # Ajustar por dificultad del partido
        fixture_adjusted = self.adjust_for_fixture_difficulty(ema_points, difficulty)
        
        # Calcular probabilidad de ser titular
        starter_prob = self.calculate_starter_probability(player)
        
        # Predicción final ajustada por probabilidad de jugar
        predicted_points = fixture_adjusted * starter_prob
        
        # Calcular confianza en la predicción
        confidence = self._calculate_confidence(player, len(player.form))
        
        return PlayerPrediction(
            player_id=player.id,
            predicted_points=round(predicted_points, 2),
            confidence=confidence,
            ema_points=ema_points,
            fixture_adjusted_points=fixture_adjusted
        )
    
    def _calculate_confidence(self, player: Player, data_points: int) -> float:
        """
        Calcular nivel de confianza en la predicción
        
        Args:
            player: Jugador analizado
            data_points: Número de puntos de datos disponibles
            
        Returns:
            Nivel de confianza (0-1)
        """
        base_confidence = 0.5
        
        # Más datos = más confianza
        if data_points >= 5:
            base_confidence += 0.3
        elif data_points >= 3:
            base_confidence += 0.2
        elif data_points >= 1:
            base_confidence += 0.1
            
        # Jugadores con forma consistente = más confianza
        if player.form and len(player.form) >= 3:
            variance = np.var(player.form)
            if variance <= 2:  # Forma muy consistente
                base_confidence += 0.2
            elif variance <= 5:  # Forma moderadamente consistente
                base_confidence += 0.1
                
        # Estado del jugador afecta confianza
        if player.status.value in ["lesionado", "duda"]:
            base_confidence -= 0.2
            
        return max(0.1, min(1.0, round(base_confidence, 2)))
    
    def predict_multiple_players(self, players: List[Player], fixtures: List[Fixture] = None) -> List[PlayerPrediction]:
        """
        Generar predicciones para múltiples jugadores
        
        Args:
            players: Lista de jugadores
            fixtures: Lista de próximos partidos (opcional)
            
        Returns:
            Lista de predicciones
        """
        predictions = []
        fixture_dict = {}
        
        # Crear diccionario de fixtures por equipo para acceso rápido
        if fixtures:
            for fixture in fixtures:
                fixture_dict[fixture.team_home] = fixture
                fixture_dict[fixture.team_away] = fixture
        
        for player in players:
            fixture = fixture_dict.get(player.team)
            prediction = self.predict_player_points(player, fixture)
            predictions.append(prediction)
            
        return predictions