#!/bin/bash
# AI Pulse — Quick Start
# Run this from the ai-pulse/ directory

echo "🚀 Starting AI Pulse..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install it from https://python.org"
    exit 1
fi

# Check .env
if [ ! -f backend/.env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp backend/.env.example backend/.env
    echo "👉 Open backend/.env and add your ANTHROPIC_API_KEY, then re-run this script."
    exit 1
fi

# Install deps
echo "📦 Installing dependencies..."
cd backend
pip install -r requirements.txt -q

# Start server
echo "✅ Starting server at http://localhost:8000"
echo "   Open your browser to http://localhost:8000"
echo ""
python app.py
