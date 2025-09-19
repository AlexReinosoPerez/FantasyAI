"""
Streamlit dashboard for Fantasy LaLiga Decision Assistant.
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
import numpy as np

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Fantasy LaLiga Assistant",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)


def make_api_request(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None):
    """Make API request to the backend."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None


def load_sample_data():
    """Load sample data from API."""
    data = {}
    
    # Load sample data
    endpoints = {
        'team': '/sample/team',
        'market': '/sample/market', 
        'players': '/sample/players',
        'rivals': '/sample/rivals'
    }
    
    for key, endpoint in endpoints.items():
        result = make_api_request(endpoint)
        if result:
            data[key] = result
    
    return data


def display_player_table(players_analysis, title="Players"):
    """Display players in a formatted table."""
    if not players_analysis:
        st.write("No players to display.")
        return
    
    # Convert to DataFrame for display
    player_data = []
    for analysis in players_analysis:
        player_data.append({
            "Player ID": analysis['player_id'],
            "Expected Points": f"{analysis['expected_points_next_3']:.1f}",
            "Form Score": f"{analysis['form_score']:.1f}",
            "Value Ratio": f"{analysis['value_ratio']:.1f}",
            "Risk Score": f"{analysis['risk_score']:.1f}",
            "Fair Value": f"{analysis['fair_value']:.1f}M"
        })
    
    if player_data:
        df = pd.DataFrame(player_data)
        st.subheader(title)
        st.dataframe(df, use_container_width=True)


def display_swap_recommendations(swaps):
    """Display swap recommendations."""
    if not swaps:
        st.write("No swap recommendations available.")
        return
    
    st.subheader("🔄 Swap Recommendations")
    
    for i, swap in enumerate(swaps):
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.metric(
                "Sell Player",
                f"ID: {swap['sell_player_id']}"
            )
        
        with col2:
            st.metric(
                "Buy Player", 
                f"ID: {swap['buy_player_id']}"
            )
        
        with col3:
            st.metric(
                "Points Gain",
                f"{swap['expected_points_gain']:.1f}",
                f"Cost: {swap['cost_difference']:.1f}M"
            )
            st.caption(f"Risk: {swap['risk_assessment']} | Confidence: {swap['confidence']:.1%}")
        
        st.divider()


def display_bid_recommendations(bids):
    """Display bidding recommendations."""
    if not bids:
        st.write("No bid recommendations available.")
        return
    
    st.subheader("💰 Bidding Strategy")
    
    bid_data = []
    for bid in bids:
        bid_data.append({
            "Player ID": bid['player_id'],
            "Min Bid": f"{bid['min_bid']:.1f}M",
            "Fair Value": f"{bid['fair_value']:.1f}M", 
            "Max Bid": f"{bid['max_bid']:.1f}M",
            "Risk Level": bid['risk_level'],
            "Market Pressure": f"{bid['market_pressure']:.1%}"
        })
    
    if bid_data:
        df = pd.DataFrame(bid_data)
        st.dataframe(df, use_container_width=True)


def create_value_chart(market_analysis):
    """Create value ratio chart for market analysis."""
    if not market_analysis or not market_analysis.get('best_buys'):
        return None
    
    players = market_analysis['best_buys'][:10]  # Top 10
    
    player_ids = [p['player_id'] for p in players]
    value_ratios = [p['value_ratio'] for p in players]
    expected_points = [p['expected_points_next_3'] for p in players]
    
    fig = px.scatter(
        x=value_ratios,
        y=expected_points,
        text=player_ids,
        title="Player Value Analysis (Top Targets)",
        labels={
            'x': 'Value Ratio (Points per Million)',
            'y': 'Expected Points (Next 3 GW)'
        }
    )
    
    fig.update_traces(textposition="top center")
    fig.update_layout(height=400)
    
    return fig


