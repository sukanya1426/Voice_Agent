/**
 * Simplified API Server for Frontend Testing
 * 
 * This version doesn't require Fonoster SDK and is perfect for testing
 * the frontend interface without phone call functionality.
 */

const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Serve frontend files
app.use(express.static(path.join(__dirname, '../Frontend')));

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        message: 'Sigmoix AI Backend Server is running (Demo Mode)',
        timestamp: new Date().toISOString(),
        mode: 'demo'
    });
});

// Demo initiate call endpoint (simulates call without actual Fonoster)
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
        
        console.log(`📞 [DEMO] Simulating call from ${from} to ${to}...`);
        
        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Return demo success response
        const demoCallId = 'demo-call-' + Date.now();
        
        console.log('✅ [DEMO] Call simulation successful:', demoCallId);
        
        res.json({
            success: true,
            callId: demoCallId,
            message: 'Call initiated successfully (Demo Mode)',
            to: to,
            from: from,
            status: 'demo-initiated',
            note: 'This is a demo. No actual call was made. Connect Fonoster for real calls.'
        });
        
    } catch (error) {
        console.error('❌ Demo call simulation failed:', error.message);
        
        res.status(500).json({
            error: 'Failed to simulate call',
            details: error.message,
            mode: 'demo'
        });
    }
});

// Get call status endpoint (demo)
app.get('/api/call-status/:callId', async (req, res) => {
    try {
        const { callId } = req.params;
        
        res.json({
            callId: callId,
            status: 'demo-active',
            duration: '00:30',
            timestamp: new Date().toISOString(),
            note: 'This is a demo status. Connect Fonoster for real call tracking.'
        });
        
    } catch (error) {
        console.error('Error getting demo call status:', error.message);
        res.status(500).json({
            error: 'Failed to get call status',
            details: error.message
        });
    }
});

