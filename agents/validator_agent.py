from agents.base import GeminiAgentExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import completed_task
import logging

logger = logging.getLogger(__name__)

class ValidatorAgent(GeminiAgentExecutor):
    def __init__(self):
        system_instruction = """
        You are a KukuTV Quality Reviewer.
        Validate the generated script for:
        1. Script Length: Must be 30s (70-90 words).
        2. Script Language: Must be Hinglish in DEVANAGARI ONLY. Reject if English characters are used in the dialogue.
        3. Hook: Must have a high-energy opening.
        4. Viral Element: Must contain a famous Indian analogy or dialogue.
        
        Provide verdict: APPROVED or REJECTED with reasons.
        """
        super().__init__(system_instruction=system_instruction)
