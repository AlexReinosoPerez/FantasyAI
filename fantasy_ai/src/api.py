"""
FastAPI endpoints for Fantasy LaLiga decision assistant.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
from contextlib import asynccontextmanager

from .schemas import (
    Player, TeamState, Market, RivalTeam, PlayerAnalysis,
    TeamAnalysis, MarketAnalysis, SwapRecommendation, 
    BidRecommendation, DifferentialAnalysis, RecommendationResponse
)
from .recommend import (
    analyze_myteam, analyze_market, recommend_swaps,
    recommend_bids, find_differentials, generate_comprehensive_recommendations
)
from .loaders import (
    load_players_from_json, load_team_state_from_json,
    load_market_from_json, load_rivals_from_json, create_sample_data_files
)


# Global data storage (in production, this would be a database)
app_data = {
    "players": [],
    "sample_team": None,
    "sample_market": None,
    "sample_rivals": []
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to load initial data."""
    try:
        # Create sample data on startup
        create_sample_data_files()
        print("✅ Sample data files created")
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
    
    yield
    
    # Cleanup on shutdown
    print("🔄 Application shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Fantasy LaLiga Decision Assistant",
    description="AI-powered decision assistant for Fantasy LaLiga",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Fantasy LaLiga Decision Assistant API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "team_analysis": "/analysis/myteam",
            "market_analysis": "/analysis/market", 
            "swap_recommendations": "/recommend/swaps",
            "bid_recommendations": "/recommend/bids",
            "differentials": "/league/differentials",
            "comprehensive": "/recommend/comprehensive"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "fantasy-ai-api"}


@app.post("/analysis/myteam", response_model=TeamAnalysis, tags=["Analysis"])
async def analyze_my_team(team_state: TeamState):
    """
    Analyze user's team and identify players to sell vs keep.
    
    Args:
        team_state: Current team state with players and financial info
    
    Returns:
        TeamAnalysis with players to sell/keep and team balance assessment
    """
    try:
        analysis = analyze_myteam(team_state)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing team: {str(e)}"
        )


@app.post("/analysis/market", response_model=MarketAnalysis, tags=["Analysis"])
async def analyze_market_endpoint(market: Market):
    """
    Analyze market to find best buys, overpriced players, and bargains.
    
    Args:
        market: Market state with available players
    
    Returns:
        MarketAnalysis with categorized player recommendations
    """
    try:
        analysis = analyze_market(market)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing market: {str(e)}"
        )


@app.post("/recommend/swaps", response_model=List[SwapRecommendation], tags=["Recommendations"])
async def recommend_player_swaps(team_state: TeamState, market: Market):
    """
    Recommend player swaps (sell + buy combinations).
    
    Args:
        team_state: Current team state
        market: Market state with available players
    
    Returns:
        List of swap recommendations with expected points gain
    """
    try:
        swaps = recommend_swaps(team_state, market)
        return swaps
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating swap recommendations: {str(e)}"
        )


@app.post("/recommend/bids", response_model=List[BidRecommendation], tags=["Recommendations"])
async def recommend_bidding_strategy(
    team_state: TeamState, 
    market: Market,
    target_players: Optional[List[int]] = None
):
    """
    Recommend bidding ranges for target players.
    
    Args:
        team_state: Current team state
        market: Market state with available players
        target_players: Optional list of specific player IDs to analyze
    
    Returns:
        List of bid recommendations with min/max ranges and risk assessment
    """
    try:
        bids = recommend_bids(team_state, market, target_players)
        return bids
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating bid recommendations: {str(e)}"
        )


