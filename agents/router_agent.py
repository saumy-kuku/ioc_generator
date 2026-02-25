from agents.base import GeminiAgentExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import completed_task
import logging

logger = logging.getLogger(__name__)

class RouterAgent(GeminiAgentExecutor):
    def __init__(self):
        system_instruction = """
        You are an ad script format selector for KukuTV.
        Your task is to analyze the plot structure and decide the BEST viral format:
        
        Formats to choose from:
        - Single-Speaker: Best for mind-blown rants, leaked audio style, or aggressive storytime. (e.g. Gossip girl vibe)
        - Multi-Speaker: Best for frantic phone calls, two friends reacting, or heated confrontations.
        
        Decision Criteria:
        - If there is a big revelation or dialogue (like "Nalin stuns everyone"), Multi-Speaker is preferred.
        - If it's a deep internal vow or conspiracy, Single-Speaker Rant works better.
        
        Output: [Selected Format] and a brief reason.
        """
        super().__init__(system_instruction=system_instruction)
