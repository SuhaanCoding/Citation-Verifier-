"""
Parser Agent - Server Entry Point

Starts the A2A server with SLIM transport binding for the Parser Agent.
"""
import asyncio
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agents.parser.card import get_parser_agent_card
from agents.parser.agent_executor import ParserAgentExecutor


def create_parser_server():
    """Create and configure the Parser Agent A2A server."""
    
    agent_card = get_parser_agent_card()
    executor = ParserAgentExecutor()
    task_store = InMemoryTaskStore()
    
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )
    
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    
    return app


def main():
    """Run the Parser Agent server."""
    import uvicorn
    
    host = os.getenv("PARSER_HOST", "0.0.0.0")
    port = int(os.getenv("PARSER_PORT", "8001"))
    
    print(f"Starting Parser Agent on {host}:{port}")
    
    app = create_parser_server()
    uvicorn.run(app.build(), host=host, port=port)


if __name__ == "__main__":
    main()
