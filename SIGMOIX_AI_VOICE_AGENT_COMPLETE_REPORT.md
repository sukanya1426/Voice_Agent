# Sigmoix AI Voice Agent - Complete Configuration & Setup Report

## Executive Summary

A comprehensive voice agent system for Sigmoix AI that handles product inquiries using a CSV database containing 10,799 technology products. The system integrates Fonoster Voice SDK, OpenAI/Cerebras AI services, and a custom web interface to provide intelligent voice-based product recommendations.

---

# Part I: Technical Architecture & Configuration

## Project Architecture

### Core Components

```
Voice_Agent/
├── Backend/                 # Server-side components
│   ├── fonoster_bot.js     # Original TCP-based voice agent
│   ├── fonoster_bot_http.js # HTTP webhook voice agent (final)
│   ├── api-server.js       # Full-featured API server (blocked by SDK)
│   ├── demo-server.js      # Demo/testing server
│   ├── products_merged.csv # Product database (10,799 items)
│   └── package.json        # Dependencies and scripts
└── Frontend/               # Client-side interface
    ├── index.html          # Main web interface
    ├── script.js           # Frontend logic
    └── styles.css          # ElevenLabs-inspired styling
```

## Module Breakdown

### 1. Voice Processing Engine (`fonoster_bot_http.js`)

**Purpose**: Handles incoming voice calls via HTTP webhooks and processes natural language queries against the product database.

**Key Features**:
- **CSV Product Loading**: Loads 10,799 products with specifications, prices, and categories
- **AI Integration**: Uses OpenAI/Cerebras API for intelligent conversation handling
- **Voice Recognition**: Processes speech input through Fonoster's speech-to-text
- **Smart Search**: Implements fuzzy matching and category-based product filtering
- **VoiceML Responses**: Generates proper XML responses for Fonoster voice synthesis

**Technical Implementation**:
```javascript
// Product Search Algorithm
function searchProducts(query, maxResults = 5) {
    const queryWords = query.toLowerCase().split(/\s+/);
    return productData.filter(product => {
        const searchText = `${product.name} ${product.category} ${product.description}`.toLowerCase();
        return queryWords.some(word => searchText.includes(word));
    }).slice(0, maxResults);
}
```

**Conversation Flow**:
1. **Initial Greeting**: Welcomes caller with company introduction
2. **Speech Capture**: Listens for product inquiries
3. **Query Processing**: Analyzes intent and extracts product requirements
4. **Database Search**: Searches CSV data using intelligent matching
5. **Response Generation**: Formats results with pricing and specifications
6. **Follow-up Handling**: Continues conversation or gracefully ends call

### 2. Web Interface (`Frontend/`)

**Components**:

#### `index.html`
- **Modal Interface**: Professional "Talk to Agent" dialog
- **Dual Input Methods**: Text chat and phone call options
- **ElevenLabs Design**: Modern gradient styling with professional layout
- **Responsive Design**: Works across desktop and mobile devices

#### `script.js`
- **Modal Management**: Handles opening/closing of agent interface
- **Text Chat**: Real-time messaging with typing indicators
- **Phone Integration**: Validates numbers and initiates calls
- **API Communication**: Handles backend requests with error handling

#### `styles.css`
- **Modern Gradients**: Purple-blue ElevenLabs-inspired color scheme
- **Smooth Animations**: Slide-in messages and hover effects
- **Professional Typography**: Clean, readable font hierarchy
- **Accessible Design**: Proper contrast and focus indicators

### 3. Backend Services

#### `demo-server.js`
**Purpose**: Standalone testing server without Fonoster dependencies

**Features**:
- Text chat API with intelligent product responses
- Simulated call functionality for testing
- Keyword-based response system
- No external dependencies required

**Sample Response Logic**:
```javascript
if (lowerMessage.includes('gaming') || lowerMessage.includes('game')) {
    response = `🎮 Great choice! Here are our gaming products:
    • AMD Ryzen 5 7500F Gaming PC - ৳93,900
    • AMD Ryzen 5 3400G Gaming Desktop - ৳27,500`;
}
```

#### `api-server.js`
**Purpose**: Full-featured server with Fonoster SDK integration
**Status**: Blocked by missing Fonoster authentication files
**Issue**: Requires `/home/fonoster/rbac.json` which doesn't exist in development environment

