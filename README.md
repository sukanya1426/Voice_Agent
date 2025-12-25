
## Prerequisites

- Python 3.10+
- [ngrok](https://ngrok.com/docs/getting-started/) (for tunneling)
- [Twilio Account](https://www.twilio.com/login) and [phone number](https://help.twilio.com/articles/223135247-How-to-Search-for-and-Buy-a-Twilio-Phone-Number-from-Console)
- AI Service API keys for: [Deepgram](https://console.deepgram.com/signup), [OpenAI](https://auth.openai.com/create-account), and [Cartesia](https://play.cartesia.ai/sign-up)

## Quick Start

1) Clone and enter the repo

```bash
git clone https://github.com/HugoPodworski/first-pipecat-agent.git
cd first-pipecat-agent
```

2) Create `.env` and add your API keys

```bash
cp env.example .env
```

```bash
# Fill in .env with your keys:
# DEEPGRAM_API_KEY=...
# CARTESIA_API_KEY=...
# CEREBRAS_API_KEY=...   # or OPENAI_API_KEY if you switch models
# TWILIO_ACCOUNT_SID=...
# TWILIO_AUTH_TOKEN=...
```

3) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

4) Run the helper to start ngrok and configure Twilio

```bash
python setup_ngrok_twilio.py
```

- Choose which Twilio number to use.
- The helper starts ngrok, updates your Twilio webhook, and prints a command to run the bot with the correct `--proxy` (ngrok host).
- It also prints a command you can use to place an outbound call.

5) In a new terminal, run the bot command from the helper output

```bash
python bot.py --transport twilio --proxy <ngrok-host>
```

Inbound calls to your Twilio number will now connect to the bot.

For outbound calls, run the printed command, for example:

```bash
python outbound.py --to +15551234567 --from +15557654321 --proxy <ngrok-host>
```

### Test Your Phone Bot

**Call your Twilio phone number** to start talking with your AI bot! 🚀

> 💡 **Tip**: Check your server terminal for debug logs showing Pipecat's internal workings.

## Troubleshooting

- **Call doesn't connect**: Verify your ngrok URL is correctly set in the Twilio webhook
- **No audio or bot doesn't respond**: Check that all API keys are correctly set in your `.env` file
- **Webhook errors**: Ensure your server is running and ngrok tunnel is active before making calls
- **ngrok tunnel issues**: Free ngrok URLs change each restart - remember to update Twilio

## Understanding the Call Flow

1. **Incoming Call**: User dials your Twilio number
2. **Webhook**: Twilio sends call data to your ngrok URL
3. **WebSocket**: Your server establishes real-time audio connection via Websocket and exchanges Media Streams with Twilio
4. **Processing**: Audio flows through your Pipecat Pipeline
5. **Response**: Synthesized speech streams back to caller

## Outbound calls (Twilio → phone)

You can also place outbound calls that connect the callee to your running Pipecat bot.

Prereqs:
- Your server must be running locally: `python bot.py --transport twilio --proxy your_ngrok.ngrok.io`
- Your ngrok tunnel must be active and public (same host you pass via `--proxy`)
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` set in your environment
- A Twilio phone number to place calls from

Make the call:

```bash
python outbound.py --to +15551234567 --from +15557654321 --proxy your_ngrok.ngrok.io
```

Notes:
- The script sends Twilio to `https://<proxy>/` with HTTP POST. The Pipecat runner responds with the XML that instructs Twilio to open a Media Streams WebSocket to `wss://<proxy>/ws`.
- You can override the webhook URL directly with `--url https://example.com/` if you host the runner elsewhere.

## Auto-configure Twilio + ngrok

Use this helper to:
- Start an ngrok tunnel
- Pick which Twilio number to configure
- Set "A call comes in" webhook to your ngrok URL (HTTP POST)
- Optionally set "Primary handler fails" to the same URL
- Optionally write `PIPECAT_PROXY_HOST` to `.env`

```bash
# Persistent tunnel by default; choose number interactively
python setup_ngrok_twilio.py

# Or pick a specific number and auto-launch the bot
python setup_ngrok_twilio.py --to +15551234567 --launch-bot
```

Environment:
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` required
- `NGROK_AUTHTOKEN` recommended for reliability
- `NGROK_REGION` optional (e.g. `us`)

After it prints the public URL, start the bot in another terminal (if you didn't use --launch-bot):

```bash
python bot.py --transport twilio --proxy <ngrok-host>
```