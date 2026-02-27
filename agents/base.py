from abc import ABC
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message, get_message_text
import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)


class GeminiAgentExecutor(AgentExecutor):
    def __init__(self, system_instruction: str):
        self.system_instruction = system_instruction
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )

    async def run_logic(self, user_input: str) -> str:
        """Helper for internal orchestration by PipelineHost."""
        logger.info(f"GeminiAgentExecutor: run_logic() with input: {user_input[:50]}...")
        try:
            response = await self.model.generate_content_async(user_input)
            logger.info("GeminiAgentExecutor: run_logic() received response from model")
            return response.text
        except Exception as e:
            logger.error(f"GeminiAgentExecutor: Error in run_logic: {str(e)}", exc_info=True)
            raise

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        SDK 0.3.x direct execution handler.
        """
        logger.info(f"GeminiAgentExecutor.execute() started for task: {context.task_id}")
        try:
            # BUG FIX #4: Use get_message_text(context.message) instead of context.get_user_input()
            user_input = get_message_text(context.message) if context.message else None
            if not user_input:
                logger.warning("No user input received")
                return

            logger.info(f"Calling Gemini model with input: {user_input[:50]}...")
            response = await self.model.generate_content_async(user_input)
            text_response = response.text
            logger.info(f"Gemini responded. Length: {len(text_response)}")

            # BUG FIX #1: new_agent_text_message only accepts `text` — remove task_id/context_id
            msg = new_agent_text_message(text=text_response)
            await event_queue.enqueue_event(msg)

        except Exception as e:
            logger.error(f"Error executing agent: {str(e)}")
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
