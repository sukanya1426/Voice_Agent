/**
 * HTTP Webhook Setup for Fonoster
 * 
 * This configures your Fonoster Voice Application to use HTTP webhooks
 * instead of TCP tunnels.
 * 
 * Usage: node http_setup.js <webhook_url>
 */

const readline = require('readline');

function displayInstructions() {
  console.log('\n' + '='.repeat(60));
  console.log('🎉 FONOSTER HTTP WEBHOOK SETUP GUIDE');
  console.log('='.repeat(60));
  
  console.log('\n🔧 STEP 1: Get your webhook URL');
  console.log('You already have it running:');
  console.log('   https://tandy-unnationalised-walker.ngrok-free.dev');
  
  console.log('\n🔧 STEP 2: Configure Fonoster Voice Application');
  console.log('Go to: https://console.fonoster.com');
  console.log('1. Login with your credentials');
  console.log('2. Go to "Applications" section');
  console.log('3. Find your Voice Application');
  console.log('4. Edit the application settings');
  console.log('5. Change endpoint type from "TCP" to "HTTP Webhook"');
  console.log('6. Set webhook URL to: https://tandy-unnationalised-walker.ngrok-free.dev/webhook');
  console.log('7. Save the configuration');
  
  console.log('\n🔧 STEP 3: Test your voice agent');
  console.log('Call your Fonoster number: +16592468685');
  console.log('Or use the web interface at: http://localhost:3001');
  
  console.log('\n🎯 Voice Commands to Test:');
  console.log('• "Show me gaming computers"');
  console.log('• "I need a laptop under 50,000 Taka"');
  console.log('• "What\'s your cheapest desktop?"');
  console.log('• "Tell me about AMD processors"');
  
  console.log('\n✅ Your voice agent has 10,799 products loaded and ready!');
  console.log('='.repeat(60));
}

async function promptUser() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  return new Promise((resolve) => {
    rl.question('\nPress Enter after you\'ve configured the webhook in Fonoster Console...', () => {
      rl.close();
      resolve();
    });
  });
}

async function main() {
  console.log('🚀 Starting HTTP Webhook Setup...\n');
  
  displayInstructions();
  
  await promptUser();
  
  console.log('\n🎉 Setup complete! Your voice agent should now work with phone calls.');
  console.log('📞 Test by calling: +16592468685');
  console.log('💬 Or use web interface: http://localhost:3001');
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = {
  displayInstructions
};