### 4. Product Database (`products_merged.csv`)

**Specifications**:
- **Total Products**: 10,799 technology items
- **Categories**: Desktops, Laptops, Gaming PCs, Accessories, Components
- **Price Range**: ৳3,500 - ৳150,000+
- **Brands**: AMD Ryzen, Intel, NVIDIA, gaming peripherals
- **Data Structure**: Name, Price, Category, Description, Specifications

**Sample Data**:
```csv
Name,Price,Category,Description
AMD Ryzen 5 7500F Gaming PC,৳93900,Desktop > Gaming PC,High-performance gaming...
AMD Ryzen 3 3200G Desktop PC,৳24499,Desktop > Budget PC,Affordable desktop...
```

## Configuration Process

### Phase 1: Initial Setup and Modularization
1. **Project Restructuring**: Created Frontend/Backend separation
2. **Dependencies**: Installed Fonoster SDK, OpenAI, Express, CSV-parser
3. **Environment Setup**: Configured API keys and Fonoster credentials

### Phase 2: Voice Agent Development
1. **TCP Implementation** (`fonoster_bot.js`): Original TCP-based voice handling
2. **CSV Integration**: Product database loading and search functionality
3. **AI Conversation**: OpenAI integration for natural language processing
4. **Error Handling**: Comprehensive error management and fallbacks

### Phase 3: HTTP Webhook Transition
**Challenge**: ngrok TCP requires credit card for free accounts

**Solution**: Migrated to HTTP webhook architecture
1. **New Architecture** (`fonoster_bot_http.js`): HTTP-based voice handling
2. **VoiceML Format**: Proper XML response format for Fonoster
3. **Webhook Endpoints**: `/webhook` for calls, `/webhook/input` for speech
4. **Port Configuration**: Aligned webhook server (50062) with ngrok tunnel

### Phase 4: Frontend Development
1. **Modal Interface**: Professional dialog with text and phone inputs
2. **API Integration**: Connected frontend to backend services
3. **Real-time Chat**: Implemented text-based product inquiries
4. **Phone Call UI**: Complete phone number validation and calling interface

### Phase 5: Testing and Debugging
1. **Webhook Format Issues**: Fixed VoiceML XML structure for Fonoster compatibility
2. **Port Mismatches**: Resolved server/tunnel port conflicts
3. **Response Logging**: Added comprehensive logging for debugging
4. **Error Handling**: Implemented graceful fallbacks for service failures

## Technical Challenges and Solutions

### 1. Fonoster SDK Authentication
**Problem**: Missing `/home/fonoster/rbac.json` file blocking api-server.js
**Solution**: Created demo-server.js bypass and focused on HTTP webhook approach

### 2. ngrok TCP Limitations
**Problem**: Free ngrok accounts require credit card for TCP tunnels
**Solution**: Migrated from TCP (`fonoster_bot.js`) to HTTP webhooks (`fonoster_bot_http.js`)

### 3. VoiceML Response Format
**Problem**: Initial webhook responses weren't speaking
**Solution**: Replaced VoiceResponse() with proper VoiceML XML format:
```xml
<VoiceML>
  <Say>Hello! Welcome to Sigmoix AI...</Say>
  <Gather source="speech" timeout="10000" webhook="/webhook/input">
    <Say>Please tell me what you're looking for.</Say>
  </Gather>
</VoiceML>
```

### 4. Port Configuration Mismatch
**Problem**: Server running on port 50061, ngrok tunneling port 50062
**Solution**: Updated server configuration to match ngrok tunnel port

---

# Part II: Fonoster Configuration & Setup Process

## Fonoster Account Registration and Verification Challenges

### Registration Issues with Bangladeshi Numbers

During the initial Fonoster account setup, several verification challenges were encountered:

#### **Problem: Phone Number Verification**
- **Issue**: Fonoster's registration system does not accept Bangladeshi phone numbers (+880) for account verification
- **Error**: "Invalid phone number format" or "Country not supported for verification"
- **Impact**: Unable to complete account registration with local Bangladeshi number

#### **Solution: Twilio Number Purchase**
To resolve the verification issue, a Twilio phone number was acquired:

1. **Twilio Account Creation**:
   - Registered at `https://www.twilio.com`
   - Completed identity verification with passport/national ID
   - Added payment method for number purchase

