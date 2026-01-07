/**
 * Fonoster Voice Application - Sigmoix AI Product Inquiry Bot (HTTP Webhook Version)
 * 
 * This handles voice calls for product inquiries using CSV product data via HTTP webhooks.
 * Customers can call and ask about products, specifications, pricing, etc.
 * 
 * Run with: node fonoster_bot_http.js
 * Expose with: ngrok http 50062
 */

const express = require('express');
const { VoiceResponse } = require("@fonoster/voice");
const path = require('path');

// AI Service imports and CSV parsing
const OpenAI = require('openai');
const fs = require('fs');
const csv = require('csv-parser');
require('dotenv').config();

// Initialize Express app
const app = express();
const PORT = 50062;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Initialize AI services
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || process.env.CEREBRAS_API_KEY,
  baseURL: process.env.CEREBRAS_API_KEY ? "https://api.cerebras.ai/v1" : undefined
});

// Conversation context storage (in production, use a database)
const conversations = new Map();

// Product data storage
let productData = [];

// CSV Loading Functions
async function loadProductData() {
  const products = [];
  const csvPath = path.join(__dirname, 'products_merged.csv');
  
  return new Promise((resolve, reject) => {
    fs.createReadStream(csvPath)
      .pipe(csv())
      .on('data', (data) => products.push(data))
      .on('end', () => {
        console.log(`✅ Loaded ${products.length} products from CSV`);
        resolve(products);
      })
      .on('error', reject);
  });
}

// Product search function
function searchProducts(query) {
  if (!productData || productData.length === 0) {
    return [];
  }
  
  const searchTerms = query.toLowerCase();
  const results = [];
  
  for (const product of productData) {
    const productString = `${product.name} ${product.category} ${product.description || ''} ${product.price || ''}`.toLowerCase();
    
    if (productString.includes(searchTerms) || 
        searchTerms.split(' ').some(term => productString.includes(term))) {
      results.push(product);
      
      if (results.length >= 5) break; // Limit to 5 results for voice readability
    }
  }
  
  return results;
}

// Format product information for voice
function formatProductInfo(products) {
  if (!products || products.length === 0) {
    return "I couldn't find any products matching your criteria. Could you please be more specific or try different search terms?";
  }
  
  if (products.length === 1) {
    const product = products[0];
    return `I found ${product.name} for ${product.price || 'price on request'}. ${product.description || 'This is a great choice for your needs.'}`;
  }
  
  let response = `I found ${products.length} products for you. Here are the top options: `;
  
  products.slice(0, 3).forEach((product, index) => {
    response += `${index + 1}. ${product.name} for ${product.price || 'price on request'}. `;
  });
  
  if (products.length > 3) {
    response += `And ${products.length - 3} more options available. `;
  }
  
  return response;
}

// AI Response Generation
async function getAIResponse(sessionRef, userInput) {
  try {
    let context = conversations.get(sessionRef) || [];
    
    context.push({ role: 'user', content: userInput });
    
    const systemMessage = {
      role: 'system',
      content: `You are a helpful assistant for Sigmoix AI, a technology company specializing in computers and electronics. 
      Help customers with product inquiries, technical questions, and general information. 
      Keep responses conversational and under 50 words for voice calls.
      If asked about products, encourage them to be specific about what they're looking for.`
    };
    
    const messages = [systemMessage, ...context.slice(-4)]; // Keep last 4 exchanges
    
    const completion = await openai.chat.completions.create({
      model: process.env.CEREBRAS_API_KEY ? "llama3.1-8b" : "gpt-3.5-turbo",
      messages: messages,
      max_tokens: 100,
      temperature: 0.7,
    });
    
    const response = completion.choices[0].message.content.trim();
    
    context.push({ role: 'assistant', content: response });
    conversations.set(sessionRef, context);
    
    return response;
  } catch (error) {
    console.error('AI Response Error:', error);
    return "I'm here to help you find great technology products. What are you looking for today?";
  }
}

// Product inquiry handler
async function handleProductInquiry(userInput, sessionRef) {
  try {
    // Extract product search terms from the input
    const searchResults = searchProducts(userInput);
    const responseMessage = formatProductInfo(searchResults);
    
    // If products were found, add follow-up
    let fullResponse = responseMessage;
    if (searchResults.length > 0) {
      fullResponse += " Would you like to hear more details about any specific product, or would you like me to search for something else?";
    }
    
    return fullResponse;
    
  } catch (error) {
    console.error('Product inquiry error:', error);
    return "I'm having trouble searching our product catalog right now. Please try again or call back later.";
  }
}

// HTTP Webhook Endpoints

