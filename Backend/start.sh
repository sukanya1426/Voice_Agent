#!/bin/bash

# Sigmoix AI Voice Agent Setup and Start Script
# This script sets up and starts the complete voice agent system

echo "🚀 Starting Sigmoix AI Voice Agent System"
echo "========================================"

# Check if we're in the Backend directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the Backend directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with required API keys"
    exit 1
fi

# Check for required environment variables
echo "🔍 Checking environment variables..."

check_env_var() {
    local var_name=$1
    local var_value=$(grep "^$var_name=" .env | cut -d'=' -f2 | tr -d '"')
    
    if [ -z "$var_value" ]; then
        echo "❌ Missing $var_name in .env file"
        return 1
    else
        echo "✅ $var_name is set"
        return 0
    fi
}

# Check all required variables
missing_vars=0

check_env_var "DEEPGRAM_API_KEY" || missing_vars=$((missing_vars + 1))
check_env_var "CARTESIA_API_KEY" || missing_vars=$((missing_vars + 1))
check_env_var "TWILIO_ACCOUNT_SID" || missing_vars=$((missing_vars + 1))
check_env_var "TWILIO_AUTH_TOKEN" || missing_vars=$((missing_vars + 1))
check_env_var "PIPECAT_PROXY_HOST" || missing_vars=$((missing_vars + 1))

# Check for at least one LLM API key
llm_keys=0
check_env_var "CEREBRAS_API_KEY" && llm_keys=$((llm_keys + 1))
check_env_var "OPENAI_API_KEY" && llm_keys=$((llm_keys + 1))

if [ $llm_keys -eq 0 ]; then
    echo "❌ At least one LLM API key is required (CEREBRAS_API_KEY or OPENAI_API_KEY)"
    missing_vars=$((missing_vars + 1))
fi

if [ $missing_vars -gt 0 ]; then
    echo "❌ Please fix the missing environment variables and try again"
    exit 1
fi

echo "✅ All required environment variables are set"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi

# Check if products CSV exists
if [ ! -f "products_merged.csv" ]; then
    echo "❌ products_merged.csv not found. Please ensure the product data file is in the Backend directory"
    exit 1
fi

echo "✅ Products data found"

# Create logs directory
mkdir -p logs

# Function to start services
start_services() {
    echo "🌟 Starting Sigmoix AI Voice Agent Services..."
    
    # Start API Server (Frontend + Backend API)
    echo "🔧 Starting API Server..."
    node api-server.js > logs/api-server.log 2>&1 &
    API_PID=$!
    
    sleep 2
    
    # Check if API server started successfully
    if ps -p $API_PID > /dev/null; then
        echo "✅ API Server started (PID: $API_PID)"
    else
        echo "❌ Failed to start API Server"
        exit 1
    fi
    
    # Start Twilio Webhook Server (Python)
    echo "🎙️ Starting Twilio Webhook Server..."
    if command -v python3 &> /dev/null; then
        python3 twilio_webhook_server.py > logs/webhook-server.log 2>&1 &
    else
        python twilio_webhook_server.py > logs/webhook-server.log 2>&1 &
    fi
    WEBHOOK_PID=$!
    
    sleep 3
    
    # Check if webhook server started successfully
    if ps -p $WEBHOOK_PID > /dev/null; then
        echo "✅ Webhook Server started (PID: $WEBHOOK_PID)"
    else
        echo "❌ Failed to start Webhook Server"
        kill $API_PID 2>/dev/null
        exit 1
    fi
    
    # Store PIDs for cleanup
    echo $API_PID > logs/api-server.pid
    echo $WEBHOOK_PID > logs/webhook-server.pid
    
    echo ""
    echo "🎉 Sigmoix AI Voice Agent is now running!"
    echo "========================================"
    echo "📱 Frontend: http://localhost:3001"
    echo "🔧 API Server: http://localhost:3001/api/health"
    echo "🎙️ Webhook Server: http://localhost:8765"
    echo ""
    echo "💡 Usage:"
    echo "  1. Open http://localhost:3001 in your browser"
    echo "  2. Click 'Talk to Agent' button"
    echo "  3. Enter your phone number"
    echo "  4. Click 'Call Me' to receive a call from the AI agent"
    echo ""
    echo "📋 To stop the services, press Ctrl+C or run: ./stop.sh"
    echo ""
    
    # Function to cleanup on exit
    cleanup() {
        echo ""
        echo "🛑 Stopping services..."
        kill $API_PID $WEBHOOK_PID 2>/dev/null
        rm -f logs/api-server.pid logs/webhook-server.pid
        echo "✅ Services stopped"
        exit 0
    }
    
    # Set up signal handlers
    trap cleanup SIGINT SIGTERM
    
    # Wait for services to run
    wait
}

# Check if services are already running
if [ -f "logs/api-server.pid" ] && [ -f "logs/webhook-server.pid" ]; then
    API_PID=$(cat logs/api-server.pid)
    WEBHOOK_PID=$(cat logs/webhook-server.pid)
    
    if ps -p $API_PID > /dev/null && ps -p $WEBHOOK_PID > /dev/null; then
        echo "⚠️  Services are already running!"
        echo "API Server PID: $API_PID"
        echo "Webhook Server PID: $WEBHOOK_PID"
        echo "To restart, first run: ./stop.sh"
        exit 1
    else
        rm -f logs/api-server.pid logs/webhook-server.pid
    fi
fi

# Start the services
start_services