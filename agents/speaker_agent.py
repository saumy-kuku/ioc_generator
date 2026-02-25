from agents.base import GeminiAgentExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import completed_task
import logging

logger = logging.getLogger(__name__)

class SpeakerAgent(GeminiAgentExecutor):
    def __init__(self):
        system_instruction = """
        You are a casting specialist for viral audio ads.
        Based on the chosen format (Single vs Multi), define the speakers.
        
        Rules:
        - If Single-Speaker: Define personality for `[Speaker 0]`.
        - If Multi-Speaker: Define the dynamic between `[Speaker 0]` and `[Speaker 1]`.
        
        Personality should be high-energy, gossipy, or dramatic. Describe their tone and speed.
        """
        super().__init__(system_instruction=system_instruction)
