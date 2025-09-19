#!/usr/bin/env python3
"""
Simple test script for Fantasy LaLiga Decision Assistant.
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:8000"

def test_api():
    """Test the API endpoints."""
    print("🧪 Testing Fantasy LaLiga Decision Assistant API...")
    
    # Test health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Root endpoint: {data['message']}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test sample data endpoints
    print("\n3. Testing sample data endpoints...")
    endpoints = [
        "/sample/players",
        "/sample/team", 
        "/sample/market",
        "/sample/rivals"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            response.raise_for_status()
            data = response.json()
            print(f"✅ {endpoint}: loaded {len(data) if isinstance(data, list) else 'OK'}")
        except Exception as e:
            print(f"❌ {endpoint} failed: {e}")
            return False
    
    # Test demo analysis
    print("\n4. Testing demo analysis...")
    try:
        response = requests.post(f"{API_BASE_URL}/demo/quick-analysis")
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Demo analysis completed:")
        print(f"   - Players to sell: {len(data['team_analysis']['players_to_sell'])}")
        print(f"   - Players to keep: {len(data['team_analysis']['players_to_keep'])}")
        print(f"   - Swap recommendations: {len(data['swap_recommendations'])}")
        print(f"   - Bid recommendations: {len(data['bid_recommendations'])}")
        print(f"   - Differentials found: {len(data['differentials'])}")
        print(f"   - Summary: {data['summary']}")
        
    except Exception as e:
        print(f"❌ Demo analysis failed: {e}")
        return False
    
    print("\n🎉 All tests passed! The API is working correctly.")
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)