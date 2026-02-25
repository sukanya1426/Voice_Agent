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

// Path to the Python executable in the virtual environment
const pythonPath = path.join(__dirname, '../venv/bin/python');

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
        const { phoneNumber, language } = req.body;
        const lang = language || 'en';

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

        console.log(`📞 Initiating Sigmoix AI Voice Agent call to ${cleanPhoneNumber} (Language: ${lang})...`);

        // Call the Python Twilio service to initiate the call
        const pythonProcess = spawn(pythonPath, [
            path.join(__dirname, 'twilio_call_service.py'),
            cleanPhoneNumber,
            lang
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

        let responsesSent = false;
        let timeoutId;

        pythonProcess.on('close', (code) => {
            if (!responsesSent) {
                responsesSent = true;
                clearTimeout(timeoutId);
                
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
            }
        });

        // Add timeout for the process
        timeoutId = setTimeout(() => {
            if (!responsesSent) {
                responsesSent = true;
                pythonProcess.kill('SIGKILL');
                res.status(500).json({
                    success: false,
                    error: 'Call initiation timeout',
                    message: 'The call service is taking too long to respond'
                });
            }
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

// Test product search endpoint with session support and language translation
app.post('/api/test-search', async (req, res) => {
    try {
        const { query, sessionId, language } = req.body;

        if (!query) {
            return res.status(400).json({
                error: 'Search query is required'
            });
        }

        const lang = language || 'en';
        console.log(`🔍 Search query: "${query}", Session: ${sessionId || 'new'}, Language: ${lang}`);

        // Create a temporary Python script to handle the search with session and translation
        const fs = require('fs');
        const tempScriptPath = path.join(__dirname, `temp_search_${Date.now()}.py`);

        const pythonScript = `
import sys
import json
import os
from openai import OpenAI
sys.path.append('${__dirname.replace(/\\/g, '/')}')

from rag_pipeline import search_products_for_voice_agent

query = """${query.replace(/"/g, '\\"')}"""
session_id = "${sessionId || ''}"
language = "${lang}"

# Initialize OpenAI client for translation
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def translate(text, target_lang):
    try:
        if target_lang == "en":
            # Enhanced prompt to ensure numbers and budgets are correctly translated to digits
            prompt = f"Translate the following Bengali shopping query to English. CRITICAL: Convert all Bengali number words (like 'পঞ্চাশ হাজার') into numeric digits (like '50000'). Return only the translated text: {text}"
        else:
            # Enhanced prompt for cheerful shopping assistant tone in Bengali with device name translation
            prompt = f"Translate the following English tech product information into very cheerful, enthusiastic, and helpful conversational Bengali. Act as a premium shopping assistant. CRITICAL: Translate or transliterate device names and technical terms (like 'Laptop', 'Processor', 'HP') into Bengali script. The entire response should be in natural Bengali script. Keep prices as they are. Return only the translated text: {text}"
            
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}", file=sys.stderr)
        return text

try:
    # 1. Translate Bengali query to English if needed
    search_query = query
    if language == "bn":
        search_query = translate(query, "en")
        print(f"Translated query: {search_query}", file=sys.stderr)

    # 2. Run RAG pipeline with English query
    result = search_products_for_voice_agent(search_query, session_id)
    
    # 3. Translate RAG response back to Bengali if needed
    final_response = result
    if language == "bn":
        final_response = translate(result, "bn")
        print(f"Translated response back to Bengali", file=sys.stderr)

    print(json.dumps({
        "success": True,
        "response": final_response,
        "sessionId": session_id if session_id else "web_" + str(hash(query))
    }))
except Exception as e:
    print(json.dumps({
        "success": False,
        "error": str(e)
    }), file=sys.stderr)
    sys.exit(1)
`;

        // Write temporary script
        fs.writeFileSync(tempScriptPath, pythonScript);

        // Execute the Python script
        const pythonProcess = spawn(pythonPath, [tempScriptPath], {
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
            // Clean up temp file
            try {
                if (fs.existsSync(tempScriptPath)) {
                    fs.unlinkSync(tempScriptPath);
                }
            } catch (e) {
                console.error('Failed to delete temp file:', e);
            }

            if (code === 0) {
                try {
                    const result = JSON.parse(outputData.trim());
                    res.json({
                        success: true,
                        query: query,
                        response: result.response,
                        sessionId: result.sessionId
                    });
                } catch (parseError) {
                    // Fallback if JSON parsing fails
                    res.json({
                        success: true,
                        query: query,
                        response: outputData.trim(),
                        sessionId: sessionId || `web_${Date.now()}`
                    });
                }
            } else {
                console.error('Python error:', errorData);
                res.status(500).json({
                    success: false,
                    error: 'Failed to search products',
                    details: errorData
                });
            }
        });

        // Timeout after 120 seconds (needed for library loading and RAG initialization)
        setTimeout(() => {
            pythonProcess.kill();
            try {
                if (fs.existsSync(tempScriptPath)) {
                    fs.unlinkSync(tempScriptPath);
                }
            } catch (e) { }
        }, 120000);

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