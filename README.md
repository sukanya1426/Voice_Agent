# Sigmoix AI Voice Agent

A comprehensive voice assistant system that helps customers find technology products through natural conversation. The agent integrates multiple AI services including speech-to-text, large language models, text-to-speech, and a RAG (Retrieval-Augmented Generation) pipeline for product search.

## 🏗️ Architecture

The voice agent follows a modern pipeline architecture:

```
Voice Input → VAD → STT → LLM + RAG → TTS → Voice Output
```

### Core Components

1. **Voice Activity Detection (VAD)**: Silero VAD for detecting speech
2. **Speech-to-Text (STT)**: Deepgram for transcription
3. **Intent Processing (LLM)**: Cerebras/OpenAI with RAG integration
4. **Text-to-Speech (TTS)**: Cartesia for natural voice synthesis
5. **RAG Pipeline**: Custom product search using sentence transformers

### Dual Communication Modes

- **Phone Calls**: Twilio integration for real phone conversations
- **WebRTC**: Browser-based voice chat with Web Speech API

## 🚀 Features

- **Smart Product Search**: Advanced AI searches through extensive product catalog
- **Natural Conversations**: Context-aware responses with human-like interaction
- **Instant Information**: Real-time pricing, specifications, and availability
- **Multi-Channel Support**: Phone calls and web-based voice chat
- **RAG Integration**: Semantic search through product database
- **Responsive Frontend**: Modern web interface with voice controls

## 📁 Project Structure

```
Voice_Agent/
├── Backend/
│   ├── api-server.js                 # Express API server
│   ├── bot.py                        # Main voice agent pipeline
│   ├── rag_pipeline.py              # Product search RAG system
│   ├── twilio_call_service.py       # Twilio call management
│   ├── twilio_webhook_server.py     # Webhook server for calls
│   ├── test_call.py                 # Call testing utility
│   ├── products_merged.csv          # Product database
│   ├── requirements.txt             # Python dependencies
│   ├── package.json                 # Node.js dependencies
│   ├── start.sh                     # Startup script
│   ├── stop.sh                      # Shutdown script
│   └── .env                         # Environment variables
├── Frontend/
│   ├── index.html                   # Main web interface
│   ├── script.js                    # Frontend JavaScript
│   └── styles.css                   # CSS styling
└── README.md                        # This file
```

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- ngrok (for webhook tunneling)

### 1. Environment Configuration

Create a `.env` file in the `Backend/` directory:

```bash
# Speech-to-Text
DEEPGRAM_API_KEY="your_deepgram_api_key"

# Text-to-Speech  
CARTESIA_API_KEY="your_cartesia_api_key"

# Large Language Model (choose one)
CEREBRAS_API_KEY="your_cerebras_api_key"
OPENAI_API_KEY="your_openai_api_key"

# Twilio (for phone calls)
TWILIO_ACCOUNT_SID="your_twilio_account_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
TWILIO_PHONE_NUMBER="+1234567890"

# ngrok (for webhook tunneling)
NGROK_AUTHTOKEN="your_ngrok_authtoken"
PIPECAT_PROXY_HOST="your-ngrok-url.ngrok-free.dev"
```

### 2. Installation

```bash
cd Backend/
chmod +x start.sh stop.sh
./start.sh
```

The startup script will:
- Install all dependencies
- Start the API server (port 3001)
- Start the webhook server (port 8765) 
- Start ngrok tunnel (if configured)

### 3. Access the Application

- **Web Interface**: http://localhost:3001
- **API Health**: http://localhost:3001/api/health
- **Webhook Health**: http://localhost:8765

## 🎯 Usage

### Web Interface

1. **Text Chat**: Type questions about products in the text input
2. **Voice Chat**: Click "Start Voice Chat" for browser-based voice interaction
3. **Phone Call**: Enter your phone number and click "Call Me"

### Example Queries

- "I'm looking for a gaming computer under $1000"
- "Show me AMD Ryzen processors"
- "What's the best laptop for programming?"
- "I need a budget desktop PC"

### Testing

Test the call service directly:
```bash
python test_call.py
```

Test the RAG pipeline:
```bash
python -c "from rag_pipeline import search_products_for_voice_agent; print(search_products_for_voice_agent('gaming PC'))"
```

## 🔧 Configuration

### Voice Agent Settings

The bot behavior can be customized in `bot.py`:
- System prompts
- Response length limits
- Tool function definitions
- Voice settings

### RAG Pipeline Settings

Configure product search in `rag_pipeline.py`:
- Embedding models
- Search thresholds
- Response formatting
- Product categories

### Frontend Customization

Modify the web interface in `Frontend/`:
- `index.html`: Structure and content
- `styles.css`: Visual styling
- `script.js`: Functionality and WebRTC

## 📞 Phone Call Flow

1. User enters phone number on web interface
2. Frontend sends request to API server
3. API server calls Twilio service
4. Twilio initiates outbound call
5. Call connects to webhook server
6. Webhook establishes WebSocket connection
7. Voice agent pipeline handles conversation

## 🌐 WebRTC Flow

1. User clicks "Start Voice Chat"
2. Browser requests microphone permission
3. Web Speech API captures voice input
4. Audio sent to backend for processing
5. RAG pipeline searches products
6. Response generated by LLM
7. Text-to-speech synthesis plays response

## 🛑 Stopping Services

```bash
./stop.sh
```

## 📋 API Endpoints

- `GET /` - Serve frontend
- `GET /api/health` - Health check
- `POST /api/initiate-call` - Start phone call
- `POST /api/test-search` - Test product search
- `POST /webhook/twilio/start` - Twilio webhook
- `WS /ws` - WebSocket for voice streams

## 🐛 Troubleshooting

### Common Issues

1. **No voice input detected**
   - Check browser microphone permissions
   - Ensure HTTPS for Web Speech API

2. **Call initiation fails**
   - Verify Twilio credentials
   - Check ngrok tunnel status
   - Confirm webhook URL accessibility

3. **Product search not working**
   - Ensure `products_merged.csv` exists
   - Check Python dependencies
   - Verify sentence-transformers installation

4. **Backend connection failed**
   - Confirm all services are running
   - Check port availability (3001, 8765)
   - Review service logs

### Logs

Check service logs:
```bash
tail -f api-server.log
tail -f webhook-server.log
tail -f ngrok.log
```

## 🔄 Development

### Adding New Products

Update `products_merged.csv` with new product data. The RAG pipeline will automatically reindex on restart.

### Customizing Voice Agent

Modify the system prompt in `bot.py` to change the agent's personality and capabilities.

### Extending Functionality

Add new tool functions in `bot.py` and corresponding handlers in `rag_pipeline.py`.

## 📊 Performance

- **Response Time**: < 2 seconds for product queries
- **Concurrent Calls**: Supports multiple simultaneous phone calls
- **Product Database**: Optimized for 1000+ products
- **Voice Quality**: Professional-grade with Cartesia TTS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review service logs
- Open an issue with detailed information

---

**Sigmoix AI Voice Agent** - Transforming customer interaction through intelligent voice technology.

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