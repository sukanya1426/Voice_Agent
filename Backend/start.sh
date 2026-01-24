#!/bin/bash

# Sigmoix AI Voice Agent Startup Script
echo "🚀 Starting Sigmoix AI Voice Agent..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please create one with your API keys."
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
REQUIRED_VARS=("TWILIO_ACCOUNT_SID" "TWILIO_AUTH_TOKEN" "TWILIO_PHONE_NUMBER" "DEEPGRAM_API_KEY" "CARTESIA_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    exit 1
fi

echo "✅ Environment variables validated"

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Install Python dependencies if needed
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Start ngrok if needed (optional)
if command -v ngrok &> /dev/null && [ ! -z "$NGROK_AUTHTOKEN" ]; then
    echo "🌐 Starting ngrok tunnel..."
    ngrok authtoken $NGROK_AUTHTOKEN
    nohup ngrok http 8765 > ngrok.log 2>&1 &
    sleep 3
    
    # Get ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null || echo "")
    if [ ! -z "$NGROK_URL" ]; then
        echo "✅ ngrok tunnel active: $NGROK_URL"
        export PIPECAT_PROXY_HOST=$(echo $NGROK_URL | sed 's/https:\/\///')
    fi
fi

echo "🎯 Starting services..."

# Start API server in background
echo "🖥️  Starting API server..."
nohup node api-server.js > api-server.log 2>&1 &
API_PID=$!

# Start webhook server in background
echo "📞 Starting webhook server..."
nohup python3 twilio_webhook_server.py > webhook-server.log 2>&1 &
WEBHOOK_PID=$!

# Wait a moment for services to start
sleep 2

echo "✅ Services started successfully!"
echo "   - API Server: http://localhost:3001"
echo "   - Webhook Server: http://localhost:8765"
echo "   - Frontend: http://localhost:3001 (served by API server)"

if [ ! -z "$NGROK_URL" ]; then
    echo "   - Public URL: $NGROK_URL"
fi

echo ""
echo "💡 To stop all services, run: ./stop.sh"
echo "💡 To test the call service: python3 test_call.py"
echo ""
echo "🎉 Sigmoix AI Voice Agent is ready!"

# Save PIDs for stop script
echo "$API_PID" > .api_pid
echo "$WEBHOOK_PID" > .webhook_pid