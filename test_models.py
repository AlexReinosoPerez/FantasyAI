"""
Simplified models for testing without external dependencies
"""

from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class Position(str, Enum):
    """Posiciones de jugadores"""
    PORTERO = "POR"
    DEFENSA = "DEF" 
    CENTROCAMPISTA = "CEN"
    DELANTERO = "DEL"

class PlayerStatus(str, Enum):
    """Estado del jugador"""
    DISPONIBLE = "disponible"
    LESIONADO = "lesionado"
    SANCIONADO = "sancionado"
    DUDA = "duda"

class Player:
    """Modelo de jugador simplificado"""
    def __init__(self, id: int, name: str, team: str, position: Position,
                 price: float, points: int = 0, avg_points: float = 0.0,
                 form: List[int] = None, status: PlayerStatus = PlayerStatus.DISPONIBLE,
                 ownership: float = 0.0, fixture_difficulty: int = 3,
                 starter_probability: float = 0.8):
        self.id = id
        self.name = name
        self.team = team
        self.position = position
        self.price = price
        self.points = points
        self.avg_points = avg_points
        self.form = form or []
        self.status = status
        self.ownership = ownership
        self.fixture_difficulty = fixture_difficulty
        self.starter_probability = starter_probability

class PlayerPrediction:
    """Predicción para un jugador"""
    def __init__(self, player_id: int, predicted_points: float, confidence: float,
                 ema_points: float, fixture_adjusted_points: float):
        self.player_id = player_id
        self.predicted_points = predicted_points
        self.confidence = confidence
        self.ema_points = ema_points
        self.fixture_adjusted_points = fixture_adjusted_points