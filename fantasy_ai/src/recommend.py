"""
Recommendation engine for Fantasy LaLiga decisions.
Analyzes teams, market, and provides actionable recommendations.
"""

from typing import List, Dict, Tuple
import numpy as np
from .schemas import (
    Player, TeamState, Market, RivalTeam, Position, PlayerAnalysis, 
    TeamAnalysis, MarketAnalysis, SwapRecommendation, BidRecommendation,
    DifferentialAnalysis, RecommendationResponse
)
from .forecast import expected_points_next_k, calculate_points_per_million
from .economics import (
    calculate_fair_value, calculate_max_bid, calculate_bid_range,
    calculate_expected_roi, calculate_market_timing_score
)
from .features import calculate_risk_score, calculate_form_score


def analyze_player(player: Player, bankroll: float = 10.0) -> PlayerAnalysis:
    """
    Perform comprehensive analysis of a single player.
    
    Args:
        player: Player object
        bankroll: Available bankroll for context
    
    Returns:
        PlayerAnalysis object with all metrics
    """
    expected_points = expected_points_next_k(player, 3)
    form_score = calculate_form_score(player.recent_points)
    risk_score = calculate_risk_score(player)
    fair_value = calculate_fair_value(player)
    value_ratio = calculate_points_per_million(player, 3)
    
    # Availability score (inverse of risk components)
    availability_score = max(0.0, 1.0 - risk_score)
    
    # Fixture difficulty (simplified)
    fixture_difficulty = 3.0  # Default neutral, would be calculated from fixtures
    
    return PlayerAnalysis(
        player_id=player.id,
        expected_points_next_3=expected_points,
        form_score=form_score,
        fixture_difficulty=fixture_difficulty,
        availability_score=availability_score,
        risk_score=risk_score,
        fair_value=fair_value,
        value_ratio=value_ratio
    )


def analyze_myteam(team_state: TeamState) -> TeamAnalysis:
    """
    Analyze user's current team and identify strengths/weaknesses.
    
    Args:
        team_state: Current team state
    
    Returns:
        TeamAnalysis with players to sell/keep and team balance assessment
    """
    players_to_sell = []
    players_to_keep = []
    position_counts = {pos: 0 for pos in Position}
    
    # Analyze each player
    for player in team_state.players:
        analysis = analyze_player(player, team_state.bankroll)
        
        # Count positions
        position_counts[player.position] += 1
        
        # Decision criteria for selling
        should_sell = (
            analysis.risk_score > 0.7 or  # High risk
            analysis.form_score < 3.0 or  # Poor form
            analysis.value_ratio < 1.5 or  # Poor value
            analysis.expected_points_next_3 < 6.0  # Low expected points
        )
        
        if should_sell:
            players_to_sell.append(analysis)
        else:
            players_to_keep.append(analysis)
    
    # Identify weak positions (fewer than recommended)
    recommended_counts = {
        Position.PORTERO: 2,
        Position.DEFENSA: 5,
        Position.CENTROCAMPISTA: 5,
        Position.DELANTERO: 3
    }
    
    weak_positions = []
    for position, recommended in recommended_counts.items():
        if position_counts[position] < recommended:
            weak_positions.append(position)
    
    # Calculate team balance score
    total_expected = sum(p.expected_points_next_3 for p in players_to_keep + players_to_sell)
    avg_risk = np.mean([p.risk_score for p in players_to_keep + players_to_sell]) if team_state.players else 0.5
    position_balance = len(weak_positions) / len(Position)  # 0 = perfect, 1 = all positions weak
    
    team_balance_score = max(0.0, min(1.0, 1.0 - position_balance - avg_risk * 0.3))
    
    return TeamAnalysis(
        players_to_sell=players_to_sell,
        players_to_keep=players_to_keep,
        weak_positions=weak_positions,
        team_balance_score=team_balance_score
    )