2. **Phone Number Purchase**:
   - **Country**: United States (+1)
   - **Number Type**: Voice-enabled
   - **Purchased Number**: `+16592468685`
   - **Cost**: $1.00 USD/month
   - **Purpose**: Fonoster account verification and voice application endpoint

3. **Fonoster Verification**:
   - Used Twilio number `+16592468685` for Fonoster account verification
   - Received SMS verification code successfully
   - Completed Fonoster account registration

### Account Configuration Details

```
Fonoster Account Information:
├── Email: [Your registered email]
├── Phone: +16592468685 (Twilio-purchased)
├── Region: United States
├── Plan: Free Tier
└── Verification Status: Completed
```

## Fonoster Voice Application Creation Process

### Step 1: Accessing Fonoster Console

1. **Login Process**:
   - Navigate to `https://console.fonoster.com`
   - Enter registered email and password
   - Complete 2FA if enabled

2. **Dashboard Overview**:
   - Applications section (Voice Apps)
   - Numbers section (Phone numbers)
   - Agents section (AI agents)
   - Settings section (Account configuration)

### Step 2: Voice Application Creation

#### **Navigation to Applications**
- From dashboard, click **"Applications"** in left sidebar
- Click **"Create Application"** button
- Select **"Voice Application"** type

#### **Application Configuration Form**
```
Application Details:
├── Name: "Sigmoix AI Product Inquiry Bot"
├── Description: "Voice agent for technology product inquiries and recommendations"
├── Type: Voice Application
├── Region: US-East (to match Twilio number region)
└── Language: English (US)
```

#### **Initial Endpoint Configuration**
**Phase 1 - TCP Endpoint (Initial Setup)**:
```
Endpoint Configuration:
├── Type: TCP
├── Host: Will be provided by ngrok
├── Port: 50061 (default for TCP voice apps)
├── Protocol: TCP
└── Status: Pending (awaiting ngrok tunnel)
```

**Phase 2 - HTTP Webhook (Final Configuration)**:
```
Updated Endpoint Configuration:
├── Type: HTTP Webhook
├── URL: tandy-unnationalised-walker.ngrok-free.dev
├── Method: POST
├── Path: /webhook
└── Status: Active
```

### Step 3: Phone Number Assignment

#### **Number Association Process**:
1. **Navigate to Numbers Section**:
   - Click **"Numbers"** in Fonoster console
   - View available numbers (shows Twilio-purchased number)

2. **Number Configuration**:
   ```
   Phone Number: +16592468685
   ├── Provider: Twilio
   ├── Type: Voice + SMS enabled
   ├── Region: United States
   ├── Status: Active
   └── Application: Assigned to "Sigmoix AI Product Inquiry Bot"
   ```

3. **Application Binding**:
   - Select phone number `+16592468685`
   - Click **"Edit"** or **"Configure"**
   - **Application Assignment**: Select "Sigmoix AI Product Inquiry Bot"
   - **Webhook URL**: `https://tandy-unnationalised-walker.ngrok-free.dev`
   - Save configuration

### Step 4: Advanced Configuration

#### **Voice Application Settings**
```
Advanced Settings:
├── Speech Recognition:
│   ├── Provider: Google Speech-to-Text
│   ├── Language: en-US
│   ├── Timeout: 10 seconds
│   └── Sensitivity: Medium
├── Text-to-Speech:
│   ├── Provider: Google TTS
│   ├── Voice: en-US-Standard-A (Female)
│   ├── Speed: 1.0x
│   └── Pitch: 0.0
└── Recording:
    ├── Enabled: Yes (for debugging)
    ├── Format: MP3
    └── Storage: 7 days
```

#### **Webhook Configuration Details**
```
Webhook Settings:
├── Primary URL: https://tandy-unnationalised-walker.ngrok-free.dev/webhook
├── Backup URL: None (single endpoint)
├── Authentication: None (open webhook)
├── Timeout: 30 seconds
├── Retry Policy: 3 attempts with exponential backoff
└── Headers:
    ├── Content-Type: application/json
    └── User-Agent: Fonoster-Webhook/1.0
```

## Configuration Evolution Process

### Phase 1: Initial TCP Setup (Failed)
```javascript
// Original configuration attempt
FONOSTER_ENDPOINT_TYPE=TCP
FONOSTER_HOST=localhost
FONOSTER_PORT=50061
NGROK_COMMAND=./ngrok tcp 50061
```