@app.post("/league/differentials", response_model=List[DifferentialAnalysis], tags=["League"])
async def find_differential_players(
    team_state: TeamState,
    market: Market, 
    rivals: List[RivalTeam],
    min_ownership_threshold: float = 0.3
):
    """
    Find differential players - good options that rivals don't have.
    
    Args:
        team_state: Current team state
        market: Market state
        rivals: List of rival teams
        min_ownership_threshold: Maximum ownership % to be considered differential
    
    Returns:
        List of differential player analyses
    """
    try:
        differentials = find_differentials(team_state, market, rivals, min_ownership_threshold)
        return differentials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding differentials: {str(e)}"
        )


@app.post("/recommend/comprehensive", response_model=RecommendationResponse, tags=["Recommendations"])
async def comprehensive_recommendations(
    team_state: TeamState,
    market: Market,
    rivals: Optional[List[RivalTeam]] = None
):
    """
    Generate comprehensive recommendations combining all analyses.
    
    Args:
        team_state: Current team state
        market: Market state
        rivals: Optional list of rival teams
    
    Returns:
        Complete recommendation response with all analyses
    """
    try:
        recommendations = generate_comprehensive_recommendations(team_state, market, rivals)
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating comprehensive recommendations: {str(e)}"
        )


# Sample data endpoints for testing
@app.get("/sample/players", response_model=List[Player], tags=["Sample Data"])
async def get_sample_players():
    """Get sample player data for testing."""
    try:
        from .loaders import get_data_file_path, load_players_from_json
        file_path = get_data_file_path('sample_players.json')
        players = load_players_from_json(file_path)
        return players
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample players not found: {str(e)}"
        )


@app.get("/sample/team", response_model=TeamState, tags=["Sample Data"])
async def get_sample_team():
    """Get sample team data for testing."""
    try:
        from .loaders import get_data_file_path, load_team_state_from_json
        file_path = get_data_file_path('sample_team.json')
        team = load_team_state_from_json(file_path)
        return team
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample team not found: {str(e)}"
        )


@app.get("/sample/market", response_model=Market, tags=["Sample Data"])
async def get_sample_market():
    """Get sample market data for testing."""
    try:
        from .loaders import get_data_file_path, load_market_from_json
        file_path = get_data_file_path('sample_market.json')
        market = load_market_from_json(file_path)
        return market
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample market not found: {str(e)}"
        )


@app.get("/sample/rivals", response_model=List[RivalTeam], tags=["Sample Data"])
async def get_sample_rivals():
    """Get sample rival team data for testing."""
    try:
        from .loaders import get_data_file_path, load_rivals_from_json
        file_path = get_data_file_path('sample_rivals.json')
        rivals = load_rivals_from_json(file_path)
        return rivals
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample rivals not found: {str(e)}"
        )


@app.post("/demo/quick-analysis", response_model=RecommendationResponse, tags=["Demo"])
async def quick_demo_analysis():
    """
    Quick demo using sample data to showcase the system.
    """
    try:
        from .loaders import get_data_file_path, load_team_state_from_json, load_market_from_json, load_rivals_from_json
        
        # Load sample data
        team_path = get_data_file_path('sample_team.json')
        market_path = get_data_file_path('sample_market.json')
        rivals_path = get_data_file_path('sample_rivals.json')
        
        team_state = load_team_state_from_json(team_path)
        market = load_market_from_json(market_path)
        rivals = load_rivals_from_json(rivals_path)
        
        # Generate comprehensive recommendations
        recommendations = generate_comprehensive_recommendations(team_state, market, rivals)
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running demo analysis: {str(e)}"
        )


# Utility endpoints
@app.get("/players/{player_id}", response_model=PlayerAnalysis, tags=["Players"])
async def get_player_analysis(player_id: int):
    """
    Get detailed analysis for a specific player.
    """
    try:
        from .loaders import get_data_file_path, load_players_from_json
        from .recommend import analyze_player
        
        # Load players and find the specific one
        file_path = get_data_file_path('sample_players.json')
        players = load_players_from_json(file_path)
        
        player = next((p for p in players if p.id == player_id), None)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with ID {player_id} not found"
            )
        
        analysis = analyze_player(player)
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing player: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )