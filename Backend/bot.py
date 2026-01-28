

"""Sigmoix AI Voice Agent with RAG Pipeline Integration.

The Sigmoix AI Voice Agent is a comprehensive voice assistant that helps customers
find technology products through natural conversation. It integrates:
- Deepgram (Speech-to-Text)
- Cerebras/OpenAI (LLM with RAG)
- Cartesia (Text-to-Speech)
- Custom RAG pipeline for product search

The agent connects via Twilio websocket for phone calls and provides
intelligent product recommendations based on customer queries.

Run the bot using::

    python bot.py -t twilio -x your_ngrok.ngrok.io
"""

import os
import asyncio
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.services.ai_services import FunctionEntry
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

# Import our custom RAG pipeline
from rag_pipeline import search_products_for_voice_agent, get_product_details_for_voice_agent, initialize_rag_pipeline

# Load environment variables (API keys, Twilio, etc.)
load_dotenv(override=True)

# Initialize RAG pipeline on startup
logger.info("Initializing RAG pipeline...")
initialize_rag_pipeline()
logger.info("RAG pipeline initialized successfully")


async def run_bot(transport: BaseTransport):
    logger.info(f"Starting Sigmoix AI Voice Agent")

    # STT: transcribe caller audio to text (Deepgram)
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    # TTS: convert assistant text to speech (Cartesia)
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="5c42302c-194b-4d0c-ba1a-8cb485c84ab9",  # Professional, friendly voice
    )

    # LLM: generate responses and call tools (Cerebras or OpenAI)
    cerebras_api_key = os.getenv("CEREBRAS_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if cerebras_api_key:
        llm = OpenAILLMService(
            api_key=cerebras_api_key, 
            model="llama3.1-8b", 
            base_url="https://api.cerebras.ai/v1"
        )
        logger.info("Using Cerebras LLM")
    elif openai_api_key:
        llm = OpenAILLMService(
            api_key=openai_api_key, 
            model="gpt-4o-mini"
        )
        logger.info("Using OpenAI LLM")
    else:
        raise ValueError("No valid LLM API key found")

    # System prompt for Sigmoix AI Voice Agent
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    messages = [
        {
            "role": "system",
            "content": f"""You are the Sigmoix AI Voice Agent, a helpful and knowledgeable assistant specializing in technology products. You are currently on a phone call with a customer.

IMPORTANT GUIDELINES:
1. You are speaking over the phone, so keep responses conversational and concise
2. Always be friendly, professional, and helpful
3. When customers ask about products, use the search_products function to find relevant items
4. For specific product details, use the get_product_details function
5. Speak naturally as your responses will be converted to speech
6. Don't use markdown formatting or complex punctuation in voice responses
7. Keep responses under 150 words for better voice delivery
8. Always offer to help with follow-up questions
9. Remember previous conversations to provide contextual responses
10. Be proactive in understanding customer needs and budget constraints

CONVERSATION MEMORY:
- You can remember the last 10 questions and answers from this customer
- Use this context to provide better, more personalized recommendations
- Reference previous questions when relevant to show you're listening

Your main capabilities:
- Search for technology products (laptops, desktops, gaming PCs, processors, etc.)
- Provide detailed product information including prices and specifications  
- Make personalized recommendations based on customer needs and budget
- Remember customer preferences throughout the conversation
- Answer questions about product availability, warranties, and comparisons

PRODUCT EXPERTISE:
- We have laptops from 50,000৳ to 300,000৳+ 
- Gaming laptops typically start from 80,000৳
- Desktop PCs offer better value, starting from 25,000৳
- All products come with manufacturer warranties
- We specialize in AMD Ryzen, Intel, and gaming systems

Current date and time: {now}

Remember: You represent Sigmoix AI, a premium technology product assistant. Always maintain a professional yet friendly tone and provide value-driven recommendations.""",
        },
    ]

    # Tools: functions the LLM can call for product search and details
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_products",
                "description": "Search for technology products based on customer query. Use this when customers ask about finding, looking for, or want to see products.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The customer's search query or product requirements",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_product_details",
                "description": "Get detailed information about a specific product. Use this when customers ask for more details about a particular product.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "The name of the product to get details for",
                        },
                    },
                    "required": ["product_name"],
                },
            },
        }
    ]

    # LLM context and aggregator (manages messages and tool calls)
    context = OpenAILLMContext(messages, tools=tools, tool_choice="auto")

    # Register function handlers for tool calls
    async def search_products(params):
        """Handle product search requests"""
        try:
            query = params.args.get("query", "")
            logger.info(f"Searching products for query: {query}")
            
            # Use our RAG pipeline to search products
            result = search_products_for_voice_agent(query)
            
            await params.result_callback({"response": result})
            logger.info("Product search completed successfully")
            
        except Exception as e:
            logger.error(f"Error in product search: {str(e)}")
            await params.result_callback({
                "response": "I'm having trouble searching for products right now. Could you please try again or be more specific about what you're looking for?"
            })

    async def get_product_details(params):
        """Handle product detail requests"""
        try:
            product_name = params.args.get("product_name", "")
            logger.info(f"Getting details for product: {product_name}")
            
            # Use our RAG pipeline to get product details
            result = get_product_details_for_voice_agent(product_name)
            
            await params.result_callback({"response": result})
            logger.info("Product details retrieved successfully")
            
        except Exception as e:
            logger.error(f"Error getting product details: {str(e)}")
            await params.result_callback({
                "response": "I'm having trouble getting the product details right now. Could you please specify the product name more clearly?"
            })

    # Register the functions with the LLM
    llm.register_function("search_products", search_products)
    llm.register_function("get_product_details", get_product_details)
    context_aggregator = llm.create_context_aggregator(context)

    # RTVI: normalize and route frames/events between steps
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Define the realtime pipeline: audio in -> STT -> LLM -> TTS -> audio out
    pipeline = Pipeline(
        [
            # Receive audio and events from Twilio
            transport.input(),
            # Route/format frames and propagate events
            rtvi,
            # Speech recognition (caller audio -> text)
            stt,
            # Add user text to the LLM conversation context
            context_aggregator.user(),
            # Generate assistant reply (and optional tool calls)
            llm,
            # Synthesize reply to audio (text -> speech)
            tts,
            # Send audio back to the caller
            transport.output(),
            # Save assistant speech to context for continuity
            context_aggregator.assistant(),
        ]
    )

    # Task: run pipeline with audio settings and metrics enabled
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected to Sigmoix AI Voice Agent")
        # Send the Sigmoix AI greeting when a call connects
        greeting_message = {
            "role": "system", 
            "content": "Greet the caller with: 'Hello from Sigmoix AI! I'm your technology product assistant. Tell me what you're looking for and I'll help you find the perfect product.'"
        }
        messages.append(greeting_message)
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected from Sigmoix AI Voice Agent")
        # On disconnect: stop the pipeline task
        await task.cancel()

    # Run the pipeline
    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


async def bot(websocket):
    """Main bot entry point for the bot starter."""

    # Use websocket directly - assume Twilio transport
    logger.info("Using Twilio transport for voice agent")
    
    # For Twilio, we'll extract call data from websocket messages if needed
    call_data = {
        "stream_id": "default_stream",
        "call_id": "default_call"
    }

    # Twilio serializer: attach call identifiers and credentials
    serializer = TwilioFrameSerializer(
        stream_sid=call_data["stream_id"],
        call_sid=call_data["call_id"],
        account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
    )

    # Transport: FastAPI WebSocket with audio in/out, VAD, and serialization
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(),
            serializer=serializer,
        ),
    )

    # Start the bot using this transport
    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    # CLI entrypoint
    main()