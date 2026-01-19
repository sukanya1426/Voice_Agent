#!/bin/bash

# Stop Sigmoix AI Voice Agent Services

echo "🛑 Stopping Sigmoix AI Voice Agent Services..."

# Function to stop process by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat $pid_file)
        if ps -p $pid > /dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null; then
                echo "Force stopping $service_name..."
                kill -9 $pid
            fi
            echo "✅ $service_name stopped"
        else
            echo "⚠️  $service_name was not running"
        fi
        rm -f $pid_file
    else
        echo "⚠️  No PID file found for $service_name"
    fi
}

# Stop services
stop_service "API Server" "logs/api-server.pid"
stop_service "Webhook Server" "logs/webhook-server.pid"

# Also kill any remaining processes
echo "🧹 Cleaning up any remaining processes..."
pkill -f "api-server.js" 2>/dev/null
pkill -f "twilio_webhook_server.py" 2>/dev/null
pkill -f "bot.py" 2>/dev/null

echo "✅ All services stopped"