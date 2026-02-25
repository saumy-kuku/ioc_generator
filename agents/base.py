from abc import ABC
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskState
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import completed_task
import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

class GeminiAgentExecutor(AgentExecutor):
    def __init__(self, system_instruction: str):
        # We don't call super().__init__ because AgentExecutor in 0.3.24 doesn't have an __init__
        # that takes arguments (it's just an ABC)
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
            logger.info(f"GeminiAgentExecutor: run_logic() received response from model")
            return response.text
        except Exception as e:
            logger.error(f"GeminiAgentExecutor: Error in run_logic: {str(e)}", exc_info=True)
            raise

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        SDK 0.3.24 pattern for direct SDK calls.
        """
        logger.info(f"GeminiAgentExecutor.execute() started for task: {context.task_id}")
        try:
            user_input = context.get_user_input()
            if not user_input:
                logger.warning("No user input received")
                return

            # Process with Gemini
            logger.info(f"Calling Gemini model with input: {user_input[:50]}...")
            response = await self.model.generate_content_async(user_input)
            text_response = response.text
            logger.info(f"Gemini responded. Length: {len(text_response)}")

            # 3. Enqueue Message
            msg = new_agent_text_message(
                text=text_response,
                task_id=context.task_id,
                context_id=context.context_id
            )
            await event_queue.enqueue_event(msg)

        except Exception as e:
            print(f">>> [DEBUG] EXCEPTION in GeminiAgentExecutor: {str(e)}")
            logger.error(f"Error executing agent: {str(e)}")
            # In a more robust implementation, we'd enqueue a TaskStatusUpdateEvent with failed state
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