// End call endpoint (demo)
app.post('/api/end-call', async (req, res) => {
    try {
        const { callId } = req.body;
        
        if (!callId) {
            return res.status(400).json({
                error: 'Call ID is required'
            });
        }
        
        console.log(`📞 [DEMO] Ending simulated call: ${callId}`);
        
        res.json({
            success: true,
            message: 'Call ended successfully (Demo Mode)',
            callId: callId,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('Error ending demo call:', error.message);
        res.status(500).json({
            error: 'Failed to end call',
            details: error.message
        });
    }
});

// Chat endpoint for text-based product inquiries
app.post('/api/chat', async (req, res) => {
    try {
        const { message } = req.body;
        
        if (!message || typeof message !== 'string') {
            return res.status(400).json({ error: 'Message is required' });
        }
        
        console.log('💬 [DEMO] Received chat message:', message);
        
        // Simple keyword-based responses for demo
        let response = '';
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('gaming') || lowerMessage.includes('game')) {
            response = `🎮 Great choice! Here are our gaming products:\n\n• AMD Ryzen 5 7500F Gaming PC - ৳93,900\n• AMD Ryzen 5 3400G Gaming Desktop - ৳27,500\n• AMD Ryzen 5 8400F Gaming Desktop - ৳102,000\n\nThese gaming PCs offer excellent performance for all modern games. Would you like more details about any specific model?`;
        } else if (lowerMessage.includes('laptop')) {
            response = `💻 We have excellent laptops available! While our current demo focuses on desktop computers, we offer:\n\n• Gaming Laptops with RTX graphics\n• Business Laptops for professional use\n• Ultra-portable models for travel\n\nFor detailed laptop specifications and pricing, I'd recommend requesting a phone call for personalized assistance!`;
        } else if (lowerMessage.includes('desktop') || lowerMessage.includes('computer') || lowerMessage.includes('pc')) {
            response = `🖥️ Here are our desktop computers:\n\n💰 Budget-Friendly:\n• AMD Ryzen 3 3200G Desktop - ৳24,499\n• AMD Ryzen 5 3400G Gaming Desktop - ৳27,500\n\n💪 High-Performance:\n• AMD Ryzen 7 5700G Custom Desktop - ৳37,200\n• AMD Ryzen 5 7500F Gaming PC - ৳93,900\n• AMD Ryzen 5 8400F Gaming Desktop - ৳102,000\n\nWhich category interests you most?`;
        } else if (lowerMessage.includes('price') || lowerMessage.includes('budget') || lowerMessage.includes('cost') || lowerMessage.includes('cheap') || lowerMessage.includes('affordable')) {
            response = `💰 Our products range from ৳24,499 to ৳102,000+:\n\n🏷️ Budget Range (৳20,000-30,000):\n• AMD Ryzen 3 3200G Desktop - ৳24,499\n• AMD Ryzen 5 3400G Gaming Desktop - ৳27,500\n\n🏷️ Mid Range (৳30,000-60,000):\n• AMD Ryzen 7 5700G Custom Desktop - ৳37,200\n\n🏷️ Premium (৳60,000+):\n• AMD Ryzen 5 7500F Gaming PC - ৳93,900\n• AMD Ryzen 5 8400F Gaming Desktop - ৳102,000\n\nWhat's your target budget range?`;
        } else if (lowerMessage.includes('ryzen') || lowerMessage.includes('amd')) {
            response = `⚡ We specialize in AMD Ryzen processors! Here's our AMD lineup:\n\n🔥 AMD Ryzen 3 3200G - ৳24,499 (Budget-friendly)\n🔥 AMD Ryzen 5 3400G - ৳27,500 (Great for gaming)\n🔥 AMD Ryzen 7 5700G - ৳37,200 (Professional workstation)\n🔥 AMD Ryzen 5 7500F - ৳93,900 (High-end gaming)\n🔥 AMD Ryzen 5 8400F - ৳102,000 (Latest generation)\n\nRyzen processors offer excellent performance and value. Which generation interests you?`;
        } else if (lowerMessage.includes('hello') || lowerMessage.includes('hi') || lowerMessage.includes('hey') || lowerMessage.includes('start') || lowerMessage.includes('help')) {
            response = `👋 Hello! Welcome to Sigmoix AI. I'm here to help you find the perfect technology products. \n\n🛍️ Our specialties include:\n• 🖥️ Desktop Computers & Gaming PCs\n• 💻 Laptops (Business & Gaming)\n• 🎮 Gaming Systems\n• ⚡ Custom Builds with AMD Ryzen\n\nWhat type of computer are you looking for today? You can ask about gaming PCs, budget desktops, or specific price ranges!`;
        } else if (lowerMessage.includes('thank') || lowerMessage.includes('thanks')) {
            response = `🙏 You're very welcome! I'm glad I could help you with product information. \n\nIf you have more questions about specifications, availability, or need detailed technical advice, feel free to:\n• Continue chatting with me here\n• Request a phone call for personalized assistance\n\nWe're here to help you make the best choice for your needs!`;
        } else if (lowerMessage.includes('custom') || lowerMessage.includes('build') || lowerMessage.includes('configure')) {
            response = `🔧 Excellent! We love custom builds! Our AMD Ryzen 7 5700G Custom Desktop (৳37,200) is perfect for customization.\n\nCustom Build Options:\n• 🎯 Gaming-focused builds\n• 💼 Professional workstations  \n• 🎨 Content creation systems\n• 💰 Budget-optimized configurations\n\nFor detailed custom build consultation, I'd recommend requesting a phone call where we can discuss your specific requirements and create the perfect system for you!`;
        } else if (lowerMessage.includes('specification') || lowerMessage.includes('specs') || lowerMessage.includes('details')) {
            response = `📋 Here are the key specifications for our featured systems:\n\n🎮 AMD Ryzen 5 7500F Gaming PC (৳93,900):\n• Latest Ryzen 5 processor\n• Dedicated RTX graphics\n• High-speed RAM\n• Fast SSD storage\n\n💼 AMD Ryzen 7 5700G Custom Desktop (৳37,200):\n• 8-core Ryzen 7 processor\n• Integrated Radeon graphics\n• Professional-grade components\n\nFor complete detailed specifications, please request a phone call or ask about a specific model!`;
        } else {
            response = `🤔 I understand you're asking about "${message}". Let me help you with that!\n\n💡 I can assist you with:\n• 🖥️ Desktop computer recommendations\n• 🎮 Gaming PC specifications  \n• 💰 Pricing and budget options\n• ⚡ AMD Ryzen processor comparisons\n• 🔧 Custom build configurations\n\nCould you be more specific? For example:\n• "Show me gaming computers under 50,000 Taka"\n• "I need a budget desktop for office work"\n• "What's your best gaming PC?"\n\nOr request a phone call for detailed assistance!`;
        }
        
        // Simulate processing delay (realistic response time)
        await new Promise(resolve => setTimeout(resolve, Math.random() * 1500 + 800));
        
        res.json({ 
            success: true, 
            response: response,
            timestamp: new Date().toISOString(),
            mode: 'demo'
        });
        
    } catch (error) {
        console.error('❌ Chat error:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            details: error.message 
        });
    }
});

