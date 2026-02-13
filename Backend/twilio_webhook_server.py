"""
Simplified Twilio Webhook Server for Sigmoix AI Voice Agent
"""

import os
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, Request, Response
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv

# Import our bot
from bot import bot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Sigmoix AI Voice Agent Webhook Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Sigmoix AI Voice Agent Webhook Server is running",
        "status": "healthy",
        "service": "voice_agent_webhook"
    }


@app.post("/webhook/twilio/start")
async def twilio_webhook_start(request: Request):
    """
    Twilio webhook endpoint that handles incoming calls.
    This endpoint returns TwiML to establish a WebSocket connection.
    """
    try:
        # Get the request data
        form_data = await request.form()
        query_params = dict(request.query_params)
        language = query_params.get("language", "en")
        
        call_sid = form_data.get("CallSid", "")
        from_number = form_data.get("From", "")
        to_number = form_data.get("To", "")
        
        logger.info(f"Incoming call - CallSid: {call_sid}, From: {from_number}, To: {to_number}, Language: {language}")
        
        # Get the base URL for WebSocket connection
        base_url = os.getenv("PIPECAT_PROXY_HOST", "localhost:8765")
        
        # Construct WebSocket URL
        if "localhost" in base_url:
            ws_url = f"ws://{base_url}/ws"
        else:
            ws_url = f"wss://{base_url}/ws"
        
        # Return TwiML to establish WebSocket connection
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="CallSid" value="{call_sid}" />
            <Parameter name="From" value="{from_number}" />
            <Parameter name="To" value="{to_number}" />
            <Parameter name="Language" value="{language}" />
        </Stream>
    </Connect>
</Response>"""

        
        logger.info(f"Returning TwiML with WebSocket URL: {ws_url}")
        
        return Response(
            content=twiml_response,
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"Error handling Twilio webhook: {str(e)}")
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, there was an error connecting to the voice agent. Please try again later.</Say>
    <Hangup/>
</Response>"""
        
        return Response(
            content=error_twiml,
            media_type="application/xml"
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for handling voice agent connections.
    This is where Twilio will connect for the voice stream.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        # Run the voice bot with this websocket connection
        await bot(websocket)
    except Exception as e:
        logger.error(f"Error in voice bot: {str(e)}")
    finally:
        logger.info("WebSocket connection closed")


if __name__ == "__main__":
    # Get port from environment or default to 8765
    port = int(os.getenv("WEBHOOK_PORT", 8765))
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    
    logger.info(f"Starting Sigmoix AI Voice Agent Webhook Server on {host}:{port}")
    
    # Run with uvicorn
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info"
    )