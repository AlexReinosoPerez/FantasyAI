"""
Fantasy LaLiga Assistant - Main FastAPI Application
Asistente para Fantasy LaLiga con predicciones y recomendaciones inteligentes
"""

# Basic HTTP server for testing without external dependencies
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import threading
import time

# Placeholder for when FastAPI is available
class MockFastAPI:
    def __init__(self, title=None, description=None, version=None):
        self.routes = []
        self.title = title
        self.description = description
        self.version = version
    
    def add_middleware(self, middleware_class, **kwargs):
        pass
    
    def include_router(self, router, prefix="", tags=None):
        pass
    
    def get(self, path):
        def decorator(func):
            self.routes.append(("GET", path, func))
            return func
        return decorator

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from api.routers import analysis, recommend, league
    from core.models import Player, Team, MarketData
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not available. Using basic HTTP server for demonstration.")

app = MockFastAPI(
    title="Fantasy LaLiga Assistant",
    description="Asistente inteligente para Fantasy LaLiga con análisis predictivo y recomendaciones",
    version="1.0.0"
)

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Fantasy LaLiga Assistant",
        description="Asistente inteligente para Fantasy LaLiga con análisis predictivo y recomendaciones",
        version="1.0.0"
    )
    
    # Configure CORS for Streamlit integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501"],  # Streamlit default port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
    app.include_router(recommend.router, prefix="/recommend", tags=["Recommendations"])
    app.include_router(league.router, prefix="/league", tags=["League"])

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Fantasy LaLiga Assistant API",
        "version": "1.0.0",
        "endpoints": [
            "/analysis/myteam - Análisis de tu equipo",
            "/analysis/market - Análisis del mercado", 
            "/recommend/swaps - Recomendaciones de intercambios",
            "/recommend/bids - Recomendaciones de pujas",
            "/league/differentials - Análisis de diferenciales de liga"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Fantasy LaLiga Assistant"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)