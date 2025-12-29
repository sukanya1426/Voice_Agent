/**
 * Fonoster Voice Application - Restaurant Receptionist Bot
 * 
 * This replaces the Twilio/Pipecat bot.py with a Fonoster Voice Application
 * that handles both inbound and outbound calls for The Salusbury restaurant.
 * 
 * Run with: node fonoster_bot.js
 * Expose with: ngrok tcp 50061
 */

const VoiceServer = require("@fonoster/voice").default;
const { 
  GatherSource, 
  VoiceRequest, 
  VoiceResponse 
} = require("@fonoster/voice");

// AI Service imports (you'll need to install these)
const OpenAI = require('openai');
require('dotenv').config();

// Initialize AI services
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || process.env.CEREBRAS_API_KEY,
  baseURL: process.env.CEREBRAS_API_KEY ? "https://api.cerebras.ai/v1" : undefined
});

// Conversation context storage (in production, use a database)
const conversations = new Map();

// Restaurant availability checker (mock function)
async function checkAvailability(date, time, partySize) {
  // Simulate checking availability
  await new Promise(resolve => setTimeout(resolve, 1000));
  return {
    available: true,
    message: `Great! I have a table available for ${partySize} on ${date} at ${time}. Your reservation is confirmed!`
  };
}

// AI conversation handler
async function getAIResponse(sessionRef, userInput) {
  // Get or create conversation context
  let context = conversations.get(sessionRef) || [];
  
  // System prompt for restaurant receptionist
  if (context.length === 0) {
    context.push({
      role: "system", 
      content: `You are a receptionist for a London based PUB/RESTAURANT called The Salusbury. You are on a phone call and the user's input comes from speech transcription, so account for potential errors. Respond naturally, concisely, and conversationally since your response will be spoken aloud.

Your goal is to help customers with:
1. General restaurant information
2. Table reservations (ask for date, time, and party size)
3. Menu inquiries
4. Operating hours

When taking reservations, collect all required information before confirming. Be friendly and professional.

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

// Main Voice Application
new VoiceServer().listen(async (req: VoiceRequest, voice: VoiceResponse) => {
  console.log(`📞 New call - Session: ${req.sessionRef}, From: ${req.callerNumber}, To: ${req.ingressNumber}`);
  
  try {
    // Answer the call
    await voice.answer();
    
    // Welcome message
    await voice.say("Thank you for calling The Salusbury! How can I help you today?");
    
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
            await voice.say("Thank you for calling The Salusbury! Have a wonderful day!");
            conversationActive = false;
            break;
          }
          
          // Check if this is a reservation request
          if (lowerInput.includes('reservation') || lowerInput.includes('table') || lowerInput.includes('book')) {
            await handleReservation(voice, req.sessionRef, result.speech);
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
      await voice.say("Thank you for calling The Salusbury. Goodbye!");
    }
    
  } catch (error) {
    console.error('Call error:', error);
    await voice.say("I apologize for the technical difficulty. Please call back. Goodbye.");
  } finally {
    // Clean up conversation context
    conversations.delete(req.sessionRef);
    await voice.hangup();
    console.log(`📞 Call ended - Session: ${req.sessionRef}`);
  }
});

// Handle reservation flow
async function handleReservation(voice, sessionRef, initialInput) {
  console.log('📅 Starting reservation flow');
  
  // Extract any reservation details from initial input
  let date = null, time = null, partySize = null;
  
  // Simple parsing (you might want to use a more sophisticated NLP approach)
  const dateRegex = /(\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2}|tomorrow|today|next \w+day)/i;
  const timeRegex = /(\d{1,2}:?\d{0,2}\s*(?:am|pm|AM|PM)|\d{1,2}\s*(?:am|pm|AM|PM))/i;
  const sizeRegex = /(\d+)\s*(?:people|person|guests?|seats?)/i;
  
  const dateMatch = initialInput.match(dateRegex);
  const timeMatch = initialInput.match(timeRegex);
  const sizeMatch = initialInput.match(sizeRegex);
  
  if (dateMatch) date = dateMatch[1];
  if (timeMatch) time = timeMatch[1];
  if (sizeMatch) partySize = parseInt(sizeMatch[1]);
  
  // Collect missing information
  if (!date) {
    await voice.say("What date would you like to make a reservation for?");
    const dateResult = await voice.gather({ source: GatherSource.SPEECH, timeout: 10000 });
    date = dateResult.speech;
  }
  
  if (!time) {
    await voice.say("What time would you prefer?");
    const timeResult = await voice.gather({ source: GatherSource.SPEECH, timeout: 10000 });
    time = timeResult.speech;
  }
  
  if (!partySize) {
    await voice.say("How many people will be dining?");
    const sizeResult = await voice.gather({ source: GatherSource.SPEECH, timeout: 10000 });
    partySize = parseInt(sizeResult.speech) || sizeResult.speech;
  }
  
  // Confirm details
  await voice.say(`Let me check availability for ${partySize} people on ${date} at ${time}.`);
  
  // Check availability (mock)
  try {
    const availability = await checkAvailability(date, time, partySize);
    await voice.say(availability.message);
  } catch (error) {
    console.error('Reservation error:', error);
    await voice.say("I'm having trouble checking availability right now. Please call back or try our online reservation system.");
  }
}

console.log('🚀 Fonoster Voice Application starting...');
console.log('📞 Listening on tcp://127.0.0.1:50061');
console.log('🌐 Expose with: ngrok tcp 50061');
console.log('🍽️  The Salusbury Restaurant Receptionist Bot is ready!');