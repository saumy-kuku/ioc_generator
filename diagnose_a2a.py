try:
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    print("Imports successful")
    
    capabilities = AgentCapabilities(streaming=True, push_notifications=False)
    skills = [AgentSkill(id="test", name="test", description="test", tags=["test"])]
    card = AgentCard(
        name="test", 
        description="test", 
        url="http://localhost:9999/a2a", 
        version="1", 
        capabilities=capabilities, 
        skills=skills,
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"]
    )
    print("AgentCard created successfully")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