def analyze_market(market: Market, top_n: int = 20) -> MarketAnalysis:
    """
    Analyze market to identify best buys, overpriced players, and bargains.
    
    Args:
        market: Market state with available players
        top_n: Number of top players to return in each category
    
    Returns:
        MarketAnalysis with categorized player recommendations
    """
    all_analyses = []
    
    # Analyze all available players
    for player in market.available_players:
        analysis = analyze_player(player)
        all_analyses.append(analysis)
    
    # Sort by different criteria
    by_value_ratio = sorted(all_analyses, key=lambda x: x.value_ratio, reverse=True)
    by_expected_points = sorted(all_analyses, key=lambda x: x.expected_points_next_3, reverse=True)
    by_fair_value_ratio = sorted(all_analyses, key=lambda x: x.fair_value / 
                                 next(p.price for p in market.available_players if p.id == x.player_id), 
                                 reverse=True)
    
    # Best buys: High value ratio + good expected points + low risk
    best_buys = []
    for analysis in by_value_ratio[:top_n * 2]:  # Consider top candidates
        player = next(p for p in market.available_players if p.id == analysis.player_id)
        if (analysis.value_ratio > 2.0 and 
            analysis.expected_points_next_3 > 8.0 and 
            analysis.risk_score < 0.5):
            best_buys.append(analysis)
    best_buys = best_buys[:top_n]
    
    # Overpriced: High price relative to fair value + poor value ratio
    overpriced = []
    for analysis in all_analyses:
        player = next(p for p in market.available_players if p.id == analysis.player_id)
        fair_value_ratio = analysis.fair_value / player.price if player.price > 0 else 0
        if fair_value_ratio < 0.8 and analysis.value_ratio < 1.5:
            overpriced.append(analysis)
    overpriced = sorted(overpriced, key=lambda x: x.value_ratio)[:top_n]
    
    # Bargains: Underpriced relative to fair value but good potential
    bargains = []
    for analysis in all_analyses:
        player = next(p for p in market.available_players if p.id == analysis.player_id)
        fair_value_ratio = analysis.fair_value / player.price if player.price > 0 else 0
        if (fair_value_ratio > 1.2 and 
            analysis.expected_points_next_3 > 6.0 and 
            analysis.form_score > 4.0):
            bargains.append(analysis)
    bargains = sorted(bargains, key=lambda x: x.fair_value / 
                      next(p.price for p in market.available_players if p.id == x.player_id), 
                      reverse=True)[:top_n]
    
    # Market trends (simplified)
    market_trends = {
        "avg_value_ratio": np.mean([a.value_ratio for a in all_analyses]),
        "avg_risk_score": np.mean([a.risk_score for a in all_analyses]),
        "high_value_count": len([a for a in all_analyses if a.value_ratio > 3.0]),
        "bargain_count": len(bargains)
    }
    
    return MarketAnalysis(
        best_buys=best_buys,
        overpriced=overpriced,
        bargains=bargains,
        market_trends=market_trends
    )


def recommend_swaps(team_state: TeamState, market: Market, max_recommendations: int = 10) -> List[SwapRecommendation]:
    """
    Recommend player swaps (sell + buy combinations).
    
    Args:
        team_state: Current team state
        market: Market state
        max_recommendations: Maximum number of swap recommendations
    
    Returns:
        List of SwapRecommendation objects
    """
    team_analysis = analyze_myteam(team_state)
    market_analysis = analyze_market(market)
    
    swap_recommendations = []
    
    # Consider each player to sell
    for sell_candidate in team_analysis.players_to_sell:
        sell_player = next(p for p in team_state.players if p.id == sell_candidate.player_id)
        
        # Find potential replacements in same position
        position_targets = [
            p for p in market.available_players 
            if p.position == sell_player.position and p.price <= sell_player.price * 1.2
        ]
        
        # Also consider players from best buys and bargains
        target_ids = set()
        for buy_list in [market_analysis.best_buys, market_analysis.bargains]:
            for analysis in buy_list:
                buy_player = next(p for p in market.available_players if p.id == analysis.player_id)
                if buy_player.position == sell_player.position:
                    target_ids.add(analysis.player_id)
        
        # Analyze each potential swap
        for target_id in target_ids:
            buy_player = next(p for p in market.available_players if p.id == target_id)
            buy_analysis = next(a for a in market_analysis.best_buys + market_analysis.bargains 
                               if a.player_id == target_id)
            
            cost_difference = buy_player.price - sell_player.price
            
            # Check if affordable
            if cost_difference <= team_state.bankroll:
                expected_points_gain = (buy_analysis.expected_points_next_3 - 
                                       sell_candidate.expected_points_next_3)
                
                # Risk assessment
                risk_improvement = sell_candidate.risk_score - buy_analysis.risk_score
                if risk_improvement > 0.2:
                    risk_assessment = "Lower risk"
                elif risk_improvement < -0.2:
                    risk_assessment = "Higher risk"
                else:
                    risk_assessment = "Similar risk"
                
                # Calculate confidence based on multiple factors
                confidence = min(1.0, max(0.0, (
                    0.4 * (expected_points_gain / 10.0) +  # Points improvement
                    0.3 * (buy_analysis.value_ratio / 4.0) +  # Value ratio
                    0.2 * risk_improvement +  # Risk improvement
                    0.1 * (buy_analysis.form_score / 10.0)  # Form score
                )))
                
                # Only recommend if there's clear benefit
                if expected_points_gain > 2.0 or (expected_points_gain > 0 and risk_improvement > 0.1):
                    swap_recommendations.append(SwapRecommendation(
                        sell_player_id=sell_player.id,
                        buy_player_id=buy_player.id,
                        expected_points_gain=expected_points_gain,
                        cost_difference=cost_difference,
                        risk_assessment=risk_assessment,
                        confidence=confidence
                    ))
    
    # Sort by expected points gain and confidence
    swap_recommendations.sort(
        key=lambda x: x.expected_points_gain * x.confidence, 
        reverse=True
    )
    
    return swap_recommendations[:max_recommendations]


