#!/bin/bash

# RFP AI Streamlit Application Launcher
# This script launches the Streamlit web interface for the RFP AI system

echo "🚀 Starting RFP AI - Multi-Agent System Web Interface"
echo "============================================================"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing requirements..."
    pip install -r requirements.txt
fi

# Launch Streamlit app
echo "🌐 Launching web interface..."
echo "📍 The application will open in your browser at: http://localhost:8501"
echo ""
echo "🎛️ Available features:"
echo "   • 📊 Interactive Dashboard"
echo "   • 📋 RFP Analysis & Selection"
echo "   • 🔧 Technical Specification Matching"
echo "   • 💰 Pricing & Cost Analysis" 
echo "   • 📊 Data Explorer"
echo "   • ⚙️ System Configuration"
echo ""
echo "Press Ctrl+C to stop the application"
echo "============================================================"

# Start Streamlit
streamlit run streamlit_app.py --server.port=8501 --server.address=localhost