def create_risk_distribution_chart(team_analysis):
    """Create risk distribution chart for team."""
    if not team_analysis:
        return None
    
    all_players = team_analysis['players_to_keep'] + team_analysis['players_to_sell']
    risk_scores = [p['risk_score'] for p in all_players]
    
    fig = px.histogram(
        x=risk_scores,
        nbins=10,
        title="Team Risk Distribution",
        labels={'x': 'Risk Score', 'y': 'Number of Players'}
    )
    
    fig.update_layout(height=300)
    return fig


def main():
    """Main Streamlit application."""
    st.title("⚽ Fantasy LaLiga Decision Assistant")
    st.markdown("AI-powered analysis and recommendations for your Fantasy LaLiga team")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "Team Analysis", "Market Analysis", "Recommendations", "Demo"]
    )
    
    # Load sample data
    with st.spinner("Loading data..."):
        sample_data = load_sample_data()
    
    if not sample_data:
        st.error("Failed to load sample data. Make sure the API is running on localhost:8000")
        st.code("python -m fantasy_ai.src.api")
        return
    
    # Page routing
    if page == "Dashboard":
        show_dashboard(sample_data)
    elif page == "Team Analysis":
        show_team_analysis(sample_data)
    elif page == "Market Analysis":
        show_market_analysis(sample_data)
    elif page == "Recommendations":
        show_recommendations(sample_data)
    elif page == "Demo":
        show_demo()


def show_dashboard(sample_data):
    """Show main dashboard."""
    st.header("📊 Dashboard")
    
    if 'team' in sample_data:
        team = sample_data['team']
        
        # Team overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Team Value", f"{team['total_value']:.1f}M")
        
        with col2:
            st.metric("Bankroll", f"{team['bankroll']:.1f}M")
        
        with col3:
            st.metric("Players", len(team['players']))
        
        with col4:
            st.metric("Transfers Made", team['transfers_made'])
        
        # Quick team analysis
        with st.spinner("Analyzing team..."):
            team_analysis = make_api_request("/analysis/myteam", "POST", team)
        
        if team_analysis:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Players to Sell", 
                    len(team_analysis['players_to_sell']),
                    help="Players recommended for transfer out"
                )
            
            with col2:
                st.metric(
                    "Team Balance Score",
                    f"{team_analysis['team_balance_score']:.1%}",
                    help="Overall team balance assessment"
                )
            
            # Risk distribution chart
            risk_chart = create_risk_distribution_chart(team_analysis)
            if risk_chart:
                st.plotly_chart(risk_chart, use_container_width=True)


def show_team_analysis(sample_data):
    """Show detailed team analysis."""
    st.header("👥 Team Analysis")
    
    if 'team' not in sample_data:
        st.error("Team data not available")
        return
    
    team = sample_data['team']
    
    with st.spinner("Analyzing your team..."):
        team_analysis = make_api_request("/analysis/myteam", "POST", team)
    
    if not team_analysis:
        st.error("Failed to analyze team")
        return
    
    # Display results
    col1, col2 = st.columns(2)
    
    with col1:
        display_player_table(team_analysis['players_to_sell'], "🔴 Players to Sell")
    
    with col2:
        display_player_table(team_analysis['players_to_keep'], "🟢 Players to Keep")
    
    # Weak positions
    if team_analysis['weak_positions']:
        st.subheader("⚠️ Weak Positions")
        for position in team_analysis['weak_positions']:
            st.warning(f"Consider strengthening: {position}")
    
    # Team balance
    st.subheader("📊 Team Balance")
    st.progress(team_analysis['team_balance_score'])
    st.caption(f"Balance Score: {team_analysis['team_balance_score']:.1%}")


