# FantasyAI

**Asistente inteligente para Fantasy LaLiga con predicciones y recomendaciones**

## 🎯 Características

### 📊 Análisis Predictivo
- **EMA (Media Móvil Exponencial)**: Calcula tendencias de rendimiento de jugadores
- **Análisis de Fixtures**: Ajusta predicciones según dificultad de partidos
- **Probabilidad de Titularidad**: Evalúa la probabilidad de que un jugador sea titular
- **Scoring de Confianza**: Mide la confianza en las predicciones

### 💰 Análisis de Valor y Riesgo
- **Cálculo de Valor Intrínseco**: Evaluación del valor real de jugadores
- **Análisis de Riesgo Detallado**: Múltiples factores de riesgo evaluados
- **Recomendaciones de Puja**: Pujas máximas calculadas por tolerancia al riesgo
- **Comparación de Jugadores**: Rankings por valor ajustado por riesgo

### 🔄 Recomendaciones Inteligentes
- **Intercambios Sugeridos**: Identificación de mejoras al equipo
- **Oportunidades de Mercado**: Detección de jugadores infravalorados
- **Análisis de Diferenciales**: Jugadores con baja propiedad pero alto potencial

### 🏆 Análisis de Liga
- **Comparación con Rivales**: Posicionamiento en la liga
- **Estrategias por Ranking**: Consejos según posición en liga
- **Diferenciales Premium**: Jugadores clave para ganar ventaja

## 🚀 Instalación y Uso

### Requisitos
```bash
pip install -r requirements.txt
```

### Ejecutar API (FastAPI)
```bash
python main.py
```
La API estará disponible en `http://localhost:8000`

### Ejecutar Frontend (Streamlit)
```bash
streamlit run streamlit_app.py
```
La interfaz estará disponible en `http://localhost:8501`

### Probar Funcionalidad Core
```bash
python test_core.py
```

## 📁 Estructura del Proyecto

```
FantasyAI/
├── main.py                 # Aplicación FastAPI principal
├── streamlit_app.py        # Interfaz de usuario Streamlit
├── requirements.txt        # Dependencias Python
├── test_core.py           # Tests de funcionalidad
├── core/                  # Lógica de negocio principal
│   ├── models.py          # Modelos de datos (Pydantic)
│   ├── prediction_engine.py  # Motor de predicciones
│   └── value_calculator.py   # Calculadora de valor/riesgo
├── api/                   # Endpoints de la API
│   └── routers/
│       ├── analysis.py    # Análisis de equipo y mercado
│       ├── recommend.py   # Recomendaciones
│       └── league.py      # Análisis de liga
└── data/                  # Datos de ejemplo
    ├── sample_team.json   # Equipo de ejemplo
    └── sample_market.json # Datos de mercado
```

## 🔧 API Endpoints

### Análisis
- `POST /analysis/myteam` - Analiza tu equipo actual
- `GET /analysis/market` - Analiza oportunidades de mercado

### Recomendaciones  
- `POST /recommend/swaps` - Recomendaciones de intercambios
- `POST /recommend/bids` - Recomendaciones de pujas

### Liga
- `POST /league/differentials` - Análisis de jugadores diferenciales
- `GET /league/stats/{league_id}` - Estadísticas de liga

## 🧮 Algoritmos Clave

### Predicción de Puntos
1. **EMA**: `EMA = α × current_points + (1-α) × previous_EMA`
2. **Ajuste por Fixture**: `adjusted_points = ema_points × difficulty_multiplier`
3. **Ajuste por Titularidad**: `final_points = adjusted_points × starter_probability`

### Cálculo de Valor
- **Eficiencia**: `predicted_points / price`
- **Factor de Propiedad**: `1 - (ownership / 100)`
- **Factor de Forma**: Basado en consistencia reciente
- **Valor Final**: `efficiency × ownership_factor × form_factor × consistency_factor`

### Evaluación de Riesgo
- **Volatilidad de Precio**: Cambios recientes de precio
- **Consistencia de Forma**: Varianza en rendimiento
- **Riesgo de Lesión**: Basado en estado del jugador
- **Riesgo de Rotación**: Probabilidad de no ser titular
- **Dificultad de Fixtures**: Calendarios próximos

## 🎮 Funcionalidades del Frontend

### Dashboard Principal
- Resumen de tu equipo
- Métricas clave de rendimiento
- Enlaces rápidos a análisis

### Análisis de Equipo
- Predicciones individuales por jugador
- Análisis por posición
- Identificación de problemas
- Recomendaciones de mejora

### Análisis de Mercado
- Filtros por posición, precio, propiedad
- Top oportunidades de valor
- Estrellas emergentes
- Diferenciales potenciales

### Sistema de Recomendaciones
- **Intercambios**: Análisis entrada vs salida con justificación
- **Pujas**: Pujas máximas con análisis riesgo/recompensa
- **Tolerancia al Riesgo**: Ajustes por perfil conservador/agresivo

### Análisis de Liga
- Comparación con competidores
- Estrategias según ranking
- Diferenciales por categoría (premium, valor, presupuesto)

## 🔬 Testing

El proyecto incluye tests comprehensivos que validan:
- ✅ Cálculos EMA correctos
- ✅ Ajustes por dificultad de fixtures
- ✅ Evaluaciones de probabilidad de titularidad
- ✅ Métricas de valor y riesgo
- ✅ Comparaciones entre jugadores
- ✅ Funcionalidad sin dependencias externas

## 🏗️ Arquitectura

### Modular y Extensible
- **Separación de responsabilidades** entre predicción, valor y riesgo
- **APIs independientes** para diferentes tipos de análisis
- **Configuración flexible** de parámetros de algoritmos

### Escalable
- **Cacheo de predicciones** para optimizar rendimiento
- **Procesamiento asíncrono** para análisis complejos
- **Arquitectura de microservicios** preparada para crecimiento

### Mantenible
- **Código bien documentado** con explicaciones claras
- **Tests automatizados** para validación continua
- **Configuración por entorno** para desarrollo/producción

## 📈 Roadmap Futuro

- 🔮 **Machine Learning**: Modelos avanzados de predicción
- 📱 **App Móvil**: Interfaz nativa para iOS/Android  
- ⚡ **Tiempo Real**: Actualizaciones en vivo durante partidos
- 🤖 **Automatización**: Fichajes y ventas automáticas
- 📊 **Analytics Avanzados**: Dashboards de rendimiento detallados
- 🔗 **Integración Externa**: APIs de datos oficiales de LaLiga