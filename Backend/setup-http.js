/**
 * HTTP-based Setup Helper (Alternative to TCP)
 * 
 * This uses ngrok HTTP tunnel instead of TCP for free accounts
 * Note: This is for development only - production should use direct Fonoster deployment
 */

const { spawn } = require('child_process');
const express = require('express');
require('dotenv').config();

let voiceApp = null;

// Create a simple HTTP wrapper for the voice application
function createHTTPWrapper() {
    const app = express();
    app.use(express.json());
    
    // Webhook endpoint that Fonoster can call
    app.post('/webhook', (req, res) => {
        console.log('📞 Received webhook from Fonoster:', req.body);
        
        // In a real implementation, you'd forward this to your voice application
        // For now, return a simple TwiML-style response
        res.type('application/xml').send(`
            <Response>
                <Say voice="alice">Hello! Welcome to Sigmoix AI. I'm here to help you find technology products. What are you looking for today?</Say>
                <Gather input="speech" timeout="10" action="/process-speech">
                    <Say voice="alice">Please tell me what product you're interested in.</Say>
                </Gather>
            </Response>
        `);
    });
    
    app.post('/process-speech', (req, res) => {
        const userInput = req.body.SpeechResult || 'No speech detected';
        console.log('🎤 User said:', userInput);
        
        // Simple product search simulation
        let response = "I heard you're looking for products. ";
        if (userInput.toLowerCase().includes('gaming') || userInput.toLowerCase().includes('computer')) {
            response += "I found some great gaming computers. The AMD Ryzen 5 7500F Gaming PC is available for 93,900 Taka with excellent performance.";
        } else if (userInput.toLowerCase().includes('laptop')) {
            response += "We have several laptops available. What's your budget range?";
        } else {
            response += "Could you please be more specific about what type of technology product you're looking for?";
        }
        
        res.type('application/xml').send(`
            <Response>
                <Say voice="alice">${response}</Say>
                <Gather input="speech" timeout="10" action="/process-speech">
                    <Say voice="alice">What else can I help you find?</Say>
                </Gather>
            </Response>
        `);
    });
    
    const PORT = 8080;
    app.listen(PORT, () => {
        console.log(`🎯 HTTP Voice Wrapper running on port ${PORT}`);
    });
    
    return PORT;
}

async function startNgrokHTTP(port = 8080) {
    return new Promise((resolve, reject) => {
        console.log(`🌐 Starting ngrok HTTP tunnel for port ${port}...`);
        
        const ngrok = spawn('/Users/mahdiya/Sigmoix_AI/Voice_Agent/Backend/ngrok', ['http', port.toString()], {
            stdio: ['ignore', 'pipe', 'pipe']
        });
        
        let ngrokOutput = '';
        
        ngrok.stdout.on('data', (data) => {
            const output = data.toString();
            ngrokOutput += output;
            
            // Look for the public URL
            const urlMatch = output.match(/https:\/\/([a-zA-Z0-9-]+\.ngrok(?:-free)?\.app)/);
            if (urlMatch) {
                const publicUrl = urlMatch[0];
                console.log(`✅ ngrok HTTP tunnel active: ${publicUrl}`);
                resolve(publicUrl);
            }
        });
        
        ngrok.stderr.on('data', (data) => {
            const error = data.toString();
            if (!error.includes('level=info')) {
                console.error('ngrok error:', error);
            }
        });
        
        ngrok.on('error', (error) => {
            reject(new Error(`Failed to start ngrok: ${error.message}`));
        });
        
        // Timeout after 30 seconds
        setTimeout(() => {
            reject(new Error('Timeout waiting for ngrok HTTP to start'));
        }, 30000);
    });
}

async function main() {
    try {
        console.log('🚀 Starting HTTP-based development setup...\n');
        
        // Start HTTP wrapper
        const port = createHTTPWrapper();
        
        // Start ngrok HTTP tunnel
        const publicUrl = await startNgrokHTTP(port);
        
        console.log('\n' + '='.repeat(60));
        console.log('🎉 HTTP SETUP COMPLETE (FREE ACCOUNT COMPATIBLE)!');
        console.log('='.repeat(60));
        console.log(`🌐 Your webhook URL: ${publicUrl}/webhook`);
        console.log('\n📋 Next Steps:');
        console.log('1. Go to Fonoster Console');
        console.log('2. Configure your phone number webhook to:');
        console.log(`   ${publicUrl}/webhook`);
        console.log('3. Test by calling your Fonoster number');
        console.log('\n💡 Note: This is a simplified version for free accounts');
        console.log('For full functionality, consider upgrading ngrok or use production deployment');
        console.log('\n⚠️  Keep this terminal running to maintain the tunnel');
        console.log('='.repeat(60));
        
        // Keep running
        process.on('SIGINT', () => {
            console.log('\n👋 Shutting down...');
            process.exit(0);
        });
        
        // Keep alive
        setInterval(() => {}, 60000);
        
    } catch (error) {
        console.error('❌ Setup failed:', error.message);
        console.log('\n💡 Alternative: Run without ngrok:');
        console.log('   npm run server  # Start API server only');
        console.log('   npm start       # Start voice agent locally');
        process.exit(1);
    }
}

main();