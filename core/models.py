"""
Core data models for Fantasy LaLiga Assistant
Modelos de datos principales para el asistente de Fantasy LaLiga
"""

from pydantic import BaseModel, Field
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

class Player(BaseModel):
    """Modelo de jugador"""
    id: int
    name: str
    team: str
    position: Position
    price: float = Field(..., description="Precio actual en millones")
    points: int = Field(default=0, description="Puntos totales en la temporada")
    avg_points: float = Field(default=0.0, description="Media de puntos por jornada")
    form: List[int] = Field(default_factory=list, description="Puntos últimas 5 jornadas")
    status: PlayerStatus = Field(default=PlayerStatus.DISPONIBLE)
    ownership: float = Field(default=0.0, description="Porcentaje de propiedad")
    fixture_difficulty: int = Field(default=3, description="Dificultad próximo partido (1-5)")
    starter_probability: float = Field(default=0.8, description="Probabilidad de ser titular")
    
class Team(BaseModel):
    """Modelo de equipo del usuario"""
    user_id: str
    players: List[Player]
    formation: str = Field(default="4-4-2", description="Formación táctica")
    budget: float = Field(default=0.0, description="Presupuesto disponible en millones")
    total_value: float = Field(default=0.0, description="Valor total del equipo")
    
class MarketData(BaseModel):
    """Datos del mercado de fichajes"""
    player_id: int
    current_price: float
    price_change: float = Field(description="Cambio de precio desde última jornada")
    predicted_price: float = Field(description="Precio predicho próxima jornada")
    demand: float = Field(description="Nivel de demanda (0-1)")
    supply: float = Field(description="Nivel de oferta (0-1)")

class Fixture(BaseModel):
    """Partido/enfrentamiento"""
    team_home: str
    team_away: str
    gameweek: int
    difficulty_home: int = Field(description="Dificultad para equipo local (1-5)")
    difficulty_away: int = Field(description="Dificultad para equipo visitante (1-5)")

class PlayerPrediction(BaseModel):
    """Predicción para un jugador"""
    player_id: int
    predicted_points: float
    confidence: float = Field(description="Confianza en la predicción (0-1)")
    ema_points: float = Field(description="Media móvil exponencial de puntos")
    fixture_adjusted_points: float = Field(description="Puntos ajustados por dificultad")
    
class SwapRecommendation(BaseModel):
    """Recomendación de intercambio"""
    player_out_id: int
    player_in_id: int
    reason: str
    expected_points_gain: float
    risk_level: str = Field(description="Nivel de riesgo: bajo, medio, alto")
    confidence: float

class BidRecommendation(BaseModel):
    """Recomendación de puja"""
    player_id: int
    max_bid: float = Field(description="Puja máxima recomendada")
    expected_return: float = Field(description="Retorno esperado de puntos")
    risk_assessment: str
    reasoning: str

class LeagueStats(BaseModel):
    """Estadísticas de liga"""
    league_id: str
    average_points: float
    top_score: int
    your_rank: int
    total_players: int
    points_behind_leader: int

class Differential(BaseModel):
    """Jugador diferencial"""
    player_id: int
    ownership_percentage: float
    expected_points: float
    differential_score: float = Field(description="Puntuación diferencial calculada")
    recommendation: str = Field(description="Recomendación: comprar, vender, mantener")