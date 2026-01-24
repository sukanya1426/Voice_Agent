#!/bin/bash

echo "🛑 Stopping Sigmoix AI Voice Agent services..."

# Function to stop process by PID file
stop_process() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if kill -0 "$PID" 2>/dev/null; then
            echo "   Stopping $service_name (PID: $PID)..."
            kill "$PID"
            sleep 2
            if kill -0 "$PID" 2>/dev/null; then
                echo "   Force stopping $service_name..."
                kill -9 "$PID"
            fi
            echo "   ✅ $service_name stopped"
        else
            echo "   ⚠️  $service_name was not running"
        fi
        rm -f "$pid_file"
    else
        echo "   ⚠️  No PID file found for $service_name"
    fi
}

# Stop API server
stop_process ".api_pid" "API Server"

# Stop webhook server
stop_process ".webhook_pid" "Webhook Server"

# Stop ngrok if running
if [ -f ".ngrok_pid" ]; then
    stop_process ".ngrok_pid" "ngrok"
elif pgrep -f "ngrok http 8765" > /dev/null; then
    echo "   Stopping ngrok..."
    pkill -f "ngrok http 8765"
    echo "   ✅ ngrok stopped"
fi

# Clean up any remaining processes
echo "🧹 Cleaning up..."
pkill -f "api-server.js" 2>/dev/null
pkill -f "twilio_webhook_server.py" 2>/dev/null

echo "✅ All services stopped successfully!"