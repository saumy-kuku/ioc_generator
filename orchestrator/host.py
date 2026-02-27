from agents.structurer_agent import StructurerAgent
from agents.router_agent import RouterAgent
from agents.speaker_agent import SpeakerAgent
from agents.script_agent import ScriptAgent
from agents.validator_agent import ValidatorAgent
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message, get_message_text
from a2a.types import TaskStatusUpdateEvent, TaskState, TaskStatus
import logging

logger = logging.getLogger(__name__)


class PipelineHost(AgentExecutor):
    def __init__(self):
        self.structurer = StructurerAgent()
        self.router = RouterAgent()
        self.speaker = SpeakerAgent()
        self.script_writer = ScriptAgent()
        self.validator = ValidatorAgent()

    async def _run_step(self, step_name: str, agent, input_text: str) -> str | None:
        """Runs a single agent step with isolated error handling — never raises."""
        try:
            logger.info(f">>> Running step: {step_name}")
            result = await agent.run_logic(input_text)
            logger.info(f">>> Step '{step_name}' completed. Output length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f">>> Step '{step_name}' FAILED: {str(e)}", exc_info=True)
            return None

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info(f"PipelineHost.execute() started for task: {context.task_id}")

        user_input = get_message_text(context.message) if context.message else None
        if not user_input:
            logger.warning("PipelineHost: No user input found in context")
            await event_queue.enqueue_event(new_agent_text_message(text="ERROR: No input received."))
            return

        logger.info(f"PipelineHost: Input received ({len(user_input)} chars): {user_input[:80]}...")

        errors = []

        # Step 1: Structure Input
        await event_queue.enqueue_event(new_agent_text_message(text="[1/5] Analyzing show structure..."))
        structure = await self._run_step("Structurer", self.structurer, user_input)
        if not structure:
            errors.append("Structurer agent failed")
            structure = f"(Structurer failed — using raw input)\n{user_input}"

        # Step 2: Route Format
        await event_queue.enqueue_event(new_agent_text_message(text="[2/5] Selecting ad format..."))
        ad_format = await self._run_step("Router", self.router, structure)
        if not ad_format:
            errors.append("Router agent failed")
            ad_format = "Multi-Speaker format (fallback)"

        # Step 3: Define Speakers
        await event_queue.enqueue_event(new_agent_text_message(text="[3/5] Creating speaker profiles..."))
        speakers = await self._run_step("Speaker", self.speaker, ad_format)
        if not speakers:
            errors.append("Speaker agent failed")
            speakers = "Speaker 0: High energy narrator (fallback)"

        # Step 4: Write Script
        await event_queue.enqueue_event(new_agent_text_message(text="[4/5] Drafting ad script..."))
        context_data = f"Structure: {structure}\nFormat: {ad_format}\nSpeakers: {speakers}"
        script = await self._run_step("ScriptWriter", self.script_writer, context_data)
        if not script:
            errors.append("Script writer agent failed")
            script = "(Script generation failed)"

        # Step 5: Validate Script
        await event_queue.enqueue_event(new_agent_text_message(text="[5/5] Validating final script..."))
        validation = await self._run_step("Validator", self.validator, script)
        if not validation:
            errors.append("Validator agent failed")
            validation = "(Validation skipped)"

        # Build final output
        error_section = ""
        if errors:
            error_section = "### ⚠️ Pipeline Warnings\n" + "\n".join(f"- {e}" for e in errors) + "\n\n"

        final_output = f"""{error_section}### Show Structure
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

        logger.info("Enqueueing final output...")
        await event_queue.enqueue_event(new_agent_text_message(text=final_output))

        if context.current_task:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=context.task_id,
                    contextId=context.context_id,
                    status=TaskStatus(state=TaskState.completed),
                    final=True
                )
            )

        logger.info("PipelineHost: execute() finished successfully.")

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info(f"PipelineHost: Canceling task {context.task_id}")
        pass