// Main webhook endpoint for incoming calls
app.post('/webhook', async (req, res) => {
  const { sessionRef, callerNumber, ingressNumber, event } = req.body;
  
  console.log(`📞 Webhook: ${event} - Session: ${sessionRef}, From: ${callerNumber}, To: ${ingressNumber}`);
  console.log('📦 Full request body:', JSON.stringify(req.body, null, 2));
  
  try {
    // Create VoiceML response for Fonoster
    let voiceml = '';
    
    if (event === 'call_start' || event === 'session_started') {
      voiceml = `
        <VoiceML>
          <Say>Hello! Welcome to Sigmoix AI. I'm here to help you find the perfect technology products from our catalog of over 10,000 items. What are you looking for today?</Say>
          <Gather source="speech" timeout="10000" webhook="/webhook/input">
            <Say>Please tell me what product you're interested in.</Say>
          </Gather>
        </VoiceML>
      `;
    } else {
      voiceml = `
        <VoiceML>
          <Say>Thank you for calling Sigmoix AI. Goodbye!</Say>
          <Hangup/>
        </VoiceML>
      `;
    }
    
    console.log('📤 Sending VoiceML response:', voiceml);
    
    res.type('application/xml');
    res.send(voiceml.trim());
    
  } catch (error) {
    console.error('❌ Webhook error:', error);
    
    const errorResponse = `
      <VoiceML>
        <Say>I apologize for the technical difficulty. Please call back. Thank you for choosing Sigmoix AI.</Say>
        <Hangup/>
      </VoiceML>
    `;
    
    res.type('application/xml');
    res.send(errorResponse.trim());
  }
});

// Input handling webhook
app.post('/webhook/input', async (req, res) => {
  const { sessionRef, speech } = req.body;
  
  console.log(`👤 Caller said: "${speech}"`);
  console.log('📦 Input request body:', JSON.stringify(req.body, null, 2));
  
  try {
    let voiceml = '';
    
    if (speech && speech.trim()) {
      const lowerInput = speech.toLowerCase();
      
      // Check if caller wants to end call
      if (lowerInput.includes('goodbye') || lowerInput.includes('thank you') || lowerInput.includes('bye')) {
        voiceml = `
          <VoiceML>
            <Say>Thank you for calling Sigmoix AI! Have a wonderful day!</Say>
            <Hangup/>
          </VoiceML>
        `;
        
        // Clean up conversation context
        conversations.delete(sessionRef);
        
      } else if (lowerInput.includes('looking for') || lowerInput.includes('search') || lowerInput.includes('find') || 
                 lowerInput.includes('product') || lowerInput.includes('computer') || lowerInput.includes('gaming') ||
                 lowerInput.includes('desktop') || lowerInput.includes('laptop') || lowerInput.includes('ryzen') ||
                 lowerInput.includes('intel') || lowerInput.includes('price') || lowerInput.includes('specification')) {
        
        // Handle product inquiry
        const productResponse = await handleProductInquiry(speech, sessionRef);
        voiceml = `
          <VoiceML>
            <Say>${productResponse}</Say>
            <Gather source="speech" timeout="10000" webhook="/webhook/input">
              <Say>What else would you like to know about our products?</Say>
            </Gather>
          </VoiceML>
        `;
        
      } else {
        // General AI conversation
        const aiResponse = await getAIResponse(sessionRef, speech);
        console.log(`🤖 AI Response: "${aiResponse}"`);
        voiceml = `
          <VoiceML>
            <Say>${aiResponse}</Say>
            <Gather source="speech" timeout="10000" webhook="/webhook/input">
              <Say>How else can I help you?</Say>
            </Gather>
          </VoiceML>
        `;
      }
      
    } else {
      // Handle silence
      voiceml = `
        <VoiceML>
          <Say>I'm still here. How else can I help you with our technology products?</Say>
          <Gather source="speech" timeout="10000" webhook="/webhook/input">
            <Say>Please tell me what you're looking for.</Say>
          </Gather>
        </VoiceML>
      `;
    }
    
    console.log('📤 Sending input VoiceML response:', voiceml);
    
    res.type('application/xml');
    res.send(voiceml.trim());
    
  } catch (error) {
    console.error('❌ Input handling error:', error);
    
    const errorResponse = `
      <VoiceML>
        <Say>I didn't catch that. Could you please repeat your question about our products?</Say>
        <Gather source="speech" timeout="10000" webhook="/webhook/input">
          <Say>I'm here to help.</Say>
        </Gather>
      </VoiceML>
    `;
    
    res.type('application/xml');
    res.send(errorResponse.trim());
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Fonoster HTTP Voice Bot is running',
    products_loaded: productData.length,
    timestamp: new Date().toISOString()
  });
});

// Initialize and start server
async function startServer() {
  try {
    // Load product data
    productData = await loadProductData();
    
    // Start HTTP server
    app.listen(PORT, () => {
      console.log('🚀 Fonoster HTTP Voice Application starting...');
      console.log(`📞 HTTP Webhook server running on http://localhost:${PORT}`);
      console.log(`🌐 Expose with: ngrok http ${PORT}`);
      console.log('📋 Webhook endpoints:');
      console.log(`   - POST /webhook (main call handler)`);
      console.log(`   - POST /webhook/input (input handler)`);
      console.log(`   - GET /health (health check)`);
      console.log('🤖 Sigmoix AI Product Inquiry Bot is ready!');
    });
    
  } catch (error) {
    console.error('❌ Failed to load product data:', error);
    console.log('⚠️  Bot will start without product data - please check products_merged.csv file');
    
    // Start server anyway
    app.listen(PORT, () => {
      console.log('⚠️  Server started without product data');
      console.log(`📞 HTTP Webhook server running on http://localhost:${PORT}`);
      console.log(`🌐 Expose with: ngrok http ${PORT}`);
    });
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down Fonoster HTTP Voice Bot...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Shutting down Fonoster HTTP Voice Bot...');
  process.exit(0);
});

// Start the server
startServer();