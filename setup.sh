#!/bin/bash

# Healthcare Triage Backend Setup Script

echo "🏥 Healthcare Triage Backend Setup"
echo "=================================="

# Check Python version
echo "📋 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.11+"; exit 1; }

# Create virtual environment
echo "🐍 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if Ollama is installed
echo "🤖 Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    
    # Check if Llama 3 model is available
    if ollama list | grep -q "llama3:8b"; then
        echo "✅ Llama 3 8B model is available"
    else
        echo "📥 Downloading Llama 3 8B model..."
        ollama pull llama3:8b
    fi
else
    echo "⚠️  Ollama not found. Installing..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "📥 Downloading Llama 3 8B model..."
    ollama pull llama3:8b
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from app.database.database import DatabaseManager; DatabaseManager()"

# Run quick test
echo "🧪 Running quick tests..."
python3 quick_test.py

echo ""
echo "🎉 Setup completed!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "To test the API:"
echo "  python3 test_validation.py"
echo ""
echo "API Documentation will be available at:"
echo "  http://localhost:8000/docs"
