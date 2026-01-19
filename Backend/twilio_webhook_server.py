"""
Twilio Webhook Server for Sigmoix AI Voice Agent

This server handles incoming Twilio webhook requests and establishes
websocket connections for the voice agent pipeline.
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
        call_sid = form_data.get("CallSid", "")
        from_number = form_data.get("From", "")
        to_number = form_data.get("To", "")
        
        logger.info(f"Incoming call - CallSid: {call_sid}, From: {from_number}, To: {to_number}")
        
        # Get the base URL for WebSocket connection
        # In production, this should be your ngrok URL or domain
        base_url = os.getenv("PIPECAT_PROXY_HOST", "localhost:8765")
        
        # Ensure the base URL has the right protocol
        if not base_url.startswith(("ws://", "wss://")):
            if "localhost" in base_url:
                ws_url = f"ws://{base_url}/ws"
            else:
                ws_url = f"wss://{base_url}/ws"
        else:
            ws_url = f"{base_url}/ws"
        
        # Return TwiML to establish WebSocket connection
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="CallSid" value="{call_sid}" />
            <Parameter name="From" value="{from_number}" />
            <Parameter name="To" value="{to_number}" />
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
    <Say>Sorry, there was an error connecting to our voice agent. Please try again later.</Say>
</Response>"""
        return Response(
            content=error_twiml,
            media_type="application/xml"
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint that connects to the voice agent pipeline.
    This is where Twilio streams audio for processing.
    """
    await websocket.accept()
    
    try:
        logger.info("WebSocket connection established for voice agent")
        
        # Run the voice agent bot with websocket
        await bot(websocket)
        
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        await websocket.close(code=1000)


@app.post("/webhook/twilio/end")
async def twilio_webhook_end(request: Request):
    """
    Twilio webhook endpoint for call end events (optional).
    """
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid", "")
        call_status = form_data.get("CallStatus", "")
        
        logger.info(f"Call ended - CallSid: {call_sid}, Status: {call_status}")
        
        return {"status": "acknowledged"}
        
    except Exception as e:
        logger.error(f"Error handling call end webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8765))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Sigmoix AI Voice Agent Webhook Server on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "twilio_webhook_server:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )