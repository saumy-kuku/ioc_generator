import os
import asyncio
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import httpx

from a2a.client import A2AClient
from a2a.client.card_resolver import A2ACardResolver
from a2a.types import (
    SendStreamingMessageRequest, 
    MessageSendParams, 
    Message, 
    Part, 
    TextPart, 
    Role,
    SendStreamingMessageSuccessResponse,
    JSONRPCErrorResponse
)
from a2a.utils.message import get_message_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="KukuTV Ad Script Generator API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    prompt: str | None = None
    episode_summary: str | None = None
    peak_moments: list[str] | None = None

@app.post("/api/generate-script")
async def generate_script(request: GenerateRequest):
    """
    Client-facing endpoint that triggers the A2A Pipeline.
    """
    # Construct prompt from available fields
    if request.episode_summary and request.peak_moments:
        full_prompt = f"Episode Summary: {request.episode_summary}\nPeak Moments: {', '.join(request.peak_moments)}"
    else:
        full_prompt = request.prompt or "Generic script request"

    print(f"\n>>> [DEBUG] Received request. Constructed prompt: {full_prompt[:50]}...")
    port = os.getenv("A2A_SERVER_PORT", "9999")
    agent_url = f"http://localhost:{port}/"
    
    try:
        print(f">>> [DEBUG] Connecting to A2A Agent at {agent_url}...")
        logger.info(f"Connecting to A2A Agent at {agent_url}...")
        
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            # 1. Resolve Agent Card
            resolver = A2ACardResolver(httpx_client=http_client, base_url=agent_url)
            # Correct method name is get_agent_card()
            agent_card = await resolver.get_agent_card()
            print(f">>> [DEBUG] Agent Card resolved: {agent_card.name}")
            
            # 2. Initialize A2AClient
            client = A2AClient(httpx_client=http_client, agent_card=agent_card)
            print(">>> [DEBUG] A2AClient initialized.")

            # 3. Prepare Payload
            send_message_payload = {
                'message': {
                    'role': Role.user,
                    'parts': [{'kind': 'text', 'text': full_prompt}],
                    'messageId': uuid.uuid4().hex,
                },
            }
            
            streaming_request = SendStreamingMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(**send_message_payload)
            )

            # 4. Consume stream
            messages = []
            print(">>> [DEBUG] Sending message & starting stream consumption...")
            
            # client.send_message_streaming returns an AsyncGenerator
            async for chunk in client.send_message_streaming(streaming_request):
                # chunk is SendStreamingMessageResponse
                resp = chunk.root
                
                if isinstance(resp, JSONRPCErrorResponse):
                    error_detail = resp.error.message
                    print(f">>> [DEBUG] A2A Error Response: {error_detail}")
                    raise HTTPException(status_code=500, detail=f"A2A Error: {error_detail}")
                
                # resp is SendStreamingMessageSuccessResponse
                result = resp.result
                if isinstance(result, Message):
                    text = get_message_text(result)
                    print(f">>> [DEBUG] Received Message: {text[:50]}...")
                    messages.append(text)
                elif hasattr(result, 'status') and hasattr(result.status, 'state'):
                    # For TaskStatusUpdateEvent or Task objects with status
                    print(f">>> [DEBUG] Task Progress: {result.status.state}")
                else:
                    print(f">>> [DEBUG] Received other event type: {type(result)}")

            print(f">>> [DEBUG] Stream consumption finished. Total messages: {len(messages)}")
            
            if not messages:
                print(">>> [DEBUG] ERROR: No messages received!")
                raise HTTPException(status_code=500, detail="No output received from agent")

            # The last message enqueued by PipelineHost is the comprehensive final output
            final_text = messages[-1]
            print(f">>> [DEBUG] Final text length: {len(final_text)}")

            return {
                "script": final_text,
                "genre": "kukufm_drama",
                "speaker_format": "multi_speaker" if "Multi-Speaker" in final_text else "single_speaker"
            }

    except Exception as e:
        logger.error(f"Error calling A2A Agent: {str(e)}", exc_info=True)
        print(f">>> [DEBUG] EXCEPTION in main.py: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