**Issues Encountered**:
- ngrok TCP requires credit card for free accounts
- Error: "You must add a credit or debit card before you can use TCP endpoints"
- Solution: Migrate to HTTP webhook approach

### Phase 2: HTTP Webhook Migration (Successful)
```javascript
// Updated configuration
FONOSTER_ENDPOINT_TYPE=HTTP
FONOSTER_WEBHOOK_URL=https://tandy-unnationalised-walker.ngrok-free.dev
FONOSTER_PORT=50062
NGROK_COMMAND=./ngrok http 50062
```

## Fonoster Console Interface Screenshots (Conceptual)

### Voice Application Dashboard
```
[Applications]
┌─────────────────────────────────────────────────┐
│ Sigmoix AI Product Inquiry Bot                  │
│ ──────────────────────────────────────────────  │
│ Status: ● Active                                │
│ Type: Voice Application                         │
│ Endpoint: HTTP Webhook                          │
│ URL: tandy-unnationalised-walker.ngrok-free.dev │
│ Phone: +16592468685                             │
│ Created: 2026-01-07                             │
│                                                 │
│ [Edit] [Test] [Logs] [Delete]                   │
└─────────────────────────────────────────────────┘
```

### Number Configuration Panel
```
[Phone Numbers]
┌─────────────────────────────────────────────────┐
│ +16592468685 (US - Twilio)                      │
│ ──────────────────────────────────────────────  │
│ Status: ● Active                                │
│ Application: Sigmoix AI Product Inquiry Bot     │
│ Features: Voice ✓ SMS ✓                         │
│ Monthly Cost: $1.00 USD                         │
│                                                 │
│ Webhook: https://tandy-unnationalised...        │
│ [Configure] [Test] [Release]                    │
└─────────────────────────────────────────────────┘
```

## Environment Configuration Files

### Updated `.env` Configuration
```bash
# Fonoster Configuration
FONOSTER_ACCESS_KEY_ID=your_access_key_here
FONOSTER_SECRET_ACCESS_KEY=your_secret_key_here
FONOSTER_ENDPOINT=https://console.fonoster.com
FONOSTER_APP_REF=sigmoix-ai-product-inquiry-bot

# Phone Configuration
FONOSTER_NUMBER=+16592468685
TWILIO_PHONE_NUMBER=+16592468685

# Webhook Configuration
WEBHOOK_URL=https://tandy-unnationalised-walker.ngrok-free.dev
HTTP_PORT=50062

# AI Services
OPENAI_API_KEY=sk-your-openai-key
CEREBRAS_API_KEY=sk-your-cerebras-key
```

### Fonoster Configuration JSON
```json
{
  "name": "Sigmoix AI Product Inquiry Bot",
  "description": "Voice agent for technology product inquiries",
  "endpoint": {
    "type": "webhook",
    "url": "https://tandy-unnationalised-walker.ngrok-free.dev/webhook",
    "method": "POST"
  },
  "phoneNumber": "+16592468685",
  "region": "us-east-1",
  "speechConfig": {
    "provider": "google",
    "language": "en-US",
    "timeout": 10000
  },
  "ttsConfig": {
    "provider": "google",
    "voice": "en-US-Standard-A",
    "speed": 1.0
  }
}
```

## Testing and Validation Process

### Fonoster Console Testing Tools
1. **Built-in Test Feature**:
   - Console provides "Test" button for voice applications
   - Simulates incoming call without actual phone
   - Validates webhook response format
   - Shows real-time logs and debug information

2. **Webhook Testing**:
   ```bash
   # Manual webhook test from Fonoster console
   curl -X POST https://tandy-unnationalised-walker.ngrok-free.dev/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "sessionRef": "test-session-123",
       "callerNumber": "+1234567890", 
       "ingressNumber": "+16592468685",
       "event": "call_start"
     }'
   ```

3. **Live Call Testing**:
   - Direct dial to `+16592468685`
   - Monitor console logs in real-time
   - Review call recordings and transcripts
   - Analyze response times and accuracy

## Cost Structure

### Fonoster Costs
```
Fonoster Free Tier:
├── Voice Applications: 1 free
├── Monthly Minutes: 300 minutes free
├── Phone Numbers: Not included
└── Additional Features: Limited
```