def show_market_analysis(sample_data):
    """Show market analysis."""
    st.header("🏪 Market Analysis")
    
    if 'market' not in sample_data:
        st.error("Market data not available")
        return
    
    market = sample_data['market']
    
    with st.spinner("Analyzing market..."):
        market_analysis = make_api_request("/analysis/market", "POST", market)
    
    if not market_analysis:
        st.error("Failed to analyze market")
        return
    
    # Market trends
    st.subheader("📈 Market Trends")
    trends = market_analysis['market_trends']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Value Ratio", f"{trends['avg_value_ratio']:.1f}")
    
    with col2:
        st.metric("Avg Risk Score", f"{trends['avg_risk_score']:.1f}")
    
    with col3:
        st.metric("High Value Players", trends['high_value_count'])
    
    with col4:
        st.metric("Bargains Found", trends['bargain_count'])
    
    # Player categories
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_player_table(market_analysis['best_buys'][:5], "🟢 Best Buys")
    
    with col2:
        display_player_table(market_analysis['bargains'][:5], "💎 Bargains")
    
    with col3:
        display_player_table(market_analysis['overpriced'][:5], "🔴 Overpriced")
    
    # Value chart
    value_chart = create_value_chart(market_analysis)
    if value_chart:
        st.plotly_chart(value_chart, use_container_width=True)


def show_recommendations(sample_data):
    """Show recommendations page."""
    st.header("🎯 Recommendations")
    
    if 'team' not in sample_data or 'market' not in sample_data:
        st.error("Team or market data not available")
        return
    
    team = sample_data['team']
    market = sample_data['market']
    rivals = sample_data.get('rivals', [])
    
    # Comprehensive analysis
    with st.spinner("Generating recommendations..."):
        recommendations = make_api_request(
            "/recommend/comprehensive", 
            "POST", 
            {
                "team_state": team,
                "market": market,
                "rivals": rivals
            }
        )
    
    if not recommendations:
        st.error("Failed to generate recommendations")
        return
    
    # Summary
    st.subheader("📋 Summary")
    st.info(recommendations['summary'])
    
    # Swap recommendations
    display_swap_recommendations(recommendations['swap_recommendations'])
    
    # Bidding recommendations
    display_bid_recommendations(recommendations['bid_recommendations'])
    
    # Differentials (if rivals available)
    if recommendations['differentials']:
        st.subheader("🎯 Differential Players")
        
        diff_data = []
        for diff in recommendations['differentials']:
            diff_data.append({
                "Player ID": diff['player_id'],
                "Ownership %": f"{diff['ownership_percentage']:.1f}%",
                "Differential Value": f"{diff['differential_value']:.1f}",
                "Risk/Reward": f"{diff['risk_reward_ratio']:.1f}"
            })
        
        if diff_data:
            df = pd.DataFrame(diff_data)
            st.dataframe(df, use_container_width=True)


def show_demo():
    """Show demo page with quick analysis."""
    st.header("🚀 Quick Demo")
    st.markdown("See the system in action with sample data!")
    
    if st.button("Run Quick Analysis", type="primary"):
        with st.spinner("Running comprehensive analysis..."):
            demo_result = make_api_request("/demo/quick-analysis", "POST")
        
        if demo_result:
            st.success("Analysis complete!")
            
            # Show key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Swap Opportunities",
                    len(demo_result['swap_recommendations'])
                )
            
            with col2:
                st.metric(
                    "Market Targets", 
                    len(demo_result['bid_recommendations'])
                )
            
            with col3:
                st.metric(
                    "Differentials",
                    len(demo_result['differentials'])
                )
            
            # Summary
            st.subheader("🎯 AI Recommendations")
            st.info(demo_result['summary'])
            
            # Quick insights
            if demo_result['swap_recommendations']:
                best_swap = demo_result['swap_recommendations'][0]
                st.success(
                    f"💡 Best Swap: Sell Player #{best_swap['sell_player_id']} → "
                    f"Buy Player #{best_swap['buy_player_id']} "
                    f"(+{best_swap['expected_points_gain']:.1f} points)"
                )
            
        else:
            st.error("Demo analysis failed")
    
    # API Documentation
    st.subheader("📚 API Endpoints")
    st.markdown("""
    **Available endpoints:**
    - `GET /sample/team` - Get sample team data
    - `POST /analysis/myteam` - Analyze team  
    - `POST /analysis/market` - Analyze market
    - `POST /recommend/swaps` - Get swap recommendations
    - `POST /recommend/bids` - Get bidding strategy
    - `POST /league/differentials` - Find differential players
    - `POST /recommend/comprehensive` - Complete analysis
    """)


if __name__ == "__main__":
    main()