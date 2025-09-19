#!/bin/bash
# Fantasy LaLiga Assistant - Startup Script

echo "🚀 Fantasy LaLiga Assistant"
echo "=========================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python no encontrado. Por favor instala Python 3.8+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activando entorno virtual..."
source venv/bin/activate || source venv/Scripts/activate

# Install dependencies
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Start services
echo "🌟 Iniciando servicios..."
echo ""
echo "Opciones disponibles:"
echo "1. 🚀 Iniciar API (FastAPI)"  
echo "2. 🖥️  Iniciar Frontend (Streamlit)"
echo "3. 🧪 Ejecutar Tests"
echo "4. 📊 Ver documentación de API"
echo ""

read -p "Selecciona una opción (1-4): " choice

case $choice in
    1)
        echo "🚀 Iniciando API en http://localhost:8000"
        python main.py
        ;;
    2) 
        echo "🖥️ Iniciando Frontend en http://localhost:8501"
        streamlit run streamlit_app.py
        ;;
    3)
        echo "🧪 Ejecutando tests..."
        python test_core.py
        ;;
    4)
        echo "📊 Iniciando servidor de documentación..."
        echo "La documentación estará disponible en:"
        echo "• Swagger UI: http://localhost:8000/docs"
        echo "• ReDoc: http://localhost:8000/redoc"
        python main.py
        ;;
    *)
        echo "❌ Opción no válida"
        exit 1
        ;;
esac