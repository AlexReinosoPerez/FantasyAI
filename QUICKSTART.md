# 🚀 Quick Start Guide

## Running the Fantasy LaLiga Decision Assistant

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
uvicorn fantasy_ai.src.api:app --host 0.0.0.0 --port 8000
```

### 3. Run the Demo
```bash
python demo.py
```

### 4. Start the Web UI (Optional)
```bash
streamlit run streamlit_app.py
```

### 5. Test the API
```bash
python test_api.py
```

## API Documentation
Visit http://localhost:8000/docs for interactive API documentation.

## Sample API Calls

### Get Sample Data
```bash
curl http://localhost:8000/sample/players
curl http://localhost:8000/sample/team
```

### Run Quick Analysis
```bash
curl -X POST http://localhost:8000/demo/quick-analysis
```

### Analyze Your Team
```bash
curl -X POST http://localhost:8000/analysis/myteam \
  -H "Content-Type: application/json" \
  -d @fantasy_ai/data/sample_team.json
```

## Key Features Demonstrated

✅ **Team Analysis**: Identifies players to keep vs sell based on expected points, form, and value  
✅ **Market Analysis**: Finds best buys with high value ratios (points per million)  
✅ **Smart Bidding**: Calculates fair value and optimal bid ranges using Kelly criterion  
✅ **Risk Assessment**: Evaluates injury, suspension, and performance consistency risks  
✅ **AI Recommendations**: Provides clear, actionable advice with confidence scores  

## Sample Results

The demo shows analysis of Real Madrid and Barcelona players:
- **Best Target**: Jude Bellingham (3.6 points per million value ratio)
- **Low Risk Players**: All sample players show low risk scores (0.02-0.10)
- **Fair Value**: System calculates precise fair market values
- **Market Efficiency**: Accounts for market pricing inefficiencies

## Architecture Highlights

- **Modular Design**: Separate modules for features, forecasting, economics
- **Type Safety**: Full Pydantic validation
- **Production Ready**: Error handling, logging, CORS support
- **Extensible**: Easy to add new analysis methods