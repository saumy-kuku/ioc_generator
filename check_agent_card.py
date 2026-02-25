import httpx
import asyncio
import os
from dotenv import load_dotenv
from a2a.client.client_factory import ClientFactory

load_dotenv()

async def check_card():
    port = os.getenv("A2A_SERVER_PORT", "9999")
    
    # Common A2A discovery paths
    paths = [
        "/a2a",
        "/a2a/.well-known/agent-card.json",
        "/",
        "/.well-known/agent-card.json"
    ]
    
    print(f"--- Diagnostic Check ---")
    
    async with httpx.AsyncClient() as client:
        for path in paths:
            url = f"http://localhost:{port}{path}"
            print(f"\n[HTTP] Testing GET: {url}")
            try:
                response = await client.get(url)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"FOUND! Content type: {response.headers.get('content-type')}")
                    # print(f"Content: {response.text[:100]}...")
            except Exception as e:
                print(f"Error: {str(e)}")

        # 2. SDK Connection Check
        base_url = f"http://localhost:{port}/"
        print(f"\n[SDK] Testing ClientFactory.connect('{base_url}')...")
        try:
            a2a_client = await ClientFactory.connect(base_url)
            print("Success! SDK established connection.")
            # Check for card if attribute exists, else just print client
            if hasattr(a2a_client, 'agent_card'):
                print(f"Agent Card Name: {a2a_client.agent_card.name}")
            else:
                print(f"Connected Client: {type(a2a_client).__name__}")
        except Exception as e:
            print(f"SDK Connection Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_card())
