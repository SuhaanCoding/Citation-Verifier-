"""
A2A Test Client for Parser Agent

This script tests the Parser Agent by sending a message via A2A protocol.
Run the Parser Agent first: python -m agents.parser.server

Usage: python scripts/test_parser_a2a.py
"""
import asyncio
import httpx
import json

PARSER_URL = "http://localhost:8001"


async def test_parser_agent():
    """Send a test message to the Parser Agent and print the response."""
    
    print("Testing Parser Agent via A2A...")
    print(f"Parser URL: {PARSER_URL}")
    print("-" * 50)
    
    # Test text with various citation types
    test_text = """
    According to recent research (doi:10.1234/test.2024), AI has made significant progress.
    The findings align with the study at https://example.org/ai-research/2024.
    For background, see the textbook ISBN 978-0-13-468599-1.
    Smith, J. A. (2020). The impact of AI on society. Journal of AI Research.
    """
    
    # A2A message format - requires messageId
    import uuid
    
    message = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [
                    {"type": "text", "text": test_text}
                ]
            }
        },
        "id": "test-1"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PARSER_URL}/",
                json=message,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            print("-" * 50)
            
            if response.status_code == 200:
                result = response.json()
                print("Response:")
                print(json.dumps(result, indent=2))
            else:
                print(f"Error: {response.text}")
                
    except httpx.ConnectError:
        print("ERROR: Could not connect to Parser Agent.")
        print("Make sure the agent is running: python -m agents.parser.server")
    except Exception as e:
        print(f"ERROR: {e}")


async def test_health():
    """Check if the Parser Agent is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{PARSER_URL}/.well-known/agent.json")
            if response.status_code == 200:
                agent_card = response.json()
                print("✅ Parser Agent is running!")
                print(f"   Name: {agent_card.get('name', 'Unknown')}")
                print(f"   Version: {agent_card.get('version', 'Unknown')}")
                return True
    except:
        pass
    
    print("❌ Parser Agent is not running")
    return False


if __name__ == "__main__":
    print("=" * 50)
    print("Citation Verifier - Parser Agent Test")
    print("=" * 50)
    print()
    
    asyncio.run(test_health())
    print()
    asyncio.run(test_parser_agent())
