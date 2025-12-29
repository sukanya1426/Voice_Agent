## Prerequisites

- Node.js 16+
- [ngrok](https://ngrok.com/docs/getting-started/) (for TCP tunneling)
- [Fonoster Account](https://console.fonoster.com/) and phone number
- AI Service API keys for: [Deepgram](https://console.deepgram.com/signup), [OpenAI](https://auth.openai.com/create-account), or [Cerebras](https://inference.cerebras.ai/)

## Quick Start

1) Clone and enter the repo

```bash
git clone https://github.com/sukanya1426/Voice_Agent.git
cd Voice_Agent
```

2) Create `.env` and add your API keys

```bash
cp .env.example .env
```

```bash
# Fill in .env with your keys:
# FONOSTER_API_KEY=...
# FONOSTER_API_SECRET=...
# FONOSTER_ACCESS_KEY_ID=...
# FONOSTER_APP_REF=...
# OPENAI_API_KEY=... (or CEREBRAS_API_KEY)
```

3) Install dependencies

```bash
npm install
```

4) Run the helper to start ngrok TCP tunnel and your Voice Application

```bash
node fonoster_setup.js
```

- The helper starts ngrok TCP tunnel on port 50061
- Launches your Fonoster Voice Application server
- Displays setup instructions and ngrok URL

5) Deploy to Fonoster and configure

- Deploy your Voice Application to Fonoster Console
- Get your `FONOSTER_APP_REF` and update `.env`
- Configure your Fonoster phone number to use your deployed app

For outbound calls:

```bash
node fonoster_outbound.js --to +15551234567 --from +YOUR_FONOSTER_NUMBER
```

### Test Your Phone Bot

**Call your Fonoster phone number** to start talking with your AI bot! 🚀

> 💡 **Tip**: Check your terminal for debug logs showing your Voice Application's conversation flow.

## Troubleshooting

- **Call doesn't connect**: Verify your Voice Application is deployed and configured in Fonoster Console
- **No audio or bot doesn't respond**: Check that all API keys are correctly set in your `.env` file
- **Voice Application errors**: Ensure your Node.js server is running and ngrok TCP tunnel is active
- **ngrok tunnel issues**: Free ngrok URLs change each restart - redeploy your Voice Application with new URL
- **SDK errors**: Check your Fonoster API credentials and ensure your account has sufficient credits

## Understanding the Call Flow

1. **Incoming Call**: User dials your Fonoster number
2. **Voice Application**: Fonoster routes call to your deployed Voice Application
3. **TCP Connection**: Your local server (via ngrok) handles the call flow
4. **AI Processing**: Speech-to-text → AI response → Text-to-speech
5. **Response**: Synthesized speech streams back to caller through Fonoster

## Outbound calls (Fonoster → phone)

You can place outbound calls that connect the callee to your running Voice Application.

Prereqs:
- Your Voice Application must be deployed to Fonoster
- Your local server can be running for development: `node fonoster_bot.js`
- `FONOSTER_API_KEY`, `FONOSTER_API_SECRET`, `FONOSTER_ACCESS_KEY_ID` set in your environment
- A Fonoster phone number to place calls from

Make the call:

```bash
node fonoster_outbound.js --to +15551234567 --from +YOUR_FONOSTER_NUMBER
```

Notes:
- The script uses Fonoster SDK to initiate calls
- The `appRef` in your `.env` determines which Voice Application handles the call
- You can pass metadata to your Voice Application through the call request

## Development Setup with ngrok

Use this helper to set up your local development environment:

```bash
node fonoster_setup.js
```

This will:
- Start an ngrok TCP tunnel on port 50061
- Launch your Voice Application server locally
- Display the public TCP URL for Fonoster configuration
- Keep the tunnel active for development

Options:
```bash
# Custom port
node fonoster_setup.js --port 8080

# Don't start the Voice Application automatically  
node fonoster_setup.js --no-start-app

# Exit after setup (don't keep tunnel running)
node fonoster_setup.js --no-keep-running
```

For production deployment, you'll want to:
1. Deploy your Voice Application directly to Fonoster's platform
2. Use Fonoster Console to configure your phone numbers
3. Set up proper authentication and scaling

Environment variables needed:
- `FONOSTER_API_KEY`, `FONOSTER_API_SECRET`, `FONOSTER_ACCESS_KEY_ID` - from Fonoster Console
- `FONOSTER_APP_REF` - your deployed Voice Application reference
- `OPENAI_API_KEY` or `CEREBRAS_API_KEY` - for AI responses
- `NGROK_AUTHTOKEN` - recommended for stable tunnels during development

## Voice Application Features

Your Fonoster Voice Application (`fonoster_bot.js`) includes:

- **Restaurant Receptionist**: Handles calls for "The Salusbury" restaurant  
- **Reservation System**: Collects date, time, and party size for bookings
- **AI Conversation**: Natural language processing with OpenAI/Cerebras
- **Speech Recognition**: Built-in speech-to-text via Fonoster
- **Conversation Memory**: Maintains context throughout the call
- **Graceful Handling**: Manages silence, errors, and call termination

The bot can handle both inbound calls (customers calling in) and outbound calls (calling customers back).