// Get product information endpoint (demo with sample data)
app.get('/api/products', async (req, res) => {
    try {
        const { search, limit = 10 } = req.query;
        
        // Sample product data from CSV
        const sampleProducts = [
            {
                name: "AMD Ryzen 5 7500F Gaming PC",
                price: "৳93,900",
                category: "Desktop > Gaming PC",
                description: "High-performance gaming PC with AMD Ryzen 5 7500F processor and RTX graphics card"
            },
            {
                name: "AMD Ryzen 3 3200G Desktop PC",  
                price: "৳24,499",
                category: "Desktop > Budget PC", 
                description: "Affordable desktop PC perfect for office work and light gaming with integrated graphics"
            },
            {
                name: "AMD Ryzen 5 3400G Gaming Desktop PC",
                price: "৳27,500", 
                category: "Desktop > Gaming PC",
                description: "Mid-range gaming PC with AMD Ryzen 5 processor and Radeon Vega graphics"
            },
            {
                name: "AMD Ryzen 5 8400F Gaming Desktop PC", 
                price: "৳102,000",
                category: "Desktop > High-end Gaming",
                description: "Premium gaming desktop with latest Ryzen processor and dedicated graphics card"
            },
            {
                name: "AMD Ryzen 7 5700G Custom Desktop PC",
                price: "৳37,200",
                category: "Desktop > Workstation", 
                description: "Powerful workstation PC with AMD Ryzen 7 processor for professional tasks"
            }
        ];
        
        // Filter products if search term provided
        let filteredProducts = sampleProducts;
        if (search) {
            filteredProducts = sampleProducts.filter(product =>
                product.name.toLowerCase().includes(search.toLowerCase()) ||
                product.category.toLowerCase().includes(search.toLowerCase()) ||
                product.description.toLowerCase().includes(search.toLowerCase())
            );
        }
        
        // Limit results
        const limitedProducts = filteredProducts.slice(0, parseInt(limit));
        
        res.json({
            products: limitedProducts,
            total: limitedProducts.length,
            search: search || 'all',
            mode: 'demo'
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
    console.log('🚀 Sigmoix AI Demo Server started');
    console.log(`📡 Server running on http://localhost:${PORT}`);
    console.log(`🌐 Frontend available at http://localhost:${PORT}`);
    console.log(`📱 API endpoints (Demo Mode):`);
    console.log(`   - GET  /api/health`);
    console.log(`   - POST /api/initiate-call (simulated)`);
    console.log(`   - POST /api/chat (text inquiries)`);
    console.log(`   - GET  /api/call-status/:callId (simulated)`);
    console.log(`   - POST /api/end-call (simulated)`);
    console.log(`   - GET  /api/products`);
    console.log('');
    console.log('🎯 Demo Mode: No actual calls will be made');
    console.log('💬 Text Chat: Fully functional with product recommendations');
    console.log('💡 Test the beautiful frontend at http://localhost:3001');
    console.log('🔧 For real calls: Fix Fonoster credentials and use api-server.js');
    console.log('');
});