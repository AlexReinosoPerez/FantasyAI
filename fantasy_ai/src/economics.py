"""
Economic calculations for Fantasy LaLiga: fair value, risk assessment, and bidding strategy.
"""

import numpy as np
from typing import Dict, List, Tuple
from .schemas import Player, Position
from .forecast import expected_points_next_k, expected_points_confidence_interval
from .features import calculate_risk_score, get_position_scarcity_multiplier


# Market constants for LaLiga Fantasy
POINTS_TO_MONEY_RATIO = 0.5  # Average millions per expected point
MIN_PLAYER_PRICE = 0.5  # Minimum player price in millions
MAX_PLAYER_PRICE = 15.0  # Maximum realistic player price
MARKET_EFFICIENCY = 0.8  # How efficiently the market prices players (0-1)
RISK_FREE_RATE = 0.02  # Risk-free return rate for discounting


def calculate_fair_value(player: Player, gameweeks: int = 3, discount_rate: float = 0.05) -> float:
    """
    Calculate fair market value based on discounted future expected points.
    
    Args:
        player: Player object
        gameweeks: Number of gameweeks to consider for valuation
        discount_rate: Rate to discount future returns
    
    Returns:
        Fair value in millions
    """
    # Get expected points for the forecast period
    expected_points = expected_points_next_k(player, gameweeks)
    
    # Apply discounting for future periods
    discount_factor = 1 / (1 + discount_rate)
    discounted_points = expected_points * (discount_factor ** (gameweeks / 38))  # Normalize to season
    
    # Convert points to monetary value
    base_value = discounted_points * POINTS_TO_MONEY_RATIO
    
    # Apply position scarcity multiplier
    position_multiplier = get_position_scarcity_multiplier(player.position)
    adjusted_value = base_value * position_multiplier
    
    # Apply market efficiency adjustment
    # If market is 80% efficient, fair value should be close to market price
    current_price = player.price
    efficient_value = MARKET_EFFICIENCY * current_price + (1 - MARKET_EFFICIENCY) * adjusted_value
    
    # Ensure realistic bounds
    fair_value = max(MIN_PLAYER_PRICE, min(MAX_PLAYER_PRICE, efficient_value))
    
    return fair_value


def calculate_value_over_replacement(player: Player, replacement_value: float = None) -> float:
    """
    Calculate Value Over Replacement Player (VORP).
    
    Args:
        player: Player object
        replacement_value: Expected points from replacement player (auto-calculated if None)
    
    Returns:
        Value over replacement in points
    """
    if replacement_value is None:
        # Default replacement values by position (average bench player)
        replacement_values = {
            Position.PORTERO: 2.0,
            Position.DEFENSA: 2.5,
            Position.CENTROCAMPISTA: 3.0,
            Position.DELANTERO: 3.5
        }
        replacement_value = replacement_values.get(player.position, 3.0)
    
    player_expected = expected_points_next_k(player, 3)
    replacement_expected = replacement_value * 3  # 3 gameweeks
    
    return max(0, player_expected - replacement_expected)


def calculate_kelly_fraction(expected_return: float, win_probability: float, 
                           loss_probability: float, win_amount: float, loss_amount: float) -> float:
    """
    Calculate Kelly criterion for optimal bet sizing.
    
    Args:
        expected_return: Expected return on investment
        win_probability: Probability of positive outcome
        loss_probability: Probability of negative outcome  
        win_amount: Amount gained if successful
        loss_amount: Amount lost if unsuccessful
    
    Returns:
        Kelly fraction (0-1, representing % of bankroll to bet)
    """
    if loss_amount <= 0 or win_probability <= 0:
        return 0.0
    
    # Kelly formula: f = (bp - q) / b
    # where b = odds (win_amount/loss_amount), p = win_prob, q = loss_prob
    b = win_amount / loss_amount
    f = (b * win_probability - loss_probability) / b
    
    # Cap Kelly fraction to prevent excessive risk
    return max(0.0, min(0.25, f))  # Never bet more than 25% of bankroll


def calculate_max_bid(player: Player, bankroll: float, market_pressure: float = 0.5, 
                     risk_tolerance: float = 0.5) -> float:
    """
    Calculate maximum recommended bid for a player.
    
    Considers:
    - Fair value calculation
    - Risk assessment
    - Kelly criterion for position sizing
    - Market pressure and competition
    - Available bankroll
    
    Args:
        player: Player object
        bankroll: Available money for transfers
        market_pressure: Market demand pressure (0-1)
        risk_tolerance: User's risk tolerance (0-1)
    
    Returns:
        Maximum recommended bid in millions
    """
    # Calculate fair value
    fair_value = calculate_fair_value(player)
    
    # Calculate risk score
    risk_score = calculate_risk_score(player)
    
    # Risk-adjusted fair value
    risk_adjustment = 1.0 - (risk_score * (1.0 - risk_tolerance))
    risk_adjusted_value = fair_value * risk_adjustment
    
    # Market pressure adjustment
    # High pressure = bid closer to fair value, low pressure = bid below fair value
    pressure_multiplier = 0.8 + (market_pressure * 0.4)  # Range: 0.8 to 1.2
    market_adjusted_value = risk_adjusted_value * pressure_multiplier
    
    # Kelly criterion for position sizing
    expected_points = expected_points_next_k(player, 3)
    current_value = player.price
    
    # Estimate win/loss scenarios
    win_probability = max(0.1, min(0.9, 1.0 - risk_score))
    loss_probability = 1.0 - win_probability
    
    # Potential gain/loss amounts (simplified)
    potential_gain = max(0, fair_value - current_value)
    potential_loss = min(current_value * 0.3, bankroll * 0.1)  # Limit downside
    
    if potential_gain > 0 and potential_loss > 0:
        kelly_fraction = calculate_kelly_fraction(
            expected_return=potential_gain,
            win_probability=win_probability,
            loss_probability=loss_probability,
            win_amount=potential_gain,
            loss_amount=potential_loss
        )
        kelly_adjusted_bankroll = bankroll * kelly_fraction
    else:
        kelly_adjusted_bankroll = bankroll * 0.1  # Conservative default
    
    # Final maximum bid
    max_bid = min(
        market_adjusted_value,
        kelly_adjusted_bankroll,
        bankroll * 0.5  # Never spend more than 50% of bankroll on one player
    )
    
    # Ensure minimum viable bid
    min_bid = player.price * 0.9  # At least 90% of current price
    max_bid = max(min_bid, max_bid)
    
    return max_bid


