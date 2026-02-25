from agents.structurer_agent import StructurerAgent
from agents.router_agent import RouterAgent
from agents.speaker_agent import SpeakerAgent
from agents.script_agent import ScriptAgent
from agents.validator_agent import ValidatorAgent
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from a2a.utils.task import completed_task
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class PipelineHost(AgentExecutor):
    """
    KukuTV A2A Pipeline Host Agent.
    Orchestrates the ad script generation pipeline by calling specialized agents internally.
    """
    def __init__(self):
        self.structurer = StructurerAgent()
        self.router = RouterAgent()
        self.speaker = SpeakerAgent()
        self.script_writer = ScriptAgent()
        self.validator = ValidatorAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info(f"PipelineHost.execute() started for task: {context.task_id}")
        user_input = context.get_user_input()
        if not user_input:
            logger.warning("PipelineHost: No user input found in context")
            return

        try:
            print(f">>> [HOST] PipelineHost.execute() starting for {context.task_id}")
            logger.info(f"PipelineHost: Input: {user_input[:50]}...")
            
            # Step 1: Structure Input
            print(">>> [HOST] Step 1: Structurer...")
            await event_queue.enqueue_event(new_agent_text_message(
                text="[1/5] Analyzing show structure...",
                task_id=context.task_id,
                context_id=context.context_id
            ))
            structure = await self.structurer.run_logic(user_input)
            
            # Step 2: Route Format
            print(">>> [HOST] Step 2: Router...")
            await event_queue.enqueue_event(new_agent_text_message(
                text="[2/5] Selecting ad format...",
                task_id=context.task_id,
                context_id=context.context_id
            ))
            ad_format = await self.router.run_logic(structure)
            
            # Step 3: Define Speakers
            print(">>> [HOST] Step 3: Speaker...")
            await event_queue.enqueue_event(new_agent_text_message(
                text="[3/5] Creating speaker profiles...",
                task_id=context.task_id,
                context_id=context.context_id
            ))
            speakers = await self.speaker.run_logic(ad_format)
            
            # Step 4: Write Script
            print(">>> [HOST] Step 4: Script...")
            await event_queue.enqueue_event(new_agent_text_message(
                text="[4/5] Drafting ad script...",
                task_id=context.task_id,
                context_id=context.context_id
            ))
            context_data = f"Structure: {structure}\nFormat: {ad_format}\nSpeakers: {speakers}"
            script = await self.script_writer.run_logic(context_data)
            
            # Step 5: Validate Script
            print(">>> [HOST] Step 5: Validator...")
            await event_queue.enqueue_event(new_agent_text_message(
                text="[5/5] Validating final script...",
                task_id=context.task_id,
                context_id=context.context_id
            ))
            validation = await self.validator.run_logic(script)
            
            print(">>> [HOST] Step 6: Finalizing...")
            final_output = f"""
### Show Structure
{structure}

### Ad Format
{ad_format}

### Speaker Profiles
{speakers}

### Generated Ad Script
{script}

### Validation Report
{validation}
"""
            # Send Final Message
            logger.info("Enqueuing final message...")
            await event_queue.enqueue_event(new_agent_text_message(
                text=final_output,
                task_id=context.task_id,
                context_id=context.context_id
            ))

            # Mark Task Completed
            if context.current_task:
                logger.info("Marking task as COMPLETED...")
                await event_queue.enqueue_event(completed_task(context.current_task))
            
            logger.info("PipelineHost: execute() finished successfully.")

        except Exception as e:
            error_msg = f"PipelineHost Error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await event_queue.enqueue_event(new_agent_text_message(
                text=f"ERROR: {error_msg}",
                task_id=context.task_id,
                context_id=context.context_id
            ))
            # Mark task as failed if possible
            if context.current_task:
                from a2a.types import TaskStatusUpdateEvent, TaskState, TaskStatus
                from a2a.utils.message import new_agent_text_message
                await event_queue.enqueue_event(TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    status=TaskStatus(state=TaskState.failed, message=new_agent_text_message(text=error_msg))
                ))
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info(f"PipelineHost: Canceling task {context.task_id}")
        pass
