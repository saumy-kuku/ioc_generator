import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import httpx

from a2a.client import A2AClient, ClientFactory
from a2a.client.card_resolver import A2ACardResolver
from a2a.types import (
    SendStreamingMessageRequest,
    MessageSendParams,
    Message,
    Part,
    TextPart,
    Role,
    JSONRPCErrorResponse,
)
from a2a.utils.message import get_message_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="KukuTV Ad Script Generator API")

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
    if request.episode_summary and request.peak_moments:
        full_prompt = (
            f"Episode Summary: {request.episode_summary}\n"
            f"Peak Moments: {', '.join(request.peak_moments)}"
        )
    else:
        full_prompt = request.prompt or "Generic script request"

    logger.info(f"Received request. Prompt: {full_prompt[:80]}...")

    port = os.getenv("A2A_SERVER_PORT", "9999")
    agent_url = f"http://localhost:{port}/"

    try:
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            # 1. Resolve Agent Card
            resolver = A2ACardResolver(httpx_client=http_client, base_url=agent_url)
            agent_card = await resolver.get_agent_card()
            logger.info(f"Agent Card resolved: {agent_card.name}")

            # 2. Initialize client via ClientFactory (A2AClient is deprecated)
            client = await ClientFactory.create_client(httpx_client=http_client, agent_card=agent_card)

            # BUG FIX #5: Use proper Part/TextPart objects, not raw dicts
            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=full_prompt))],
                messageId=uuid.uuid4().hex,
            )

            streaming_request = SendStreamingMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(message=message)
            )

            # 4. Consume stream — collect all Message chunks
            all_messages = []
            logger.info("Sending message and consuming stream...")

            async for chunk in client.send_message_streaming(streaming_request):
                resp = chunk.root

                if isinstance(resp, JSONRPCErrorResponse):
                    error_detail = resp.error.message
                    logger.error(f"A2A Error Response: {error_detail}")
                    raise HTTPException(status_code=500, detail=f"A2A Error: {error_detail}")

                result = resp.result
                if isinstance(result, Message):
                    text = get_message_text(result)
                    logger.info(f"Stream chunk received: {text[:80]}...")
                    all_messages.append(text)
                elif hasattr(result, "status") and hasattr(result.status, "state"):
                    logger.info(f"Task state update: {result.status.state}")
                else:
                    logger.debug(f"Received event: {type(result).__name__}")

            logger.info(f"Stream finished. Total chunks received: {len(all_messages)}")

            if not all_messages:
                raise HTTPException(status_code=500, detail="No output received from agent pipeline")

            # Progress messages are like "[1/5]...", final output is the last (and longest) message
            final_text = max(all_messages, key=len)

            return {
                "script": final_text,
                "genre": "kukufm_drama",
                "speaker_format": "multi_speaker" if "Multi-Speaker" in final_text else "single_speaker",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling A2A Agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
