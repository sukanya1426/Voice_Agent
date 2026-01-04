/**
 * Fonoster Voice Application - Sigmoix AI Product Inquiry Bot
 * 
 * This handles voice calls for product inquiries using CSV product data.
 * Customers can call and ask about products, specifications, pricing, etc.
 * 
 * Run with: node fonoster_bot.js
 * Expose with: ngrok tcp 50061
 */

const { VoiceServer } = require("@fonoster/voice");
const { 
  GatherSource, 
  VoiceRequest, 
  VoiceResponse 
} = require("@fonoster/voice");

// AI Service imports and CSV parsing
const OpenAI = require('openai');
const fs = require('fs');
const csv = require('csv-parser');
require('dotenv').config();

// Initialize AI services
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || process.env.CEREBRAS_API_KEY,
  baseURL: process.env.CEREBRAS_API_KEY ? "https://api.cerebras.ai/v1" : undefined
});

// Conversation context storage (in production, use a database)
const conversations = new Map();

// Product data storage
let productData = [];

// Load product data from CSV
async function loadProductData() {
  return new Promise((resolve, reject) => {
    const products = [];
    fs.createReadStream('products_merged.csv')
      .pipe(csv())
      .on('data', (row) => {
        // Clean and structure the product data
        products.push({
          name: row.name || '',
          price: row.price || '',
          category: row.category || '',
          description: row.description || '',
          key_features: row.key_features || '',
          specifications: row.specifications || '',
          brand: row.brand || '',
          url: row.url || ''
        });
      })
      .on('end', () => {
        console.log(`✅ Loaded ${products.length} products from CSV`);
        resolve(products);
      })
      .on('error', reject);
  });
}

// Search products based on query
function searchProducts(query, limit = 5) {
  const searchTerm = query.toLowerCase();
  const matches = productData.filter(product => 
    product.name.toLowerCase().includes(searchTerm) ||
    product.category.toLowerCase().includes(searchTerm) ||
    product.description.toLowerCase().includes(searchTerm) ||
    product.key_features.toLowerCase().includes(searchTerm) ||
    (product.brand && product.brand.toLowerCase().includes(searchTerm))
  );
  
  return matches.slice(0, limit);
}

// Format product information for voice response
function formatProductInfo(products) {
  if (products.length === 0) {
    return "I couldn't find any products matching your query. Could you try a different search term?";
  }
  
  if (products.length === 1) {
    const product = products[0];
    return `I found the ${product.name}. It's priced at ${product.price}. ${product.description.substring(0, 200)}... Would you like to know more about its specifications or features?`;
  }
  
  let response = `I found ${products.length} products that match your query:\n`;
  products.forEach((product, index) => {
    response += `${index + 1}. ${product.name} - ${product.price}\n`;
  });
  response += "Which one would you like to know more about?";
  
  return response;
}

// AI conversation handler
async function getAIResponse(sessionRef, userInput) {
  // Get or create conversation context
  let context = conversations.get(sessionRef) || [];
  
  // System prompt for product inquiry assistant
  if (context.length === 0) {
    context.push({
      role: "system", 
      content: `You are a product inquiry assistant for Sigmoix AI. You help customers find and learn about technology products from our extensive catalog. You are on a phone call and the user's input comes from speech transcription, so account for potential errors. Respond naturally, concisely, and conversationally since your response will be spoken aloud.

Your goal is to help customers with:
1. Product searches and recommendations
2. Specifications and features
3. Pricing information
4. Product comparisons
5. General product inquiries

When customers ask about products, use the search_products function to find relevant items. Be helpful, knowledgeable, and professional. Always try to understand what the customer is looking for and provide relevant product suggestions.

Current date/time: ${new Date().toISOString()}`
    });
  }
  
  // Add user input
  context.push({ role: "user", content: userInput });
  
  try {
    const completion = await openai.chat.completions.create({
      model: process.env.CEREBRAS_API_KEY ? "qwen-3-235b-a22b-instruct-2507" : "gpt-4",
      messages: context,
      max_tokens: 150,
      temperature: 0.7
    });
    
    const response = completion.choices[0].message.content;
    
    // Add AI response to context
    context.push({ role: "assistant", content: response });
    
    // Store updated context
    conversations.set(sessionRef, context);
    
    return response;
  } catch (error) {
    console.error('AI API Error:', error);
    return "I apologize, I'm having technical difficulties. Please try again or call us back.";
  }
}

