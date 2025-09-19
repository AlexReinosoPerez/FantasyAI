"""
Forecasting engine for predicting expected points.
"""

import numpy as np
from typing import Dict, List
from .schemas import Player, Position
from .features import (
    calculate_form_score, 
    calculate_fixture_difficulty, 
    calculate_availability_score,
    get_position_scarcity_multiplier,
    calculate_momentum_score,
    FDR_TABLE
)


# Base expected points per game by position (from historical LaLiga data)
BASE_POINTS_BY_POSITION = {
    Position.PORTERO: 3.5,
    Position.DEFENSA: 4.2,
    Position.CENTROCAMPISTA: 4.8,
    Position.DELANTERO: 5.1
}


def calculate_base_points_per_game(player: Player) -> float:
    """
    Calculate base expected points per game for a player.
    
    Args:
        player: Player object
    
    Returns:
        Base points per game based on historical performance
    """
    if player.games_played > 0:
        historical_ppg = player.total_points / player.games_played
        # Weight historical performance with position baseline
        position_baseline = BASE_POINTS_BY_POSITION.get(player.position, 4.0)
        
        # Give more weight to historical data if player has played enough games
        if player.games_played >= 5:
            weight_historical = 0.8
        else:
            weight_historical = 0.5
            
        base_ppg = weight_historical * historical_ppg + (1 - weight_historical) * position_baseline
    else:
        # New/unproven player - use position baseline
        base_ppg = BASE_POINTS_BY_POSITION.get(player.position, 4.0)
    
    return base_ppg


def apply_form_adjustment(base_points: float, player: Player) -> float:
    """
    Adjust base points based on current form.
    
    Args:
        base_points: Base expected points per game
        player: Player object
    
    Returns:
        Form-adjusted points per game
    """
    form_score = calculate_form_score(player.recent_points)
    
    # Convert form score (0-10) to multiplier (0.5-1.5)
    # Form of 5 = neutral (1.0x), form of 10 = 1.5x, form of 0 = 0.5x
    form_multiplier = 0.5 + (form_score / 10.0)
    
    # Apply momentum factor
    momentum = calculate_momentum_score(player.recent_points)
    momentum_adjustment = 1.0 + (momentum * 0.2)  # ±20% based on momentum
    
    adjusted_points = base_points * form_multiplier * momentum_adjustment
    
    return max(0.0, adjusted_points)


def apply_fixture_adjustment(points_per_game: float, player: Player, gameweeks: int = 3) -> float:
    """
    Adjust points based on fixture difficulty.
    
    Args:
        points_per_game: Form-adjusted points per game
        player: Player object
        gameweeks: Number of gameweeks to consider
    
    Returns:
        Fixture-adjusted points per game
    """
    # Get fixtures for the specified gameweeks
    fixtures_to_consider = player.next_fixtures[:gameweeks]
    
    if not fixtures_to_consider:
        return points_per_game
    
    avg_difficulty = calculate_fixture_difficulty(fixtures_to_consider)
    
    # Convert difficulty (1-5) to adjustment factor
    # Difficulty 1 = 1.2x points, Difficulty 5 = 0.7x points, Difficulty 3 = 1.0x
    difficulty_multiplier = 1.45 - (avg_difficulty * 0.15)
    
    # Apply position-specific fixture sensitivity
    position_sensitivity = {
        Position.PORTERO: 0.8,      # Goalkeepers less affected by fixtures
        Position.DEFENSA: 1.0,      # Defenders moderately affected
        Position.CENTROCAMPISTA: 1.1,  # Midfielders more affected
        Position.DELANTERO: 1.2     # Forwards most affected by fixtures
    }
    
    sensitivity = position_sensitivity.get(player.position, 1.0)
    adjusted_multiplier = 1.0 + (difficulty_multiplier - 1.0) * sensitivity
    
    return points_per_game * adjusted_multiplier


def apply_availability_adjustment(points_per_game: float, player: Player) -> float:
    """
    Adjust points based on availability/injury risk.
    
    Args:
        points_per_game: Fixture-adjusted points per game
        player: Player object
    
    Returns:
        Availability-adjusted points per game
    """
    availability_score = calculate_availability_score(player)
    
    # Reduce expected points based on availability risk
    adjusted_points = points_per_game * availability_score
    
    return adjusted_points


