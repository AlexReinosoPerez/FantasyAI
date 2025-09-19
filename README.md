# FantasyAI - Fantasy LaLiga Decision Assistant

🤖 AI-powered decision assistant for Fantasy LaLiga that analyzes your team, the market, and rivals to provide actionable recommendations.

## 🎯 Features

- **Team Analysis**: Identifies players to sell vs keep based on form, fixtures, and value
- **Market Analysis**: Finds best buys, bargains, and overpriced players
- **Smart Recommendations**: Suggests optimal player swaps and bidding strategies
- **Differential Analysis**: Finds good players that your rivals don't have
- **Risk Assessment**: Evaluates injury, suspension, and performance risks
- **Fair Value Calculation**: Estimates player prices based on expected points

## 🏗️ Architecture

```
fantasy_ai/
├── data/                    # Sample JSON data files
├── src/
│   ├── schemas.py          # Pydantic data models
│   ├── features.py         # Feature engineering (form, fixtures, risk)
│   ├── forecast.py         # Expected points prediction
│   ├── economics.py        # Fair value & bidding strategy
│   ├── recommend.py        # Recommendation engine
│   ├── loaders.py          # JSON data loaders
│   └── api.py              # FastAPI endpoints
├── streamlit_app.py        # Streamlit dashboard
├── test_api.py             # API tests
└── requirements.txt        # Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
uvicorn fantasy_ai.src.api:app --host 0.0.0.0 --port 8000
```

### 3. Test the API

```bash
python test_api.py
```

### 4. Access the Dashboard

```bash
streamlit run streamlit_app.py
```

Visit: http://localhost:8501

## 📡 API Endpoints

### Core Analysis
- `POST /analysis/myteam` - Analyze your team
- `POST /analysis/market` - Analyze market opportunities  
- `POST /recommend/swaps` - Get player swap recommendations
- `POST /recommend/bids` - Get bidding strategies
- `POST /league/differentials` - Find differential players
- `POST /recommend/comprehensive` - Complete analysis

### Sample Data
- `GET /sample/players` - Sample player data
- `GET /sample/team` - Sample team data
- `GET /sample/market` - Sample market data
- `GET /sample/rivals` - Sample rival teams

### Demo
- `POST /demo/quick-analysis` - Quick demo with sample data

## 📊 Example Usage

### Quick Demo
```bash
curl -X POST http://localhost:8000/demo/quick-analysis
```

### Analyze Your Team
```python
import requests

team_data = {
    "players": [...],  # Your player data
    "bankroll": 5.5,
    "total_value": 85.0
}

response = requests.post(
    "http://localhost:8000/analysis/myteam", 
    json=team_data
)

analysis = response.json()
print(f"Players to sell: {len(analysis['players_to_sell'])}")
```

## 🧠 AI Analysis Features

### Form Analysis
- Exponential Moving Average of recent performances
- Momentum detection (trending up/down)
- Consistency scoring

### Fixture Difficulty  
- LaLiga team strength ratings (1-5 scale)
- Position-specific fixture impact
- Multi-gameweek difficulty averaging

### Risk Assessment
- Injury/suspension probability
- Playing time consistency
- Price volatility
- Form variance

### Economic Modeling
- Fair value calculation using discounted expected points
- Kelly criterion for optimal bid sizing
- Value over replacement player (VORP)
- Market timing analysis

## 📈 Machine Learning

The system uses several ML techniques:

- **Expected Points Prediction**: Combines historical performance, form, fixtures, and availability
- **Risk Modeling**: Multi-factor risk assessment with weighted components
- **Value Optimization**: Fair value calculation with market efficiency adjustments
- **Portfolio Theory**: Kelly criterion for bankroll management

## 🔧 Configuration

### Fixture Difficulty Ratings
Edit `fantasy_ai/src/features.py` to customize team strength ratings:

```python
FDR_TABLE = {
    "Real Madrid": 5,
    "Barcelona": 5, 
    "Atletico Madrid": 4,
    # ... customize ratings
}
```

### Economic Parameters
Adjust in `fantasy_ai/src/economics.py`:

```python
POINTS_TO_MONEY_RATIO = 0.5  # Points to price conversion
MARKET_EFFICIENCY = 0.8      # Market efficiency (0-1)
RISK_FREE_RATE = 0.02       # Discount rate
```

## 📁 Data Format

The system expects JSON data in this format:

### Player Data
```json
{
  "id": 1,
  "name": "Player Name",
  "team": "Team Name", 
  "position": "Delantero",
  "price": 8.5,
  "total_points": 120,
  "recent_points": [8, 12, 6, 15, 4],
  "status": "available",
  "minutes": 1080,
  "games_played": 12,
  "next_fixtures": ["Real Madrid", "Barcelona"]
}
```

### Team Data
```json
{
  "players": [...],
  "bankroll": 5.5,
  "total_value": 85.0,
  "transfers_made": 1
}
```

## 🧪 Testing

Run the test suite:
```bash
python test_api.py
```

## 🛠️ Development

### Adding New Features

1. **New Analysis**: Add functions to `features.py`
2. **New Predictions**: Extend `forecast.py`
3. **New Economics**: Add to `economics.py`  
4. **New Endpoints**: Add to `api.py`
5. **New UI**: Extend `streamlit_app.py`

### Code Structure

The system is designed to be modular:
- **Features**: Stateless functions for player analysis
- **Economics**: Pure functions for financial calculations
- **Recommendations**: Combines features + economics
- **API**: Thin layer exposing functionality
- **UI**: Consumes API for user interaction

## 📋 TODO / Roadmap

- [ ] Add historical data analysis
- [ ] Implement player clustering
- [ ] Add transfer market trend analysis
- [ ] Create mobile-friendly UI
- [ ] Add email/push notifications
- [ ] Integrate with official Fantasy API
- [ ] Add advanced ML models (neural networks)
- [ ] Create Docker deployment
- [ ] Add user authentication
- [ ] Implement caching layer

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

This tool is for educational and personal use only. Fantasy football decisions involve risk. Past performance does not guarantee future results. Always verify data from official sources.