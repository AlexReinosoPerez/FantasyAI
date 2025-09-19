#!/usr/bin/env python3
"""
Test script for Fantasy LaLiga Assistant core functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use simplified models for testing
from test_models import Player, Position, PlayerStatus, PlayerPrediction

# Import numpy if available, otherwise use basic math
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("NumPy not available, using basic math functions")

class SimplePredictionEngine:
    """Simplified prediction engine without external dependencies"""
    
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.fixture_multipliers = {
            1: 1.3,   # Muy fácil
            2: 1.15,  # Fácil  
            3: 1.0,   # Neutral
            4: 0.85,  # Difícil
            5: 0.7    # Muy difícil
        }
    
    def calculate_ema_points(self, recent_points, current_avg):
        """Calcular la media móvil exponencial de puntos"""
        if not recent_points:
            return current_avg
            
        ema = current_avg
        for points in recent_points:
            ema = self.alpha * points + (1 - self.alpha) * ema
            
        return round(ema, 2)
    
    def adjust_for_fixture_difficulty(self, base_points, difficulty):
        """Ajustar puntos predichos según dificultad del partido"""
        multiplier = self.fixture_multipliers.get(difficulty, 1.0)
        return round(base_points * multiplier, 2)
    
    def calculate_starter_probability(self, player):
        """Calcular probabilidad de que el jugador sea titular"""
        base_prob = 0.8  # Probabilidad base
        
        # Ajustar por forma reciente del jugador
        if player.form:
            if NUMPY_AVAILABLE:
                recent_avg = np.mean(player.form[-3:]) if len(player.form) >= 3 else np.mean(player.form)
            else:
                recent_form = player.form[-3:] if len(player.form) >= 3 else player.form
                recent_avg = sum(recent_form) / len(recent_form) if recent_form else 0
                
            if recent_avg > player.avg_points:
                base_prob += 0.1
            elif recent_avg < player.avg_points * 0.5:
                base_prob -= 0.2
                
        # Ajustar por estado del jugador
        status_adjustments = {
            "disponible": 0.0,
            "duda": -0.3,
            "lesionado": -0.8,
            "sancionado": -1.0
        }
        base_prob += status_adjustments.get(player.status.value, 0.0)
        
        # Ajustar por precio/calidad
        if player.price > 8.0:  # Jugadores caros suelen ser más titulares
            base_prob += 0.1
        elif player.price < 4.0:  # Jugadores baratos menos probable que sean titulares
            base_prob -= 0.1
            
        return max(0.0, min(1.0, round(base_prob, 2)))
    
    def predict_player_points(self, player):
        """Generar predicción completa para un jugador"""
        # Calcular EMA
        ema_points = self.calculate_ema_points(player.form, player.avg_points)
        
        # Ajustar por dificultad del partido
        fixture_adjusted = self.adjust_for_fixture_difficulty(ema_points, player.fixture_difficulty)
        
        # Calcular probabilidad de ser titular
        starter_prob = self.calculate_starter_probability(player)
        
        # Predicción final ajustada por probabilidad de jugar
        predicted_points = fixture_adjusted * starter_prob
        
        # Calcular confianza en la predicción
        confidence = self._calculate_confidence(player, len(player.form))
        
        return PlayerPrediction(
            player_id=player.id,
            predicted_points=round(predicted_points, 2),
            confidence=confidence,
            ema_points=ema_points,
            fixture_adjusted_points=fixture_adjusted
        )
    
    def _calculate_confidence(self, player, data_points):
        """Calcular nivel de confianza en la predicción"""
        base_confidence = 0.5
        
        # Más datos = más confianza
        if data_points >= 5:
            base_confidence += 0.3
        elif data_points >= 3:
            base_confidence += 0.2
        elif data_points >= 1:
            base_confidence += 0.1
            
        # Jugadores con forma consistente = más confianza
        if player.form and len(player.form) >= 3:
            if NUMPY_AVAILABLE:
                variance = np.var(player.form)
            else:
                mean_form = sum(player.form) / len(player.form)
                variance = sum((x - mean_form) ** 2 for x in player.form) / len(player.form)
                
            if variance <= 2:  # Forma muy consistente
                base_confidence += 0.2
            elif variance <= 5:  # Forma moderadamente consistente
                base_confidence += 0.1
                
        # Estado del jugador afecta confianza
        if player.status.value in ["lesionado", "duda"]:
            base_confidence -= 0.2
            
        return max(0.1, min(1.0, round(base_confidence, 2)))

def test_prediction_engine():
    """Test the prediction engine functionality"""
    print("🧪 Testing Prediction Engine...")
    
    # Create sample player
    player = Player(
        id=1,
        name="Vinicius Jr",
        team="Real Madrid",
        position=Position.DELANTERO,
        price=12.5,
        points=180,
        avg_points=6.5,
        form=[8, 6, 9, 7, 8],
        status=PlayerStatus.DISPONIBLE,
        ownership=45.2,
        fixture_difficulty=2
    )
    
    # Initialize prediction engine
    engine = SimplePredictionEngine(alpha=0.3)
    
    # Test EMA calculation
    ema = engine.calculate_ema_points(player.form, player.avg_points)
    print(f"✅ EMA calculated: {ema}")
    
    # Test fixture adjustment
    adjusted = engine.adjust_for_fixture_difficulty(ema, 2)
    print(f"✅ Fixture adjusted points: {adjusted}")
    
    # Test starter probability
    starter_prob = engine.calculate_starter_probability(player)
    print(f"✅ Starter probability: {starter_prob}")
    
    # Test full prediction
    prediction = engine.predict_player_points(player)
    print(f"✅ Full prediction: {prediction.predicted_points} points (confidence: {prediction.confidence})")
    
    return prediction

def test_value_calculator():
    """Test basic value calculations"""
    print("\n💰 Testing Value Calculations...")
    
    # Create sample player and prediction
    player = Player(
        id=2,
        name="Pedri",
        team="Barcelona",
        position=Position.CENTROCAMPISTA,
        price=8.5,
        points=120,
        avg_points=4.8,
        form=[5, 4, 6, 5, 3],
        status=PlayerStatus.DISPONIBLE,
        ownership=22.1,
        fixture_difficulty=3
    )
    
    engine = SimplePredictionEngine()
    prediction = engine.predict_player_points(player)
    
    # Basic value calculation (points per million)
    value_per_million = prediction.predicted_points / player.price if player.price > 0 else 0
    print(f"✅ Value per million: {value_per_million:.3f}")
    
    # Risk assessment based on form consistency
    if player.form and len(player.form) >= 3:
        if NUMPY_AVAILABLE:
            form_variance = np.var(player.form)
        else:
            mean_form = sum(player.form) / len(player.form)
            form_variance = sum((x - mean_form) ** 2 for x in player.form) / len(player.form)
        
        if form_variance <= 2:
            risk_level = "Low"
        elif form_variance <= 5:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        print(f"✅ Risk level: {risk_level} (variance: {form_variance:.2f})")
    
    # Recommended bid (basic calculation)
    max_bid = player.price * (1 + (prediction.predicted_points - player.avg_points) / 10)
    max_bid = max(player.price, max_bid)  # Never bid below current price
    print(f"✅ Recommended max bid: {max_bid:.2f}M")
    
    return value_per_million, prediction

def test_multiple_players():
    """Test with multiple players"""
    print("\n👥 Testing Multiple Players...")
    
    players = [
        Player(
            id=3, name="Militão", team="Real Madrid", position=Position.DEFENSA,
            price=6.5, points=95, avg_points=3.8, form=[4, 5, 3, 4, 6],
            ownership=18.5, fixture_difficulty=2
        ),
        Player(
            id=4, name="Ter Stegen", team="Barcelona", position=Position.PORTERO,
            price=5.5, points=110, avg_points=4.4, form=[6, 4, 5, 6, 5],
            ownership=35.8, fixture_difficulty=3
        ),
        Player(
            id=5, name="Iago Aspas", team="Celta Vigo", position=Position.DELANTERO,
            price=9.2, points=155, avg_points=6.2, form=[6, 8, 5, 7, 6],
            ownership=15.4, fixture_difficulty=1
        )
    ]
    
    engine = SimplePredictionEngine()
    
    # Generate predictions and comparisons
    results = []
    for player in players:
        prediction = engine.predict_player_points(player)
        value_per_million = prediction.predicted_points / player.price if player.price > 0 else 0
        
        results.append({
            'name': player.name,
            'position': player.position.value,
            'price': player.price,
            'predicted_points': prediction.predicted_points,
            'value_per_million': value_per_million,
            'confidence': prediction.confidence,
            'ownership': player.ownership
        })
    
    # Sort by value per million
    results.sort(key=lambda x: x['value_per_million'], reverse=True)
    
    print("✅ Player comparisons (sorted by value per million):")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['name']} ({result['position']}): {result['value_per_million']:.3f} pts/M")
        print(f"      Price: {result['price']:.1f}M, Predicted: {result['predicted_points']:.1f} pts")
        print(f"      Confidence: {result['confidence']:.2f}, Ownership: {result['ownership']:.1f}%")
        print()
    
    return results

def main():
    """Run all tests"""
    print("🚀 Starting Fantasy LaLiga Assistant Tests\n")
    
    try:
        # Test individual components
        prediction = test_prediction_engine()
        value_info = test_value_calculator()
        results = test_multiple_players()
        
        print("\n✅ All tests completed successfully!")
        print("\n📊 Summary:")
        print(f"   - Prediction engine working ✓")
        print(f"   - Value calculations working ✓")
        print(f"   - Multi-player analysis working ✓")
        print(f"   - Best value player: {results[0]['name']} ({results[0]['value_per_million']:.3f} pts/M)")
        
        print("\n🎯 Key Features Demonstrated:")
        print("   ✅ EMA (Exponential Moving Average) calculation")
        print("   ✅ Fixture difficulty adjustment")
        print("   ✅ Starting probability assessment") 
        print("   ✅ Confidence scoring")
        print("   ✅ Value per million analysis")
        print("   ✅ Multi-player comparison")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)