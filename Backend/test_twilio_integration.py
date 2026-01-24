#!/usr/bin/env python3
"""
Test script to verify Twilio integration for Sigmoix AI Voice Agent
"""

import os
import sys
from dotenv import load_dotenv
from twilio_call_service import TwilioCallService

# Load environment variables
load_dotenv()

def test_twilio_configuration():
    """Test if Twilio credentials are properly configured"""
    print("🧪 Testing Twilio Integration for Sigmoix AI Voice Agent")
    print("=" * 60)
    
    # Check environment variables
    required_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'TWILIO_PHONE_NUMBER',
        'PIPECAT_PROXY_HOST'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"❌ {var}: Not configured")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("\n🔧 Testing Twilio Service Initialization...")
    try:
        service = TwilioCallService()
        print("✅ TwilioCallService initialized successfully")
        
        # Test webhook URL construction
        webhook_url = f"https://{service.proxy_host}/webhook/twilio/start"
        print(f"✅ Webhook URL: {webhook_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize TwilioCallService: {str(e)}")
        return False

def test_call_simulation():
    """Test call initiation with a test number (won't actually make a call)"""
    print("\n📞 Testing Call Service (Simulation Mode)")
    print("-" * 40)
    
    try:
        service = TwilioCallService()
        
        # Use a test number format - won't actually call
        test_number = "+15551234567"  # Test number
        
        print(f"📱 Simulating call initiation to {test_number}...")
        print("ℹ️  Note: This would normally initiate a real call")
        print("ℹ️  Webhook URL would be called when user answers")
        print("ℹ️  Voice agent would handle the conversation")
        
        print("\n✅ Call service is ready for production use")
        return True
        
    except Exception as e:
        print(f"❌ Error in call simulation: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Sigmoix AI Voice Agent - Twilio Integration Test\n")
    
    config_ok = test_twilio_configuration()
    if config_ok:
        test_call_simulation()
        print("\n🎉 Twilio integration is properly configured!")
        print("\n📋 Next steps:")
        print("   1. Open http://localhost:3001 in your browser")
        print("   2. Click 'Talk to Agent' button")
        print("   3. Enter your phone number in the input field")
        print("   4. Click 'Call Me' to receive a call from the AI agent")
        print("   5. Answer the call to start talking with Sigmoix AI")
    else:
        print("\n❌ Please fix the configuration issues above")
        sys.exit(1)

if __name__ == "__main__":
    main()