import os
import uvicorn
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from orchestrator.host import PipelineHost
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

def create_a2a_app():
    logger.info("Configuring Agent Capabilities...")
    capabilities = AgentCapabilities(
        streaming=True,
        push_notifications=False
    )

    logger.info("Defining Agent Skills...")
    skills = [
        AgentSkill(
            id="generate_ad_script",
            name="Generate Ad Script",
            description="Generates a structured KukuFM ad script from a show concept.",
            tags=["kukufm", "ad-script", "generation"]
        )
    ]

    # 3. Define Agent Card
    port = os.getenv("A2A_SERVER_PORT", "9999")
    agent_card = AgentCard(
        name="KukuTV Ad Script Generator",
        description="Complex agent pipeline for generating KukuFM audio ad scripts.",
        url=f"http://localhost:{port}/",
        version="1.0.0",
        capabilities=capabilities,
        skills=skills,
        preferred_transport="JSONRPC",
        protocol_version="0.3.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"]
    )

    # 4. Initialize Pipeline Host Agent
    logger.info("Initializing PipelineHost Agent...")
    host_agent = PipelineHost()

    # 5. Create Starlette Application
    logger.info("Creating A2AStarletteApplication...")
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=host_agent,
            task_store=InMemoryTaskStore()
        )
    )

    logger.info("Building application...")
    return a2a_app.build()

app = create_a2a_app()

if __name__ == "__main__":
    port = int(os.getenv("A2A_SERVER_PORT", "9999"))
    logger.info(f"Starting A2A Server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
