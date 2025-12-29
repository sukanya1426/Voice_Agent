/**
 * Fonoster Setup Helper
 * 
 * This replaces setup_ngrok_twilio.py for Fonoster.
 * It starts ngrok TCP tunnel for your Fonoster Voice Application.
 * 
 * Usage: node fonoster_setup.js
 */

const { spawn } = require('child_process');
const { Command } = require('commander');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

function updateEnvFile(key, value, envPath = '.env') {
  try {
    let envContent = '';
    
    // Read existing .env file
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }
    
    const lines = envContent.split('\n');
    let keyFound = false;
    
    // Update existing key or add new one
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].startsWith(`${key}=`)) {
        lines[i] = `${key}=${value}`;
        keyFound = true;
        break;
      }
    }
    
    if (!keyFound) {
      lines.push(`${key}=${value}`);
    }
    
    // Write back to file
    fs.writeFileSync(envPath, lines.join('\n'));
    console.log(`✅ Updated ${key} in ${envPath}`);
    
  } catch (error) {
    console.error(`❌ Failed to update ${envPath}:`, error.message);
  }
}

async function startNgrokTCP(port = 50061) {
  return new Promise((resolve, reject) => {
    console.log(`🚀 Starting ngrok TCP tunnel for port ${port}...`);
    
    // Check if ngrok is installed
    const ngrok = spawn('ngrok', ['tcp', port.toString()], {
      stdio: ['ignore', 'pipe', 'pipe']
    });
    
    let ngrokOutput = '';
    
    ngrok.stdout.on('data', (data) => {
      const output = data.toString();
      ngrokOutput += output;
      
      // Look for the public URL in the output
      const urlMatch = output.match(/tcp:\/\/([a-zA-Z0-9.-]+:\d+)/);
      if (urlMatch) {
        const publicUrl = urlMatch[1];
        console.log(`✅ ngrok TCP tunnel active: tcp://${publicUrl}`);
        resolve(publicUrl);
      }
    });
    
    ngrok.stderr.on('data', (data) => {
      const error = data.toString();
      console.error('ngrok error:', error);
      
      if (error.includes('command not found') || error.includes('not recognized')) {
        reject(new Error('ngrok is not installed. Please install ngrok first: https://ngrok.com/download'));
      }
    });
    
    ngrok.on('error', (error) => {
      reject(new Error(`Failed to start ngrok: ${error.message}`));
    });
    
    ngrok.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`ngrok process exited with code ${code}`));
      }
    });
    
    // Timeout after 30 seconds
    setTimeout(() => {
      if (!resolve.called) {
        reject(new Error('Timeout waiting for ngrok to start'));
      }
    }, 30000);
  });
}

async function startVoiceApp() {
  return new Promise((resolve, reject) => {
    console.log('🤖 Starting Fonoster Voice Application...');
    
    const voiceApp = spawn('node', ['fonoster_bot.js'], {
      stdio: ['ignore', 'pipe', 'pipe']
    });
    
    voiceApp.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('Voice App:', output.trim());
      
      if (output.includes('Listening on tcp://')) {
        console.log('✅ Voice Application is running');
        resolve(voiceApp);
      }
    });
    
    voiceApp.stderr.on('data', (data) => {
      console.error('Voice App Error:', data.toString());
    });
    
    voiceApp.on('error', (error) => {
      reject(new Error(`Failed to start voice application: ${error.message}`));
    });
    
    voiceApp.on('close', (code) => {
      console.log(`Voice application exited with code ${code}`);
    });
    
    // Timeout after 10 seconds
    setTimeout(() => {
      resolve(voiceApp);
    }, 10000);
  });
}

function displayInstructions(publicUrl) {
  console.log('\n' + '='.repeat(60));
  console.log('🎉 FONOSTER VOICE APPLICATION SETUP COMPLETE!');
  console.log('='.repeat(60));
  console.log(`📞 Your Voice Application is accessible at: tcp://${publicUrl}`);
  console.log('\n📋 Next Steps:');
  console.log('1. Configure your Fonoster account to use this TCP endpoint');
  console.log('2. Deploy your Voice Application to Fonoster');
  console.log('3. Update FONOSTER_APP_REF in your .env file');
  console.log('\n🔧 For outbound calls:');
  console.log(`   node fonoster_outbound.js --to +DESTINATION --from +YOUR_NUMBER`);
  console.log('\n🌐 Fonoster Console: https://console.fonoster.com');
  console.log('\n💡 Make sure to install Node.js dependencies:');
  console.log('   npm install @fonoster/sdk @fonoster/voice commander dotenv openai');
  console.log('\n⚠️  Keep this terminal running to maintain the ngrok tunnel');
  console.log('='.repeat(60));
}

async function main(options) {
  try {
    console.log('🚀 Starting Fonoster development setup...\n');
    
    // Check if required files exist
    if (!fs.existsSync('fonoster_bot.js')) {
      console.error('❌ fonoster_bot.js not found. Make sure you have the Voice Application file.');
      process.exit(1);
    }
    
    // Start ngrok TCP tunnel
    let publicUrl;
    try {
      publicUrl = await startNgrokTCP(options.port);
    } catch (error) {
      console.error('❌ Failed to start ngrok:', error.message);
      process.exit(1);
    }
    
    // Update .env file with the ngrok URL
    if (options.updateEnv) {
      updateEnvFile('FONOSTER_PUBLIC_TCP_URL', `tcp://${publicUrl}`);
    }
    
    // Start Voice Application if requested
    if (options.startApp) {
      try {
        await startVoiceApp();
      } catch (error) {
        console.error('❌ Failed to start Voice Application:', error.message);
        console.log('💡 You can start it manually with: node fonoster_bot.js');
      }
    }
    
    // Display instructions
    displayInstructions(publicUrl);
    
    // Keep running
    if (options.keepRunning) {
      console.log('\n🔄 Press Ctrl+C to stop...\n');
      
      // Handle graceful shutdown
      process.on('SIGINT', () => {
        console.log('\n👋 Shutting down...');
        process.exit(0);
      });
      
      // Keep the process alive
      setInterval(() => {
        // Do nothing, just keep alive
      }, 60000);
    }
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    process.exit(1);
  }
}

// Command line interface
const program = new Command();

program
  .name('fonoster-setup')
  .description('Setup ngrok TCP tunnel for Fonoster Voice Application')
  .version('1.0.0');

program
  .option('-p, --port <number>', 'Port for Voice Application (default: 50061)', '50061')
  .option('--no-update-env', 'Do not update .env file with ngrok URL')
  .option('--no-start-app', 'Do not start the Voice Application')
  .option('--no-keep-running', 'Exit after setup instead of keeping tunnel active')
  .action(async (options) => {
    options.port = parseInt(options.port);
    await main(options);
  });

program.parse();

// If run directly without arguments, use defaults
if (process.argv.length === 2) {
  main({
    port: 50061,
    updateEnv: true,
    startApp: true,
    keepRunning: true
  });
}