// Handle product inquiry flow
async function handleProductInquiry(voice, sessionRef, initialInput) {
  console.log('🔍 Starting product inquiry flow');
  
  try {
    // Extract product search terms from the input
    const searchResults = searchProducts(initialInput);
    const responseMessage = formatProductInfo(searchResults);
    
    await voice.say(responseMessage);
    
    // If products were found, offer more details
    if (searchResults.length > 0) {
      await voice.say("Would you like to hear more details about any specific product, or would you like me to search for something else?");
    }
    
  } catch (error) {
    console.error('Product inquiry error:', error);
    await voice.say("I'm having trouble searching our product catalog right now. Please try again or call back later.");
  }
}

// Main Voice Application
new VoiceServer().listen(async (req, voice) => {
  console.log(`📞 New call - Session: ${req.sessionRef}, From: ${req.callerNumber}, To: ${req.ingressNumber}`);
  
  try {
    // Answer the call
    await voice.answer();
    
    // Welcome message
    await voice.say("Hello! Welcome to Sigmoix AI. I'm here to help you find the perfect technology products. What are you looking for today?");
    
    // Main conversation loop
    let conversationActive = true;
    let silenceCount = 0;
    const maxSilence = 3;
    
    while (conversationActive && silenceCount < maxSilence) {
      try {
        // Gather speech input from caller
        const result = await voice.gather({
          source: GatherSource.SPEECH,
          timeout: 10000, // 10 second timeout
          maxSilence: 3000 // 3 seconds of silence
        });
        
        if (result.speech && result.speech.trim()) {
          console.log(`👤 Caller said: "${result.speech}"`);
          silenceCount = 0; // Reset silence counter
          
          // Check if caller wants to end call
          const lowerInput = result.speech.toLowerCase();
          if (lowerInput.includes('goodbye') || lowerInput.includes('thank you') || lowerInput.includes('bye')) {
            await voice.say("Thank you for calling Sigmoix AI! Have a wonderful day!");
            conversationActive = false;
            break;
          }
          
          // Check if this is a product search request
          if (lowerInput.includes('looking for') || lowerInput.includes('search') || lowerInput.includes('find') || 
              lowerInput.includes('product') || lowerInput.includes('computer') || lowerInput.includes('gaming') ||
              lowerInput.includes('desktop') || lowerInput.includes('laptop') || lowerInput.includes('ryzen') ||
              lowerInput.includes('intel') || lowerInput.includes('price') || lowerInput.includes('specification')) {
            await handleProductInquiry(voice, req.sessionRef, result.speech);
          } else {
            // General AI conversation
            const aiResponse = await getAIResponse(req.sessionRef, result.speech);
            console.log(`🤖 AI Response: "${aiResponse}"`);
            await voice.say(aiResponse);
          }
          
        } else {
          // Handle silence
          silenceCount++;
          console.log(`🔇 Silence detected (${silenceCount}/${maxSilence})`);
          
          if (silenceCount === 1) {
            await voice.say("I'm still here. How else can I help you?");
          } else if (silenceCount === 2) {
            await voice.say("Are you still there? Please let me know how I can assist you.");
          }
        }
        
      } catch (gatherError) {
        console.error('Gather error:', gatherError);
        silenceCount++;
        
        if (silenceCount < maxSilence) {
          await voice.say("I didn't catch that. Could you please repeat?");
        }
      }
    }
    
    // End call due to silence
    if (silenceCount >= maxSilence) {
      await voice.say("Thank you for calling Sigmoix AI. Goodbye!");
    }
    
  } catch (error) {
    console.error('Call error:', error);
    await voice.say("I apologize for the technical difficulty. Please call back. Thank you for choosing Sigmoix AI.");
  } finally {
    // Clean up conversation context
    conversations.delete(req.sessionRef);
    await voice.hangup();
    console.log(`📞 Call ended - Session: ${req.sessionRef}`);
  }
});

// Initialize product data on startup
(async () => {
  try {
    productData = await loadProductData();
    console.log('🚀 Fonoster Voice Application starting...');
    console.log('📞 Listening on tcp://127.0.0.1:50061');
    console.log('🌐 Expose with: ngrok tcp 50061');
    console.log('🤖 Sigmoix AI Product Inquiry Bot is ready!');
  } catch (error) {
    console.error('❌ Failed to load product data:', error);
    console.log('⚠️  Bot will start without product data - please check products_merged.csv file');
  }
})();