def calculate_bid_range(player: Player, bankroll: float, market_pressure: float = 0.5,
                       risk_tolerance: float = 0.5) -> Tuple[float, float, float]:
    """
    Calculate recommended bidding range for a player.
    
    Args:
        player: Player object
        bankroll: Available money
        market_pressure: Market demand pressure (0-1)
        risk_tolerance: Risk tolerance (0-1)
    
    Returns:
        Tuple of (min_bid, fair_value, max_bid)
    """
    fair_value = calculate_fair_value(player)
    max_bid = calculate_max_bid(player, bankroll, market_pressure, risk_tolerance)
    
    # Minimum bid should be conservative
    min_bid = min(
        player.price * 0.95,  # 5% below current price
        fair_value * 0.85     # 15% below fair value
    )
    
    # Ensure logical ordering
    min_bid = max(MIN_PLAYER_PRICE, min_bid)
    max_bid = max(min_bid, max_bid)
    fair_value = max(min_bid, min(max_bid, fair_value))
    
    return (min_bid, fair_value, max_bid)


def calculate_expected_roi(player: Player, purchase_price: float, holding_period: int = 10) -> float:
    """
    Calculate expected return on investment for a player purchase.
    
    Args:
        player: Player object
        purchase_price: Price to purchase player
        holding_period: Number of gameweeks to hold player
    
    Returns:
        Expected ROI as a percentage
    """
    if purchase_price <= 0:
        return 0.0
    
    # Expected points over holding period
    expected_points = expected_points_next_k(player, min(holding_period, 10))
    
    # Estimate future selling price based on performance
    performance_multiplier = expected_points / (holding_period * 4)  # Assume 4 pts/game baseline
    performance_multiplier = max(0.8, min(1.3, performance_multiplier))  # Cap between 80%-130%
    
    estimated_selling_price = purchase_price * performance_multiplier
    
    # Points value during ownership
    points_value = expected_points * POINTS_TO_MONEY_RATIO
    
    # Total return = capital appreciation + points value
    total_return = (estimated_selling_price - purchase_price) + points_value
    
    # ROI percentage
    roi = (total_return / purchase_price) * 100
    
    return roi


def assess_price_trend(player: Player, trend_window: int = 5) -> str:
    """
    Assess recent price trend for a player.
    
    Args:
        player: Player object
        trend_window: Number of recent price points to analyze
    
    Returns:
        Trend assessment: "Rising", "Falling", "Stable", "Unknown"
    """
    if len(player.price_history) < 2:
        return "Unknown"
    
    recent_prices = player.price_history[:trend_window]
    
    if len(recent_prices) < 2:
        return "Unknown"
    
    # Calculate trend using linear regression
    x = np.arange(len(recent_prices))
    y = np.array(recent_prices)
    
    # Calculate slope
    slope = np.polyfit(x, y, 1)[0]
    
    # Classify trend
    if slope > 0.05:  # Rising by more than 0.05M per period
        return "Rising"
    elif slope < -0.05:  # Falling by more than 0.05M per period
        return "Falling"
    else:
        return "Stable"


def calculate_market_timing_score(player: Player) -> float:
    """
    Calculate timing score for purchasing a player (0-1, higher = better timing).
    
    Args:
        player: Player object
    
    Returns:
        Market timing score (0-1)
    """
    # Factor 1: Price trend (buy when falling)
    trend = assess_price_trend(player)
    trend_scores = {
        "Falling": 1.0,
        "Stable": 0.7,
        "Rising": 0.3,
        "Unknown": 0.5
    }
    trend_score = trend_scores.get(trend, 0.5)
    
    # Factor 2: Current price vs recent high/low
    if len(player.price_history) >= 5:
        recent_high = max(player.price_history[:5])
        recent_low = min(player.price_history[:5])
        
        if recent_high > recent_low:
            price_position = (player.price - recent_low) / (recent_high - recent_low)
            price_score = 1.0 - price_position  # Better to buy near recent low
        else:
            price_score = 0.5
    else:
        price_score = 0.5
    
    # Factor 3: Form vs price (undervalued if good form, low price)
    fair_value = calculate_fair_value(player)
    if player.price > 0:
        value_score = min(1.0, fair_value / player.price)  # Better if fair value > current price
    else:
        value_score = 0.5
    
    # Combine factors
    timing_score = (
        0.4 * trend_score +
        0.3 * price_score +
        0.3 * value_score
    )
    
    return max(0.0, min(1.0, timing_score))