#!/usr/bin/env python3
"""
Test script to debug Twilio call initiation issues
"""

import os
import sys
from dotenv import load_dotenv
from twilio_call_service import TwilioCallService

def main():
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN", 
        "TWILIO_PHONE_NUMBER",
        "PIPECAT_PROXY_HOST"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return
    
    print("✅ All required environment variables are set:")
    print(f"   - TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID')}")
    print(f"   - TWILIO_AUTH_TOKEN: {'*' * len(os.getenv('TWILIO_AUTH_TOKEN', ''))}")
    print(f"   - TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER')}")
    print(f"   - PIPECAT_PROXY_HOST: {os.getenv('PIPECAT_PROXY_HOST')}")
    
    # Test phone number (your Bangladesh number)
    test_phone = "+8801312190214"
    
    # Construct webhook URL
    webhook_base = os.getenv("PIPECAT_PROXY_HOST")
    webhook_url = f"https://{webhook_base}/webhook/twilio/start"
    print(f"   - Webhook URL: {webhook_url}")
    
    try:
        # Initialize Twilio service
        print("\n📞 Initializing Twilio Call Service...")
        twilio_service = TwilioCallService()
        
        # Test call initiation
        print(f"\n🚀 Testing call to {test_phone}...")
        result = twilio_service.initiate_call(test_phone, webhook_url)
        
        if result["success"]:
            print("✅ Call initiated successfully!")
            print(f"   - Call SID: {result['call_sid']}")
            print(f"   - Status: {result['status']}")
            print(f"   - From: {result['from']}")
            print(f"   - To: {result['to']}")
            print(f"   - Message: {result['message']}")
        else:
            print("❌ Call initiation failed!")
            print(f"   - Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

if __name__ == "__main__":
    main()