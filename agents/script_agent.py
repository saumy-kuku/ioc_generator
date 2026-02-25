from agents.base import GeminiAgentExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import completed_task
import logging

logger = logging.getLogger(__name__)

class ScriptAgent(GeminiAgentExecutor):
    def __init__(self):
        system_instruction = """
        Act as an expert copywriter for short-form viral promotional videos (Reels/Shorts).
        Your task is to write a high-energy, dramatic Hinglish advertisement script (strictly Devanagari script).

        STRICT GUIDELINES:
        1. Language: Hinglish (Hindi + English) in DEVANAGARI ONLY. Use raw Indian slangs (e.g., 'Bhai saab', 'Kand ho gaya', 'Zeher scene').
        2. Words: Maximum 70-90 words total (Strictly 30 SECONDS). 
        3. The Hook (0-3s): Start with a mind-blown or gossip-heavy opening (e.g., "Arre pados waali aunti ne jo bataya na...").
        4. UNPREDICTABLE Analogies: Use famous hilarious Indian analogies (Bollywood dialogues, Nirma/Cadbury ads, etc.) every time.
        5. Format: Use `[Speaker 0]` and `[Speaker 1]` (if multi-speaker). Show Title must be prominent.
        """
        super().__init__(system_instruction=system_instruction)
