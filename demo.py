#!/usr/bin/env python3
"""
Demo script to showcase Fantasy LaLiga Decision Assistant functionality.
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:8000"

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🏆 {title}")
    print(f"{'='*60}")

def print_players_table(players, title):
    """Print players in a formatted table."""
    if not players:
        print(f"No {title.lower()} found.")
        return
    
    print(f"\n{title}:")
    print("-" * 80)
    print(f"{'ID':<4} {'Expected Pts':<12} {'Form':<6} {'Value Ratio':<12} {'Risk':<6} {'Fair Value':<10}")
    print("-" * 80)
    
    for player in players[:5]:  # Show top 5
        print(f"{player['player_id']:<4} "
              f"{player['expected_points_next_3']:<12.1f} "
              f"{player['form_score']:<6.1f} "
              f"{player['value_ratio']:<12.1f} "
              f"{player['risk_score']:<6.2f} "
              f"{player['fair_value']:<10.1f}M")

def demo_comprehensive_analysis():
    """Run comprehensive analysis demo."""
    print_header("Fantasy LaLiga Decision Assistant Demo")
    
    print("🚀 Running comprehensive analysis with sample data...")
    
    try:
        response = requests.post(f"{API_BASE_URL}/demo/quick-analysis")
        response.raise_for_status()
        data = response.json()
        
        # Team Analysis
        print_header("Team Analysis Results")
        team_analysis = data['team_analysis']
        
        print(f"📊 Team Balance Score: {team_analysis['team_balance_score']:.1%}")
        print(f"🔴 Players to sell: {len(team_analysis['players_to_sell'])}")
        print(f"🟢 Players to keep: {len(team_analysis['players_to_keep'])}")
        
        if team_analysis['weak_positions']:
            print(f"⚠️  Weak positions: {', '.join(team_analysis['weak_positions'])}")
        
        print_players_table(team_analysis['players_to_keep'], "Top Players to Keep")
        
        # Market Analysis
        print_header("Market Analysis Results")
        market_analysis = data['market_analysis']
        
        trends = market_analysis['market_trends']
        print(f"📈 Market Trends:")
        print(f"   - Average Value Ratio: {trends['avg_value_ratio']:.1f}")
        print(f"   - Average Risk Score: {trends['avg_risk_score']:.1f}")
        print(f"   - High Value Players: {trends['high_value_count']}")
        print(f"   - Bargains Found: {trends['bargain_count']}")
        
        print_players_table(market_analysis['best_buys'], "🎯 Best Buy Targets")
        print_players_table(market_analysis['bargains'], "💎 Market Bargains")
        
        # Recommendations
        print_header("AI Recommendations")
        print(f"💡 Summary: {data['summary']}")
        
        # Swap Recommendations
        swaps = data['swap_recommendations']
        if swaps:
            print(f"\n🔄 Top Swap Recommendations:")
            print("-" * 70)
            print(f"{'Sell':<6} {'Buy':<6} {'Points Gain':<12} {'Cost':<8} {'Confidence':<10}")
            print("-" * 70)
            
            for swap in swaps[:3]:  # Top 3 swaps
                print(f"{swap['sell_player_id']:<6} "
                      f"{swap['buy_player_id']:<6} "
                      f"{swap['expected_points_gain']:<12.1f} "
                      f"{swap['cost_difference']:<8.1f}M "
                      f"{swap['confidence']:<10.1%}")
        
        # Bidding Strategy
        bids = data['bid_recommendations']
        if bids:
            print(f"\n💰 Bidding Strategy (Top Targets):")
            print("-" * 70)
            print(f"{'Player':<8} {'Min Bid':<8} {'Fair Value':<11} {'Max Bid':<8} {'Risk':<8}")
            print("-" * 70)
            
            for bid in bids[:5]:  # Top 5 targets
                print(f"{bid['player_id']:<8} "
                      f"{bid['min_bid']:<8.1f}M "
                      f"{bid['fair_value']:<11.1f}M "
                      f"{bid['max_bid']:<8.1f}M "
                      f"{bid['risk_level']:<8}")
        
        # Performance Summary
        print_header("Analysis Performance")
        print("✅ Successfully analyzed:")
        print(f"   - {len(team_analysis['players_to_keep']) + len(team_analysis['players_to_sell'])} team players")
        print(f"   - {len(market_analysis['best_buys']) + len(market_analysis['bargains'])} market opportunities")
        print(f"   - {len(swaps)} swap recommendations")
        print(f"   - {len(bids)} bidding strategies")
        
        print(f"\n🎯 Key Insight: {data['summary']}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        print("Make sure the API server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

def demo_individual_endpoints():
    """Test individual endpoints."""
    print_header("Individual Endpoint Tests")
    
    # Test sample data endpoints
    endpoints = {
        "Players Data": "/sample/players",
        "Team Data": "/sample/team",
        "Market Data": "/sample/market",
        "Rivals Data": "/sample/rivals"
    }
    
    for name, endpoint in endpoints.items():
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                print(f"✅ {name}: {len(data)} items loaded")
            elif isinstance(data, dict) and 'players' in data:
                print(f"✅ {name}: {len(data['players'])} players loaded")
            else:
                print(f"✅ {name}: Data loaded successfully")
                
        except Exception as e:
            print(f"❌ {name}: Failed - {e}")

def main():
    """Main demo function."""
    print("🏆 Fantasy LaLiga Decision Assistant")
    print("🤖 AI-powered analysis for Fantasy LaLiga teams")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    
    # Test basic connectivity
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        print("✅ API server is running")
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("Please start the API server first:")
        print("uvicorn fantasy_ai.src.api:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Run demos
    demo_individual_endpoints()
    
    if demo_comprehensive_analysis():
        print_header("Demo Complete")
        print("🎉 All systems working correctly!")
        print("\nNext steps:")
        print("1. Start Streamlit UI: streamlit run streamlit_app.py")
        print("2. Visit http://localhost:8501 for the web interface")
        print("3. Check API docs at http://localhost:8000/docs")
    else:
        print("❌ Demo failed - check the logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()