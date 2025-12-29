/**
 * Fonoster Outbound Calling Script
 * 
 * This replaces outbound.py for making outbound calls using Fonoster SDK
 * instead of Twilio client.
 * 
 * Usage: node fonoster_outbound.js --to +1234567890 --from +0987654321
 */

const SDK = require("@fonoster/sdk");
const { Command } = require('commander');
require('dotenv').config();

async function makeOutboundCall(options) {
  try {
    console.log('🚀 Initializing Fonoster SDK...');
    
    // Initialize Fonoster client
    const apiKey = process.env.FONOSTER_API_KEY;
    const apiSecret = process.env.FONOSTER_API_SECRET;
    const accessKeyId = process.env.FONOSTER_ACCESS_KEY_ID;
    const appRef = process.env.FONOSTER_APP_REF; // Your Voice Application reference
    
    if (!apiKey || !apiSecret || !accessKeyId) {
      console.error('❌ ERROR: Missing Fonoster credentials in environment variables');
      console.error('Required: FONOSTER_API_KEY, FONOSTER_API_SECRET, FONOSTER_ACCESS_KEY_ID');
      process.exit(1);
    }
    
    if (!appRef) {
      console.error('❌ ERROR: Missing FONOSTER_APP_REF in environment variables');
      console.error('This should be the reference ID of your deployed Voice Application');
      process.exit(1);
    }
    
    // Create and authenticate client
    const client = new SDK.Client({ accessKeyId });
    await client.loginWithApiKey(apiKey, apiSecret);
    console.log('✅ Authenticated with Fonoster');
    
    // Prepare call request
    const callRequest = {
      from: options.from,
      to: options.to,
      appRef: appRef,
      // Optional metadata to be sent to the Voice Application
      metadata: {
        callType: 'outbound',
        timestamp: new Date().toISOString(),
        purpose: 'restaurant_contact'
      }
    };
    
    console.log(`📞 Initiating call from ${options.from} to ${options.to}...`);
    
    // Create the call
    const calls = new SDK.Calls(client);
    const response = await calls.createCall(callRequest);
    
    console.log('✅ Call initiated successfully!');
    console.log(`📞 Call ID: ${response.callId || response.id || 'N/A'}`);
    console.log(`🎯 Target: ${options.to}`);
    console.log(`📱 From: ${options.from}`);
    console.log(`🤖 App: ${appRef}`);
    
    if (response.status) {
      console.log(`📊 Status: ${response.status}`);
    }
    
    // The person at ${options.to} should now receive a call
    // When they answer, they'll be connected to your Fonoster Voice Application
    
  } catch (error) {
    console.error('❌ Call failed:', error.message);
    
    if (error.response) {
      console.error('API Response:', error.response.data);
    }
    
    // Common error handling
    if (error.message.includes('authentication') || error.message.includes('unauthorized')) {
      console.error('\n💡 Check your Fonoster API credentials in .env file');
    } else if (error.message.includes('app') || error.message.includes('application')) {
      console.error('\n💡 Check your FONOSTER_APP_REF - make sure your Voice Application is deployed');
    } else if (error.message.includes('phone') || error.message.includes('number')) {
      console.error('\n💡 Check phone number format (should be E.164: +1234567890)');
    }
    
    process.exit(1);
  }
}

// Command line interface
const program = new Command();

program
  .name('fonoster-outbound')
  .description('Make outbound calls using Fonoster SDK')
  .version('1.0.0');

program
  .option('--to <number>', 'Destination phone number (E.164 format, e.g. +1234567890)')
  .option('--from <number>', 'Your Fonoster phone number (E.164 format)')
  .action(async (options) => {
    if (!options.to || !options.from) {
      console.error('❌ Both --to and --from phone numbers are required');
      console.log('\nExample usage:');
      console.log('  node fonoster_outbound.js --to +8801312190214 --from +16592468685');
      process.exit(1);
    }
    
    // Validate E.164 format
    const e164Regex = /^\+[1-9]\d{1,14}$/;
    if (!e164Regex.test(options.to) || !e164Regex.test(options.from)) {
      console.error('❌ Phone numbers must be in E.164 format (e.g., +1234567890)');
      process.exit(1);
    }
    
    await makeOutboundCall(options);
  });

program.parse();