"""
Feature engineering functions for player analysis.
Calculates form, fixture difficulty, availability, and risk metrics.
"""

import numpy as np
from typing import List, Dict, Tuple
from .schemas import Player, PlayerStatus, Position


# Fixture Difficulty Rating (FDR) table for LaLiga teams
# Scale: 1 (easiest) to 5 (hardest)
FDR_TABLE = {
    "Real Madrid": 5,
    "Barcelona": 5,
    "Atletico Madrid": 4,
    "Athletic Bilbao": 4,
    "Real Sociedad": 4,
    "Real Betis": 3,
    "Villarreal": 3,
    "Valencia": 3,
    "Sevilla": 3,
    "Celta Vigo": 3,
    "Osasuna": 3,
    "Rayo Vallecano": 3,
    "Las Palmas": 2,
    "Getafe": 2,
    "Girona": 2,
    "Mallorca": 2,
    "Leganes": 2,
    "Valladolid": 2,
    "Espanyol": 2,
    "Alaves": 2
}


def calculate_form_score(recent_points: List[int], alpha: float = 0.3) -> float:
    """
    Calculate Exponential Moving Average (EMA) form score from recent performances.
    
    Args:
        recent_points: List of points from recent games (most recent first)
        alpha: EMA smoothing factor (0.1-0.5, higher = more weight on recent games)
    
    Returns:
        Form score (0-10 scale)
    """
    if not recent_points:
        return 0.0
    
    if len(recent_points) == 1:
        return min(recent_points[0], 10.0)
    
    # Calculate EMA with most recent points weighted more heavily
    ema = recent_points[0]
    for points in recent_points[1:]:
        ema = alpha * points + (1 - alpha) * ema
    
    # Scale to 0-10 (assuming max realistic points per game is 15)
    return min(ema * (10.0 / 15.0), 10.0)


def calculate_fixture_difficulty(next_fixtures: List[str], fdr_table: Dict[str, int] = None) -> float:
    """
    Calculate average fixture difficulty for next fixtures.
    
    Args:
        next_fixtures: List of team names for upcoming fixtures
        fdr_table: Fixture difficulty ratings (defaults to FDR_TABLE)
    
    Returns:
        Average fixture difficulty (1-5 scale)
    """
    if not next_fixtures:
        return 3.0  # Default neutral difficulty
    
    if fdr_table is None:
        fdr_table = FDR_TABLE
    
    difficulties = []
    for team in next_fixtures:
        difficulty = fdr_table.get(team, 3)  # Default to 3 if team not found
        difficulties.append(difficulty)
    
    return sum(difficulties) / len(difficulties)


def calculate_availability_score(player: Player) -> float:
    """
    Calculate availability probability based on status and playing time.
    
    Args:
        player: Player object with status and playing time data
    
    Returns:
        Availability score (0-1, where 1 = fully available)
    """
    base_score = 1.0
    
    # Status penalties
    status_penalties = {
        PlayerStatus.INJURED: 0.0,
        PlayerStatus.SUSPENDED: 0.0,
        PlayerStatus.DOUBTFUL: 0.3,
        PlayerStatus.AVAILABLE: 1.0
    }
    
    status_score = status_penalties.get(player.availability, 1.0)
    
    # Playing time factor (if player hasn't played much, lower availability)
    if player.games_played > 0:
        minutes_per_game = player.minutes_played / player.games_played
        playing_time_score = min(minutes_per_game / 90.0, 1.0)  # Normalize to 90 min games
    else:
        playing_time_score = 0.5  # Unknown, assume moderate availability
    
    # Combine factors
    availability = status_score * (0.7 + 0.3 * playing_time_score)
    
    return max(0.0, min(1.0, availability))


def calculate_price_volatility(price_history: List[float]) -> float:
    """
    Calculate price volatility based on historical price movements.
    
    Args:
        price_history: List of historical prices (most recent first)
    
    Returns:
        Volatility score (0-1, where higher = more volatile)
    """
    if len(price_history) < 2:
        return 0.0
    
    # Calculate percentage changes
    changes = []
    for i in range(len(price_history) - 1):
        if price_history[i + 1] > 0:  # Avoid division by zero
            change = abs(price_history[i] - price_history[i + 1]) / price_history[i + 1]
            changes.append(change)
    
    if not changes:
        return 0.0
    
    # Return standard deviation of changes, capped at 1.0
    volatility = np.std(changes)
    return min(volatility * 10, 1.0)  # Scale up and cap


def calculate_risk_score(player: Player) -> float:
    """
    Calculate comprehensive risk score combining multiple factors.
    
    Risk factors:
    - Injury/suspension risk (35%)
    - Playing time availability (35%) 
    - Price volatility (20%)
    - Form consistency (10%)
    
    Args:
        player: Player object
    
    Returns:
        Risk score (0-1, where higher = more risky)
    """
    # Availability risk (injury, suspension, etc.)
    availability = calculate_availability_score(player)
    availability_risk = 1.0 - availability
    
    # Playing time risk
    if player.games_played > 0:
        minutes_per_game = player.minutes_played / player.games_played
        playing_time_risk = max(0, 1.0 - minutes_per_game / 90.0)
    else:
        playing_time_risk = 0.8  # High risk for unproven players
    
    # Price volatility risk
    volatility_risk = calculate_price_volatility(player.price_history)
    
    # Form consistency risk (high variance in recent points = risky)
    form_risk = 0.0
    if len(player.recent_points) > 1:
        form_variance = np.var(player.recent_points)
        form_risk = min(form_variance / 25.0, 1.0)  # Normalize and cap
    
    # Weighted combination
    risk_score = (
        0.35 * availability_risk +
        0.35 * playing_time_risk +
        0.20 * volatility_risk +
        0.10 * form_risk
    )
    
    return max(0.0, min(1.0, risk_score))


def get_position_scarcity_multiplier(position: Position) -> float:
    """
    Get position scarcity multiplier for valuation.
    Some positions are more scarce/valuable than others.
    
    Args:
        position: Player position
    
    Returns:
        Scarcity multiplier (1.0 = neutral)
    """
    multipliers = {
        Position.PORTERO: 0.9,  # Goalkeepers generally cheaper
        Position.DEFENSA: 1.0,  # Neutral
        Position.CENTROCAMPISTA: 1.1,  # Slightly premium
        Position.DELANTERO: 1.2  # Premium for goal scorers
    }
    
    return multipliers.get(position, 1.0)


def calculate_momentum_score(recent_points: List[int]) -> float:
    """
    Calculate momentum based on recent trend in performances.
    
    Args:
        recent_points: Points from recent games (most recent first)
    
    Returns:
        Momentum score (-1 to 1, where 1 = strong positive momentum)
    """
    if len(recent_points) < 3:
        return 0.0
    
    # Calculate trend using linear regression slope
    x = np.arange(len(recent_points))
    y = np.array(recent_points[::-1])  # Reverse to get chronological order
    
    # Simple slope calculation
    n = len(recent_points)
    slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
    
    # Normalize slope to -1 to 1 range
    momentum = np.tanh(slope / 3.0)  # tanh to bound between -1 and 1
    
    return momentum


def calculate_consistency_score(recent_points: List[int]) -> float:
    """
    Calculate consistency score based on variance in recent performances.
    
    Args:
        recent_points: Points from recent games
    
    Returns:
        Consistency score (0-1, where 1 = very consistent)
    """
    if len(recent_points) < 2:
        return 0.5  # Default moderate consistency
    
    variance = np.var(recent_points)
    mean_points = np.mean(recent_points)
    
    if mean_points == 0:
        return 0.0
    
    # Coefficient of variation (lower = more consistent)
    cv = np.sqrt(variance) / mean_points
    
    # Convert to 0-1 scale (higher = more consistent)
    consistency = np.exp(-cv)
    
    return max(0.0, min(1.0, consistency))