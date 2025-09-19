"""
Pydantic schemas for Fantasy LaLiga data structures.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Position(str, Enum):
    """Player positions"""
    PORTERO = "Portero"
    DEFENSA = "Defensa"
    CENTROCAMPISTA = "Centrocampista"
    DELANTERO = "Delantero"


class PlayerStatus(str, Enum):
    """Player availability status"""
    AVAILABLE = "available"
    INJURED = "injured"
    SUSPENDED = "suspended"
    DOUBTFUL = "doubtful"


class Player(BaseModel):
    """Player data model"""
    id: int
    name: str
    team: str
    position: Position
    price: float = Field(..., description="Current market price in millions")
    total_points: int = Field(default=0, description="Season total points")
    form: float = Field(default=0.0, description="Form score (EMA of recent performances)")
    availability: PlayerStatus = Field(default=PlayerStatus.AVAILABLE)
    minutes_played: int = Field(default=0, description="Total minutes played this season")
    games_played: int = Field(default=0, description="Games played this season")
    recent_points: List[int] = Field(default_factory=list, description="Points from last 5 games")
    price_history: List[float] = Field(default_factory=list, description="Historical prices")
    next_fixtures: List[str] = Field(default_factory=list, description="Next 3-5 fixture teams")
    
    class Config:
        use_enum_values = True


class TeamState(BaseModel):
    """User's current team state"""
    players: List[Player]
    bankroll: float = Field(..., description="Available money in millions")
    total_value: float = Field(..., description="Total team value in millions")
    weekly_budget: float = Field(default=0.0, description="Weekly transfer budget")
    transfers_made: int = Field(default=0, description="Transfers made this week")
    
    
class Market(BaseModel):
    """Market state with available players"""
    available_players: List[Player]
    trending_up: List[int] = Field(default_factory=list, description="Player IDs trending up in price")
    trending_down: List[int] = Field(default_factory=list, description="Player IDs trending down in price")
    most_transferred_in: List[int] = Field(default_factory=list, description="Most transferred in player IDs")
    most_transferred_out: List[int] = Field(default_factory=list, description="Most transferred out player IDs")


class RivalTeam(BaseModel):
    """Rival team composition"""
    team_id: str
    manager_name: str
    players: List[int] = Field(..., description="Player IDs in rival team")
    total_points: int = Field(default=0)
    team_value: float = Field(default=0.0)


class LeagueState(BaseModel):
    """Complete league state including rivals"""
    rivals: List[RivalTeam]
    league_average_points: float = Field(default=0.0)
    
    
class PlayerAnalysis(BaseModel):
    """Analysis results for a single player"""
    player_id: int
    expected_points_next_3: float = Field(..., description="Expected points next 3 gameweeks")
    form_score: float = Field(..., description="Current form (0-10)")
    fixture_difficulty: float = Field(..., description="Fixture difficulty (1-5)")
    availability_score: float = Field(..., description="Availability probability (0-1)")
    risk_score: float = Field(..., description="Risk assessment (0-1)")
    fair_value: float = Field(..., description="Calculated fair price")
    value_ratio: float = Field(..., description="Expected points per million spent")
    

class TeamAnalysis(BaseModel):
    """Analysis of user's team"""
    players_to_sell: List[PlayerAnalysis]
    players_to_keep: List[PlayerAnalysis]
    weak_positions: List[Position]
    team_balance_score: float = Field(..., description="Team balance assessment (0-1)")


class MarketAnalysis(BaseModel):
    """Market analysis results"""
    best_buys: List[PlayerAnalysis]
    overpriced: List[PlayerAnalysis]
    bargains: List[PlayerAnalysis]
    market_trends: Dict[str, Any]


class SwapRecommendation(BaseModel):
    """Player swap recommendation"""
    sell_player_id: int
    buy_player_id: int
    expected_points_gain: float
    cost_difference: float
    risk_assessment: str
    confidence: float = Field(..., description="Confidence in recommendation (0-1)")


class BidRecommendation(BaseModel):
    """Bidding recommendation for a player"""
    player_id: int
    min_bid: float = Field(..., description="Minimum sensible bid")
    max_bid: float = Field(..., description="Maximum recommended bid")
    fair_value: float = Field(..., description="Calculated fair value")
    risk_level: str = Field(..., description="Low/Medium/High risk assessment")
    market_pressure: float = Field(..., description="Market demand pressure (0-1)")


class DifferentialAnalysis(BaseModel):
    """Differential player analysis vs rivals"""
    player_id: int
    ownership_percentage: float = Field(..., description="% of rivals who own this player")
    differential_value: float = Field(..., description="Potential differential value")
    risk_reward_ratio: float
    

class RecommendationResponse(BaseModel):
    """Complete recommendation response"""
    team_analysis: TeamAnalysis
    market_analysis: MarketAnalysis
    swap_recommendations: List[SwapRecommendation]
    bid_recommendations: List[BidRecommendation]
    differentials: List[DifferentialAnalysis]
    summary: str = Field(..., description="Text summary of key recommendations")