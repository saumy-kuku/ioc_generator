from agents.base import GeminiAgentExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import completed_task
import logging

logger = logging.getLogger(__name__)

class StructurerAgent(GeminiAgentExecutor):
    def __init__(self):
        system_instruction = """
        You are a KukuTV Content Analyst. 
        Your task is to parse log-style episode data (which may include dates, EP numbers, and metadata like 'gemini-2.5-flash-lite') and extract a structured story summary.
        
        Specifically:
        1. Identify the Show Title and Character Names (Parul, Naveen, Nalin, etc.).
        2. Extract the Core Conflict (e.g., Baby swap, Betrayal, Revenge).
        3. Identify the vibe/genre from tags like 'Drama Bhar Ke' or 'Shock Laga Ke'.
        
        Output only valid JSON with keys: show_title, characters, core_conflict, vibe, summary.
        """
        super().__init__(system_instruction=system_instruction)
