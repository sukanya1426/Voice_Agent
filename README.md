# Sigmoix AI Voice Agent

An intelligent voice assistant for product inquiries with Twilio integration and a beautiful web interface.

## 🏗️ Architecture

```
Voice_Agent/
├── Frontend/           # Web interface with talk-to-agent functionality
│   ├── index.html     # Main web application
│   ├── styles.css     # Modern responsive styling  
│   └── script.js      # Frontend interaction logic
├── Backend/           # Voice agent server and API
│   ├── bot.py              # Main voice agent (Pipecat + Twilio)
│   ├── api-server.js       # Express API server for frontend
│   ├── twilio_webhook_server.py # Webhook server for Twilio
│   ├── twilio_call_service.py   # Outbound call service
│   ├── rag_pipeline.py     # RAG pipeline for product search
│   ├── products_merged.csv # Product database (10,799 products)
│   ├── requirements.txt    # Python dependencies
│   ├── .env               # Environment variables
│   └── package.json       # Node.js dependencies and scripts
├── venv/              # Python virtual environment
└── README.md          # This file
```

## ✨ Features

### Frontend (Web Interface)
- **Modern UI**: Clean, responsive design
- **Talk to Agent Button**: One-click access to voice assistant
- **Interactive Modal**: Popup interface for initiating calls
- **Real-time Status**: Connection status and call progress
- **Product Demo**: Interactive chat preview
- **Mobile Responsive**: Works on all devices
- **Bangladesh Phone Support**: Default +880 country code

### Backend (Voice Agent)
- **AI Voice Assistant**: Real-time voice conversation with Twilio integration
- **RAG Pipeline**: Search through 10,799+ technology products
- **Multi-AI Support**: Cerebras, OpenAI LLM integration
- **Speech Services**: Deepgram (STT) + Cartesia (TTS)
- **Product Search**: Natural language product queries
- **Outbound Calls**: Call customers directly
- **Webhook Integration**: Handle incoming calls via Twilio

## Prerequisites

