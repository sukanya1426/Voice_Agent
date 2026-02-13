"""
Twilio Call Initiation Service for Sigmoix AI Voice Agent

This module provides functionality to initiate outbound calls through Twilio
when users click the "Talk to Agent" button on the frontend.
"""

import os
import sys
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from dotenv import load_dotenv
import logging
from typing import Dict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwilioCallService:
    """Service for managing Twilio calls for the Sigmoix AI Voice Agent"""
    
    def __init__(self):
        """Initialize the Twilio client with credentials from environment"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", "+16592468685")
        self.proxy_host = os.getenv("PIPECAT_PROXY_HOST") or os.getenv("NGROK_HOST")
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("Missing Twilio credentials. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        
        if not self.proxy_host:
            raise ValueError("Missing PIPECAT_PROXY_HOST or NGROK_HOST for webhook URL")
        
        self.client = Client(self.account_sid, self.auth_token)
        logger.info("Twilio Call Service initialized successfully")
    
    def initiate_call(self, to_number: str, language: str = 'en') -> Dict:
        """
        Initiate an outbound call to the specified number.
        
        Args:
            to_number: The phone number to call (in E.164 format)
            language: The preferred language ('en' or 'bn')
            
        Returns:
            Dictionary with call information or error details
        """
        try:
            # Validate phone number format
            if not to_number.startswith('+'):
                return {
                    "success": False,
                    "error": "Phone number must be in E.164 format (e.g., +1234567890)"
                 }
            
            # Construct webhook URL for the voice agent with language param
            webhook_url = f"https://{self.proxy_host}/webhook/twilio/start?language={language}"
            
            logger.info(f"Initiating call from {self.twilio_phone_number} to {to_number} (Language: {language})")
            logger.info(f"Using webhook URL: {webhook_url}")
            
            # Create the call
            call = self.client.calls.create(
                to=to_number,
                from_=self.twilio_phone_number,
                url=webhook_url,
                method='POST'
            )
            
            logger.info(f"Call initiated successfully - SID: {call.sid}")
            
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "to": to_number,
                "from": self.twilio_phone_number,
                "message": "Call initiated successfully. You should receive a call shortly."
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error initiating call: {str(e)}")
            return {
                "success": False,
                "error": f"Twilio error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error initiating call: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }


if __name__ == "__main__":
    """
    Standalone script to initiate a call from command line or API server
    Usage: python twilio_call_service.py <phone_number> [language]
    """
    if len(sys.argv) < 2:
        print("Usage: python twilio_call_service.py <phone_number> [language]")
        print("Example: python twilio_call_service.py +1234567890 bn")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'en'
    
    try:
        service = TwilioCallService()
        result = service.initiate_call(phone_number, language)
        
        if result["success"]:
            print("✅ Call initiated successfully!")
            print(f"Call SID: {result['call_sid']}")
            print(f"Status: {result['status']}")
            print(f"From: {result['from']}")  
            print(f"To: {result['to']}")
            print(f"Message: {result['message']}")
        else:
            print("❌ Call initiation failed!")
            print(f"Error: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)