def expected_points_next_k(player: Player, k: int = 3, fdr_table: Dict[str, int] = None) -> float:
    """
    Calculate expected points for next k gameweeks.
    
    This is the main forecasting function that combines:
    - Base points per game (historical + position baseline)
    - Form adjustment (recent performance trend)
    - Fixture difficulty adjustment
    - Availability adjustment (injury/suspension risk)
    
    Args:
        player: Player object
        k: Number of gameweeks to predict (default 3)
        fdr_table: Fixture difficulty ratings (optional)
    
    Returns:
        Total expected points for next k gameweeks
    """
    # Step 1: Calculate base points per game
    base_ppg = calculate_base_points_per_game(player)
    
    # Step 2: Apply form adjustment
    form_adjusted_ppg = apply_form_adjustment(base_ppg, player)
    
    # Step 3: Apply fixture adjustment
    fixture_adjusted_ppg = apply_fixture_adjustment(form_adjusted_ppg, player, k)
    
    # Step 4: Apply availability adjustment
    final_ppg = apply_availability_adjustment(fixture_adjusted_ppg, player)
    
    # Step 5: Calculate total for k gameweeks
    total_expected_points = final_ppg * k
    
    return max(0.0, total_expected_points)


def expected_points_confidence_interval(player: Player, k: int = 3, confidence: float = 0.8) -> tuple:
    """
    Calculate confidence interval for expected points prediction.
    
    Args:
        player: Player object
        k: Number of gameweeks
        confidence: Confidence level (0.8 = 80%)
    
    Returns:
        Tuple of (lower_bound, expected, upper_bound)
    """
    expected = expected_points_next_k(player, k)
    
    # Calculate variance based on recent performance and position
    if len(player.recent_points) >= 2:
        recent_variance = np.var(player.recent_points)
    else:
        # Default variance by position
        position_variance = {
            Position.PORTERO: 4.0,
            Position.DEFENSA: 6.0,
            Position.CENTROCAMPISTA: 8.0,
            Position.DELANTERO: 10.0
        }
        recent_variance = position_variance.get(player.position, 8.0)
    
    # Scale variance by number of gameweeks
    total_variance = recent_variance * k
    std_dev = np.sqrt(total_variance)
    
    # Calculate confidence interval
    # For 80% confidence, use ±1.28 standard deviations
    # For 95% confidence, use ±1.96 standard deviations
    z_scores = {0.8: 1.28, 0.9: 1.645, 0.95: 1.96, 0.99: 2.576}
    z_score = z_scores.get(confidence, 1.28)
    
    margin = z_score * std_dev
    lower_bound = max(0.0, expected - margin)
    upper_bound = expected + margin
    
    return (lower_bound, expected, upper_bound)


def batch_forecast_players(players: List[Player], k: int = 3) -> Dict[int, float]:
    """
    Batch forecast expected points for multiple players.
    
    Args:
        players: List of Player objects
        k: Number of gameweeks to predict
    
    Returns:
        Dictionary mapping player_id to expected points
    """
    forecasts = {}
    
    for player in players:
        expected_pts = expected_points_next_k(player, k)
        forecasts[player.id] = expected_pts
    
    return forecasts


def calculate_points_per_million(player: Player, k: int = 3) -> float:
    """
    Calculate expected points per million spent (value ratio).
    
    Args:
        player: Player object
        k: Number of gameweeks
    
    Returns:
        Points per million ratio
    """
    if player.price <= 0:
        return 0.0
    
    expected_pts = expected_points_next_k(player, k)
    return expected_pts / player.price


def rank_players_by_value(players: List[Player], k: int = 3) -> List[tuple]:
    """
    Rank players by value (points per million).
    
    Args:
        players: List of Player objects
        k: Number of gameweeks for forecasting
    
    Returns:
        List of tuples (player, expected_points, points_per_million) sorted by value
    """
    player_values = []
    
    for player in players:
        expected_pts = expected_points_next_k(player, k)
        ppm = calculate_points_per_million(player, k)
        player_values.append((player, expected_pts, ppm))
    
    # Sort by points per million (descending)
    player_values.sort(key=lambda x: x[2], reverse=True)
    
    return player_values