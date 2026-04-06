#!/bin/bash

# DDGS API Startup Script

set -e

echo "🚀 Starting DDGS API..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -e ".[api]"
pip install -e .

# Run the API
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API documentation available at http://localhost:8000/docs"
echo "🔍 ReDoc documentation available at http://localhost:8000/redoc"

python -m uvicorn ddgs.api_server:fastapi_app --host 0.0.0.0 --port 8000
