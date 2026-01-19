"""
Twilio Call Initiation Service for Sigmoix AI Voice Agent

This module provides functionality to initiate outbound calls through Twilio
when users click the "Talk to Agent" button on the frontend.
"""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from dotenv import load_dotenv
import logging
from typing import Dict, Optional

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
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", "+16592468685")  # Default Twilio number
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("Missing Twilio credentials. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        
        self.client = Client(self.account_sid, self.auth_token)
        logger.info("Twilio Call Service initialized successfully")
    
    def initiate_call(self, to_number: str, webhook_url: str) -> Dict:
        """
        Initiate an outbound call to the specified number.
        
        Args:
            to_number: The phone number to call (in E.164 format)
            webhook_url: The webhook URL for handling the call
            
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
            
            logger.info(f"Initiating call from {self.twilio_phone_number} to {to_number}")
            
            # Create the call
            call = self.client.calls.create(
                to=to_number,
                from_=self.twilio_phone_number,
                url=webhook_url,
                method='POST',
                status_callback=f"{webhook_url.replace('/start', '/end')}",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
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
    
    def get_call_status(self, call_sid: str) -> Dict:
        """
        Get the status of a specific call.
        
        Args:
            call_sid: The Twilio call SID
            
        Returns:
            Dictionary with call status information
        """
        try:
            call = self.client.calls(call_sid).fetch()
            
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None
            }
            
        except TwilioException as e:
            logger.error(f"Error fetching call status: {str(e)}")
            return {
                "success": False,
                "error": f"Error fetching call status: {str(e)}"
            }
    
    def list_recent_calls(self, limit: int = 10) -> Dict:
        """
        List recent calls made through this service.
        
        Args:
            limit: Maximum number of calls to return
            
        Returns:
            Dictionary with list of recent calls
        """
        try:
            calls = self.client.calls.list(limit=limit)
            
            call_list = []
            for call in calls:
                call_list.append({
                    "call_sid": call.sid,
                    "to": call.to,
                    "from": call.from_,
                    "status": call.status,
                    "start_time": call.start_time.isoformat() if call.start_time else None,
                    "duration": call.duration
                })
            
            return {
                "success": True,
                "calls": call_list,
                "count": len(call_list)
            }
            
        except TwilioException as e:
            logger.error(f"Error listing calls: {str(e)}")
            return {
                "success": False,
                "error": f"Error listing calls: {str(e)}"
            }


# Global service instance
_twilio_service: Optional[TwilioCallService] = None

def get_twilio_service() -> TwilioCallService:
    """Get or create the global Twilio service instance"""
    global _twilio_service
    if _twilio_service is None:
        _twilio_service = TwilioCallService()
    return _twilio_service


def initiate_voice_agent_call(phone_number: str) -> Dict:
    """
    Convenient function to initiate a call to the Sigmoix AI Voice Agent.
    
    Args:
        phone_number: The phone number to call
        
    Returns:
        Dictionary with call result
    """
    # Get the webhook URL from environment or construct it
    webhook_base = os.getenv("PIPECAT_PROXY_HOST", "localhost:8765")
    if not webhook_base.startswith(("http://", "https://")):
        if "localhost" in webhook_base:
            webhook_url = f"http://{webhook_base}/webhook/twilio/start"
        else:
            webhook_url = f"https://{webhook_base}/webhook/twilio/start"
    else:
        webhook_url = f"{webhook_base}/webhook/twilio/start"
    
    service = get_twilio_service()
    result = service.initiate_call(phone_number, webhook_url)
    
    if result["success"]:
        logger.info(f"Voice agent call initiated to {phone_number}")
    else:
        logger.error(f"Failed to initiate voice agent call: {result['error']}")
    
    return result


if __name__ == "__main__":
    # Test the service
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python twilio_call_service.py <phone_number>")
        print("Example: python twilio_call_service.py +1234567890")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    result = initiate_voice_agent_call(phone_number)
    
    if result["success"]:
        print(f"✅ Call initiated successfully!")
        print(f"Call SID: {result['call_sid']}")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
    else:
        print(f"❌ Failed to initiate call:")
        print(f"Error: {result['error']}")