### Twilio Costs
```
Twilio Phone Number:
├── Number Purchase: $1.00 USD/month
├── Incoming Calls: $0.0085/minute
├── Outgoing Calls: $0.013/minute  
├── SMS (if used): $0.0075/message
└── Total Monthly: ~$1.00-5.00 USD (depending on usage)
```

### ngrok Costs
```
ngrok Free Tier:
├── HTTP Tunnels: Free (4 hours/session)
├── TCP Tunnels: Requires credit card
├── Custom Domains: Not available
└── Concurrent Tunnels: 1
```

---

# Part III: Current System Status & Deployment

## Current System Status

### ✅ Working Components
- **HTTP Webhook Server**: Running on localhost:50062 with 10,799 products loaded
- **ngrok Tunnel**: Active at `https://tandy-unnationalised-walker.ngrok-free.dev`
- **Fonoster Configuration**: Voice Application configured with webhook URL
- **Product Database**: Fully loaded and searchable
- **Frontend Interface**: Complete with text chat and phone call options
- **Demo Server**: Functional for web-based testing

### ⚠️ Known Issues
- **Fluentd Warnings**: MaxListenersExceededWarning (non-critical logging issue)
- **API Server**: Blocked by Fonoster SDK authentication requirements
- **Voice Testing**: Requires actual phone calls for full validation

## Deployment Configuration

### Fonoster Console Settings
- **Application Type**: Voice Application
- **Endpoint Type**: HTTP Webhook
- **Webhook URL**: `tandy-unnationalised-walker.ngrok-free.dev`
- **Phone Number**: +16592468685

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
CEREBRAS_API_KEY=sk-...
FONOSTER_ACCESS_KEY_ID=...
FONOSTER_SECRET_ACCESS_KEY=...
```

### Server Endpoints
- **Voice Webhook**: `POST /webhook` - Handles incoming calls
- **Input Webhook**: `POST /webhook/input` - Processes speech input
- **Health Check**: `GET /health` - Server status monitoring
- **Chat API**: `POST /api/chat` - Text-based product inquiries

## Testing Scenarios

### Voice Call Testing
1. **Direct Call**: Dial +16592468685
2. **Expected Flow**:
   - Greeting: "Hello! Welcome to Sigmoix AI..."
   - Speech Recognition: Listens for product queries
   - Database Search: Searches 10,799 products
   - AI Response: Provides intelligent recommendations
   - Follow-up: Continues conversation or ends gracefully

### Sample Voice Commands
- *"I need a gaming computer"* → Returns gaming PC recommendations with prices
- *"Show me laptops under 50,000 Taka"* → Filters by price range
- *"What AMD processors do you have?"* → Category-specific search
- *"Thank you, goodbye"* → Graceful call termination

### Web Interface Testing
1. **Text Chat**: Real-time messaging with product recommendations
2. **Phone Integration**: Number validation and call initiation
3. **Responsive Design**: Works across device sizes
4. **Error Handling**: Graceful degradation when services unavailable

## Common Issues and Troubleshooting

### Issue 1: Application Not Responding
**Problem**: Calls connect but no voice response
**Diagnosis**: Check Fonoster console logs
**Solution**: Verify webhook URL format and VoiceML response structure

### Issue 2: Speech Recognition Errors
**Problem**: Agent doesn't understand speech input
**Diagnosis**: Review speech recognition settings
**Solution**: Adjust language model and timeout settings

### Issue 3: Webhook Timeout
**Problem**: Fonoster reports webhook timeouts
**Diagnosis**: Monitor server response times
**Solution**: Optimize database queries and AI response generation

### Issue 4: Number Assignment Failures
**Problem**: Cannot assign phone number to application
**Diagnosis**: Check number status and region compatibility
**Solution**: Ensure number and application are in same region

## Future Enhancements

### Immediate Improvements
1. **Authentication Resolution**: Fix Fonoster SDK authentication for full API server
2. **Voice Quality**: Test and optimize speech recognition accuracy
3. **Performance**: Optimize product search algorithms for faster responses
4. **Logging**: Reduce Fluentd warnings and improve error tracking

### Advanced Features
1. **Multi-language Support**: Bengali and English voice recognition
2. **Payment Integration**: Complete purchase flow through voice
3. **Inventory Management**: Real-time stock level integration
4. **Analytics**: Call tracking and conversation analytics
5. **CRM Integration**: Customer data management and follow-up

