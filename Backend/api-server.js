/**
 * Backend API Server for Sigmoix AI Voice Agent
 * 
 * This Express server provides API endpoints for the frontend to communicate
 * with the Twilio-based voice agent system using Python bot integration.
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const { spawn } = require('child_process');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Serve frontend files
app.use(express.static(path.join(__dirname, '../Frontend')));

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        message: 'Sigmoix AI Backend Server is running',
        timestamp: new Date().toISOString(),
        service: 'voice_agent_api'
    });
});

// Initiate call endpoint - Updated to use Twilio directly
app.post('/api/initiate-call', async (req, res) => {
    try {
        const { phoneNumber } = req.body;
        
        // Validate request
        if (!phoneNumber) {
            return res.status(400).json({
                error: 'Phone number is required'
            });
        }
        
        // Clean and validate phone number format (basic E.164 validation)
        const cleanPhoneNumber = phoneNumber.trim();
        const e164Regex = /^\+[1-9]\d{1,14}$/;
        if (!e164Regex.test(cleanPhoneNumber)) {
            return res.status(400).json({
                error: 'Phone number must be in E.164 format (e.g., +1234567890)'
            });
        }
        
        console.log(`📞 Initiating Sigmoix AI Voice Agent call to ${cleanPhoneNumber}...`);
        
        // Call the Python Twilio service to initiate the call
        const pythonProcess = spawn('python3', [
            path.join(__dirname, 'twilio_call_service.py'),
            cleanPhoneNumber
        ], {
            cwd: __dirname,
            env: { ...process.env }
        });
        
        let outputData = '';
        let errorData = '';
        
        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            errorData += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0) {
                console.log('✅ Call initiated successfully');
                res.json({
                    success: true,
                    message: 'Call initiated successfully! You should receive a call from Sigmoix AI shortly.',
                    phoneNumber: cleanPhoneNumber,
                    timestamp: new Date().toISOString()
                });
            } else {
                console.error('❌ Failed to initiate call:', errorData);
                res.status(500).json({
                    success: false,
                    error: 'Failed to initiate call',
                    details: errorData || 'Unknown error occurred'
                });
            }
        });
        
        // Add timeout for the process
        setTimeout(() => {
            pythonProcess.kill('SIGKILL');
            res.status(500).json({
                success: false,
                error: 'Call initiation timeout',
                message: 'The call service is taking too long to respond'
            });
        }, 30000); // 30 seconds timeout
        
    } catch (error) {
        console.error('Error in /api/initiate-call:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error',
            message: 'Failed to process call request'
        });
    }
});

// Get call status endpoint
app.get('/api/call-status/:callSid', async (req, res) => {
    try {
        const { callSid } = req.params;
        
        // Here you could add logic to check call status via Twilio API
        // For now, return a simple response
        res.json({
            success: true,
            callSid: callSid,
            message: 'Call status check not implemented yet'
        });
        
    } catch (error) {
        console.error('Error checking call status:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to check call status'
        });
    }
});

// Test product search endpoint
app.post('/api/test-search', async (req, res) => {
    try {
        const { query } = req.body;
        
        if (!query) {
            return res.status(400).json({
                error: 'Search query is required'
            });
        }
        
        // Test the RAG pipeline directly
        const pythonProcess = spawn('python3', ['-c', `
import sys
sys.path.append('${__dirname}')
from rag_pipeline import search_products_for_voice_agent
result = search_products_for_voice_agent('${query}')
print(result)
        `]);
        
        let outputData = '';
        let errorData = '';
        
        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            errorData += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0) {
                res.json({
                    success: true,
                    query: query,
                    response: outputData.trim()
                });
            } else {
                res.status(500).json({
                    success: false,
                    error: 'Failed to search products',
                    details: errorData
                });
            }
        });
        
    } catch (error) {
        console.error('Error in product search test:', error);
        res.status(500).json({
            success: false,
            error: 'Internal server error'
        });
    }
});

// Serve the main frontend page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../Frontend/index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        success: false,
        error: 'Something went wrong!',
        message: 'Internal server error'
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint not found',
        message: `Cannot ${req.method} ${req.path}`
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Sigmoix AI Backend Server running on http://localhost:${PORT}`);
    console.log(`📱 Frontend available at: http://localhost:${PORT}`);
    console.log(`🏥 Health check: http://localhost:${PORT}/api/health`);
    
    // Log environment status
    console.log('\n📋 Environment Status:');
    console.log(`   Deepgram API: ${process.env.DEEPGRAM_API_KEY ? '✅ Configured' : '❌ Missing'}`);
    console.log(`   Cartesia API: ${process.env.CARTESIA_API_KEY ? '✅ Configured' : '❌ Missing'}`);
    console.log(`   Cerebras API: ${process.env.CEREBRAS_API_KEY ? '✅ Configured' : '❌ Missing'}`);
    console.log(`   OpenAI API: ${process.env.OPENAI_API_KEY ? '✅ Configured' : '❌ Missing'}`);
    console.log(`   Twilio SID: ${process.env.TWILIO_ACCOUNT_SID ? '✅ Configured' : '❌ Missing'}`);
    console.log(`   Twilio Token: ${process.env.TWILIO_AUTH_TOKEN ? '✅ Configured' : '❌ Missing'}`);
    console.log(`   Ngrok Host: ${process.env.PIPECAT_PROXY_HOST ? '✅ Configured' : '❌ Missing'}`);
});

module.exports = app;