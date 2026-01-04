/**
 * Backend API Server for Sigmoix AI Voice Agent
 * 
 * This Express server provides API endpoints for the frontend to communicate
 * with the Fonoster voice agent system.
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Import Fonoster SDK for outbound calls
const SDK = require("@fonoster/sdk");

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
        timestamp: new Date().toISOString()
    });
});

// Initiate call endpoint
app.post('/api/initiate-call', async (req, res) => {
    try {
        const { to, from } = req.body;
        
        // Validate request
        if (!to || !from) {
            return res.status(400).json({
                error: 'Both "to" and "from" phone numbers are required'
            });
        }
        
        // Validate phone number format (basic E.164 validation)
        const e164Regex = /^\+[1-9]\d{1,14}$/;
        if (!e164Regex.test(to) || !e164Regex.test(from)) {
            return res.status(400).json({
                error: 'Phone numbers must be in E.164 format (e.g., +1234567890)'
            });
        }
        
        console.log(`📞 Initiating call from ${from} to ${to}...`);
        
        // Initialize Fonoster client
        const apiKey = process.env.FONOSTER_API_KEY;
        const apiSecret = process.env.FONOSTER_API_SECRET;
        const accessKeyId = process.env.FONOSTER_ACCESS_KEY_ID;
        const appRef = process.env.FONOSTER_APP_REF;
        
        if (!apiKey || !apiSecret || !accessKeyId) {
            return res.status(500).json({
                error: 'Missing Fonoster credentials in server configuration'
            });
        }
        
        if (!appRef) {
            return res.status(500).json({
                error: 'Missing FONOSTER_APP_REF in server configuration'
            });
        }
        
        // Create and authenticate Fonoster client
        const client = new SDK.Client({ accessKeyId });
        await client.loginWithApiKey(apiKey, apiSecret);
        
        // Prepare call request
        const callRequest = {
            from: from,
            to: to,
            appRef: appRef,
            metadata: {
                callType: 'outbound',
                timestamp: new Date().toISOString(),
                purpose: 'product_inquiry',
                source: 'frontend_web_app'
            }
        };
        
        // Create the call via Fonoster
        const calls = new SDK.Calls(client);
        const response = await calls.createCall(callRequest);
        
        console.log('✅ Call initiated successfully:', response.callId || response.id);
        
        res.json({
            success: true,
            callId: response.callId || response.id || 'unknown',
            message: 'Call initiated successfully',
            to: to,
            from: from,
            status: response.status || 'initiated'
        });
        
    } catch (error) {
        console.error('❌ Call initiation failed:', error.message);
        
        let errorMessage = 'Failed to initiate call';
        let statusCode = 500;
        
        // Handle specific errors
        if (error.message.includes('authentication') || error.message.includes('unauthorized')) {
            errorMessage = 'Fonoster authentication failed. Check API credentials.';
            statusCode = 401;
        } else if (error.message.includes('app') || error.message.includes('application')) {
            errorMessage = 'Voice Application not found. Check FONOSTER_APP_REF.';
            statusCode = 404;
        } else if (error.message.includes('phone') || error.message.includes('number')) {
            errorMessage = 'Invalid phone number format.';
            statusCode = 400;
        }
        
        res.status(statusCode).json({
            error: errorMessage,
            details: error.message
        });
    }
});

// Get call status endpoint
app.get('/api/call-status/:callId', async (req, res) => {
    try {
        const { callId } = req.params;
        
        // In a real implementation, you would query Fonoster for call status
        // For now, we'll return a mock status
        res.json({
            callId: callId,
            status: 'active',
            duration: '00:30',
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('Error getting call status:', error.message);
        res.status(500).json({
            error: 'Failed to get call status',
            details: error.message
        });
    }
});

// End call endpoint
app.post('/api/end-call', async (req, res) => {
    try {
        const { callId } = req.body;
        
        if (!callId) {
            return res.status(400).json({
                error: 'Call ID is required'
            });
        }
        
        console.log(`📞 Ending call: ${callId}`);
        
        // In a real implementation, you would use Fonoster SDK to end the call
        // For now, we'll return a success response
        
        res.json({
            success: true,
            message: 'Call ended successfully',
            callId: callId,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('Error ending call:', error.message);
        res.status(500).json({
            error: 'Failed to end call',
            details: error.message
        });
    }
});

// Get product information endpoint (for potential future use)
app.get('/api/products', async (req, res) => {
    try {
        const { search, limit = 10 } = req.query;
        
        // In a real implementation, you would load and search the CSV data
        // For now, return mock product data
        const mockProducts = [
            {
                name: "AMD Ryzen 5 7500F Gaming PC",
                price: "৳93,900",
                category: "Desktop > Gaming PC",
                description: "High-performance gaming PC with AMD Ryzen 5 7500F processor and RTX graphics"
            },
            {
                name: "AMD Ryzen 3 3200G Desktop PC",  
                price: "৳24,499",
                category: "Desktop > Budget PC",
                description: "Affordable desktop PC perfect for office work and light gaming"
            }
        ];
        
        res.json({
            products: mockProducts,
            total: mockProducts.length,
            search: search || 'all'
        });
        
    } catch (error) {
        console.error('Error getting products:', error.message);
        res.status(500).json({
            error: 'Failed to get products',
            details: error.message
        });
    }
});

// Serve frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../Frontend', 'index.html'));
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Endpoint not found',
        path: req.originalUrl
    });
});

// Error handler
app.use((error, req, res, next) => {
    console.error('Server error:', error);
    res.status(500).json({
        error: 'Internal server error',
        message: error.message
    });
});

// Start server
app.listen(PORT, () => {
    console.log('🚀 Sigmoix AI Backend Server started');
    console.log(`📡 Server running on http://localhost:${PORT}`);
    console.log(`🌐 Frontend available at http://localhost:${PORT}`);
    console.log(`📞 API endpoints:`);
    console.log(`   - GET  /api/health`);
    console.log(`   - POST /api/initiate-call`);
    console.log(`   - GET  /api/call-status/:callId`);
    console.log(`   - POST /api/end-call`);
    console.log(`   - GET  /api/products`);
    console.log('');
    console.log('💡 Make sure your Fonoster credentials are set in .env file');
    console.log('⚠️  Remember to start your Fonoster voice agent: node fonoster_bot.js');
});