- **Python 3.11+** with virtual environment
- **Node.js 16+**
- **ngrok** for webhook tunneling
- **API Keys**:
  - [Twilio Account](https://console.twilio.com/) (Account SID, Auth Token, Phone Number)
  - [Deepgram](https://console.deepgram.com/) (Speech-to-Text)
  - [Cartesia](https://cartesia.ai/) (Text-to-Speech)
  - [Cerebras](https://inference.cerebras.ai/) or [OpenAI](https://platform.openai.com/) (LLM)

## 🚀 Quick Start Guide

### Step 1: Clone and Setup Project

```bash
git clone https://github.com/your-repo/Voice_Agent.git
cd Voice_Agent
```

### Step 2: Setup Python Environment

```bash
# Create virtual environment in project root
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate    # On Windows

# Install Python dependencies
cd Backend
pip install -r requirements.txt
```

### Step 3: Setup Node.js Dependencies

```bash
# Install Node.js dependencies (stay in Backend directory)
npm install
```

### Step 4: Configure Environment Variables

```bash
# Copy and edit the .env file
cp .env.example .env  # If available, or create new .env file
```

Edit the `.env` file with your API keys:

```bash
# Speech-to-Text (Deepgram)
DEEPGRAM_API_KEY="your_deepgram_api_key_here"

# Text-to-Speech (Cartesia)
CARTESIA_API_KEY="your_cartesia_api_key_here"

# LLM (Cerebras - preferred, or OpenAI as fallback)
CEREBRAS_API_KEY="your_cerebras_api_key_here"
OPENAI_API_KEY="your_openai_api_key_here"

# Twilio Configuration
TWILIO_ACCOUNT_SID="your_twilio_account_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
TWILIO_PHONE_NUMBER="your_twilio_phone_number"  # e.g., +16592468685

# Ngrok Configuration
NGROK_AUTHTOKEN="your_ngrok_auth_token"
NGROK_HOST="your-unique-subdomain.ngrok-free.dev"
PIPECAT_PROXY_HOST="your-unique-subdomain.ngrok-free.dev"
```

### Step 5: Setup Ngrok Tunnel

**Option 1: Using ngrok executable (included)**
```bash
# From Backend directory
./ngrok http 8765
```

**Option 2: Using global ngrok**
```bash
# Install ngrok globally
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# Authenticate (one-time setup)
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Start tunnel
ngrok http 8765
```

**Important**: Copy the ngrok URL (e.g., `https://abc123.ngrok-free.dev`) and update your `.env` file:
```bash
NGROK_HOST=abc123.ngrok-free.dev
PIPECAT_PROXY_HOST=abc123.ngrok-free.dev
```

## 🏃‍♂️ Running the Application

### Complete Application (Recommended)

```bash
# Make sure you're in the Backend directory
cd Voice_Agent/Backend

# Activate virtual environment
source ../venv/bin/activate  # On macOS/Linux
# ..\venv\Scripts\activate    # On Windows

# Start everything (API server + Webhook server)
npm run dev
```

This starts:
- **API Server**: http://localhost:3001 (Frontend available here)
- **Webhook Server**: http://0.0.0.0:8765 (for Twilio webhooks)

### Running Components Separately

**Terminal 1: Start API Server**
```bash
cd Voice_Agent/Backend
npm run server
# Runs on http://localhost:3001
```

**Terminal 2: Start Webhook Server**
```bash
cd Voice_Agent/Backend
source ../venv/bin/activate
python twilio_webhook_server.py
# Runs on port 8765
```

**Terminal 3: Start Ngrok Tunnel**
```bash
cd Voice_Agent/Backend
./ngrok http 8765
# Note the public URL and update .env file
```

### Testing the Application

1. **Open Web Interface**: http://localhost:3001
2. **Click "Talk to Agent"**
3. **Enter Phone Number**: 
   - Select country code (+880 for Bangladesh)
   - Enter your number (e.g., 1312190214)
4. **Click "Call Me"**
5. **Answer Your Phone**: The Sigmoix AI assistant will greet you!

### Example Conversation

When you answer the call:
- **AI**: "Hello from Sigmoix AI! I'm your technology product assistant. Tell me what you're looking for and I'll help you find the perfect product."
- **You**: "I need a gaming laptop under 50,000 Taka"
- **AI**: "I found several great gaming laptops in your budget. Let me tell you about..."

## 🔧 Available Scripts

From the `Backend` directory:

```bash
# Development (starts both servers)
npm run dev

# Production
npm start                    # Start API server only
npm run server              # Start API server only
npm run start-webhook       # Start webhook server only

# Testing
npm run test-call           # Test call functionality
npm run test-rag           # Test RAG pipeline

# Setup
npm run full-setup         # Install all dependencies
```

## 📞 Twilio Configuration

### Required Twilio Setup

1. **Create Twilio Account**: https://console.twilio.com/
2. **Get Phone Number**: Buy a Twilio phone number
3. **Configure Webhook**: 
   - Go to Phone Numbers → Manage → Active Numbers
   - Select your number
   - Set webhook URL to: `https://your-ngrok-url.ngrok-free.dev/webhook/twilio/start`
4. **Copy Credentials**: Account SID, Auth Token, Phone Number

### Bangladesh Phone Support

The system is pre-configured for Bangladesh (+880) calls:
- Default country code: +880
- Format: +8801312190214 (your number: 01312190214)
- International calling enabled through Twilio

## 🛠️ Development

### Project Structure
```
Backend/
├── bot.py                 # Main voice agent (Pipecat pipeline)
├── twilio_webhook_server.py  # FastAPI webhook server
├── twilio_call_service.py    # Outbound call service
├── api-server.js          # Express.js API server
├── rag_pipeline.py        # Product search & AI pipeline
├── products_merged.csv    # 10,799 product database
└── requirements.txt       # Python dependencies

Frontend/
├── index.html            # Main web application
├── script.js            # Frontend logic & API calls
└── styles.css           # Responsive styling
```

### Key Components

1. **Voice Pipeline** (`bot.py`):
   - Deepgram: Speech-to-Text
   - Cerebras/OpenAI: AI responses with RAG
   - Cartesia: Text-to-Speech
   - Twilio: Phone integration

2. **RAG Pipeline** (`rag_pipeline.py`):
   - 10,799 technology products
   - Semantic search with embeddings
   - Product recommendations

3. **API Layer** (`api-server.js`):
   - Frontend serving
   - Call initiation endpoint
   - Health checks

## 🚨 Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'pipecat'"
```bash
# Solution: Activate virtual environment and install requirements
source venv/bin/activate
cd Backend
pip install -r requirements.txt
```

#### 2. Call connects but says "Trial Account" message
```bash
# Solution: Ngrok tunnel not working properly
# Check if ngrok is running and .env has correct NGROK_HOST
./ngrok http 8765
# Copy the URL to .env file
```

#### 3. "RuntimeWarning: Couldn't find ffmpeg"
```bash
# Solution: Install ffmpeg (optional, doesn't break functionality)
brew install ffmpeg  # macOS
# sudo apt install ffmpeg  # Linux
```

#### 4. API Server can't start
```bash
# Solution: Check if port 3001 is free
lsof -i :3001
# Kill any processes using the port
kill -9 <PID>
```

#### 5. Webhook Server import errors
```bash
# Solution: Make sure virtual environment is activated
which python  # Should show path to venv/bin/python
source venv/bin/activate
```

### Debug Mode

```bash
# Check if all services are running
curl http://localhost:3001/api/health
curl http://localhost:8765/

# Test webhook endpoint
curl https://your-ngrok-url.ngrok-free.dev/

# Verbose logging
DEBUG=* npm run dev
```

## 🌟 Features in Detail

### AI Voice Agent Capabilities
- **Natural Conversation**: Handles interruptions, context switching
- **Product Search**: Semantic search through 10,799+ products
- **Price Queries**: Real-time pricing and availability
- **Recommendations**: AI-powered product suggestions
- **Multi-language**: Supports Bengali and English queries

### Web Interface Features
- **One-Click Calling**: Direct call initiation from browser
- **Real-time Status**: Call progress and connection status
- **Mobile Responsive**: Works on phones, tablets, desktops
- **Country Code Support**: Automatic +880 (Bangladesh) selection
- **Call History**: Track previous interactions

### Technical Features
- **High Availability**: Automatic failover and retry logic
- **Scalable**: Handles multiple concurrent calls
- **Secure**: Environment-based configuration
- **Monitoring**: Built-in health checks and logging
- **Fast**: Optimized AI pipeline for real-time responses

---

## 📋 Quick Start Checklist

- [ ] ✅ Python virtual environment created
- [ ] ✅ Node.js dependencies installed  
- [ ] 🔲 API keys configured in .env
- [ ] 🔲 Ngrok tunnel running
- [ ] 🔲 Updated .env with ngrok URL
- [ ] 🔲 Started application with `npm run dev`
- [ ] 🔲 Tested call functionality
- [ ] 🔲 Voice agent responds correctly

**Ready to start? Run `npm run dev` and call your AI assistant! 🚀**

## 📞 Support & Contact

- **Twilio Documentation**: https://www.twilio.com/docs
- **Twilio Console**: https://console.twilio.com/
- **Pipecat Documentation**: https://docs.pipecat.ai/
- **Project Issues**: Create issues in your repository
- **AI Services**: 
  - [Deepgram Docs](https://developers.deepgram.com/)
  - [Cartesia Docs](https://docs.cartesia.ai/)
  - [Cerebras Docs](https://inference.cerebras.ai/docs)

---

**Ready to talk to your AI? Open http://localhost:3001, click "Talk to Agent", and call your assistant! 🎉**