def recommend_bids(team_state: TeamState, market: Market, 
                   target_players: List[int] = None) -> List[BidRecommendation]:
    """
    Recommend bidding ranges for target players.
    
    Args:
        team_state: Current team state
        market: Market state
        target_players: Specific player IDs to analyze (if None, uses market analysis)
    
    Returns:
        List of BidRecommendation objects
    """
    if target_players is None:
        # Use best buys and bargains from market analysis
        market_analysis = analyze_market(market)
        target_players = []
        for analysis in market_analysis.best_buys + market_analysis.bargains:
            target_players.append(analysis.player_id)
    
    bid_recommendations = []
    
    for player_id in target_players:
        player = next((p for p in market.available_players if p.id == player_id), None)
        if not player:
            continue
        
        # Calculate bid range
        min_bid, fair_value, max_bid = calculate_bid_range(
            player, 
            team_state.bankroll,
            market_pressure=0.5,  # Could be calculated from market data
            risk_tolerance=0.5    # Could be user preference
        )
        
        # Risk assessment
        risk_score = calculate_risk_score(player)
        if risk_score < 0.3:
            risk_level = "Low"
        elif risk_score < 0.6:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        # Market pressure (simplified - could be enhanced with real market data)
        market_pressure = 0.5  # Default neutral pressure
        
        bid_recommendations.append(BidRecommendation(
            player_id=player_id,
            min_bid=min_bid,
            max_bid=max_bid,
            fair_value=fair_value,
            risk_level=risk_level,
            market_pressure=market_pressure
        ))
    
    return bid_recommendations


def find_differentials(team_state: TeamState, market: Market, 
                      rivals: List[RivalTeam], min_ownership_threshold: float = 0.3) -> List[DifferentialAnalysis]:
    """
    Find differential players - good options that rivals don't have.
    
    Args:
        team_state: Current team state
        market: Market state
        rivals: List of rival teams
        min_ownership_threshold: Minimum ownership % to exclude from differentials
    
    Returns:
        List of DifferentialAnalysis objects
    """
    if not rivals:
        return []
    
    # Calculate ownership percentages for each player
    total_rivals = len(rivals)
    player_ownership = {}
    
    for player in market.available_players:
        owned_by = sum(1 for rival in rivals if player.id in rival.players)
        ownership_pct = owned_by / total_rivals
        player_ownership[player.id] = ownership_pct
    
    # Find players with low ownership but good potential
    differentials = []
    market_analysis = analyze_market(market)
    
    # Consider players from best buys and bargains with low ownership
    potential_differentials = market_analysis.best_buys + market_analysis.bargains
    
    for analysis in potential_differentials:
        ownership_pct = player_ownership.get(analysis.player_id, 0.0)
        
        # Only consider if ownership is below threshold
        if ownership_pct <= min_ownership_threshold:
            player = next(p for p in market.available_players if p.id == analysis.player_id)
            
            # Calculate differential value (higher = better differential)
            differential_value = (
                analysis.expected_points_next_3 * (1.0 - ownership_pct) * 
                min(analysis.value_ratio / 2.0, 2.0)  # Cap value ratio impact
            )
            
            # Risk-reward ratio
            risk_reward_ratio = analysis.expected_points_next_3 / max(analysis.risk_score, 0.1)
            
            differentials.append(DifferentialAnalysis(
                player_id=analysis.player_id,
                ownership_percentage=ownership_pct * 100,  # Convert to percentage
                differential_value=differential_value,
                risk_reward_ratio=risk_reward_ratio
            ))
    
    # Sort by differential value
    differentials.sort(key=lambda x: x.differential_value, reverse=True)
    
    return differentials[:15]  # Return top 15 differentials


def generate_comprehensive_recommendations(
    team_state: TeamState, 
    market: Market, 
    rivals: List[RivalTeam] = None
) -> RecommendationResponse:
    """
    Generate comprehensive recommendations combining all analysis.
    
    Args:
        team_state: Current team state
        market: Market state  
        rivals: List of rival teams (optional)
    
    Returns:
        Complete RecommendationResponse with all recommendations
    """
    # Perform all analyses
    team_analysis = analyze_myteam(team_state)
    market_analysis = analyze_market(market)
    swap_recommendations = recommend_swaps(team_state, market)
    bid_recommendations = recommend_bids(team_state, market)
    
    # Find differentials if rivals provided
    differentials = []
    if rivals:
        differentials = find_differentials(team_state, market, rivals)
    
    # Generate summary
    summary_parts = []
    
    if team_analysis.players_to_sell:
        summary_parts.append(f"Consider selling {len(team_analysis.players_to_sell)} players.")
    
    if market_analysis.best_buys:
        top_buy = market_analysis.best_buys[0]
        player = next(p for p in market.available_players if p.id == top_buy.player_id)
        summary_parts.append(f"Top target: {player.name} (value ratio: {top_buy.value_ratio:.1f}).")
    
    if swap_recommendations:
        top_swap = swap_recommendations[0]
        summary_parts.append(f"Best swap gains {top_swap.expected_points_gain:.1f} points.")
    
    if differentials:
        summary_parts.append(f"Found {len(differentials)} differential opportunities.")
    
    summary = " ".join(summary_parts) if summary_parts else "No major changes recommended."
    
    return RecommendationResponse(
        team_analysis=team_analysis,
        market_analysis=market_analysis,
        swap_recommendations=swap_recommendations,
        bid_recommendations=bid_recommendations,
        differentials=differentials,
        summary=summary
    )