"""
Parser Agent - A2A Protocol Bridge (Agent Executor)

Handles incoming A2A requests and bridges them to the ParserAgent logic.
"""
import json
from typing import AsyncIterator
from a2a.types import (
    Message,
    Part,
    TextPart,
    DataPart,
    Role,
    TaskState,
    Task,
    Artifact,
)
from agents.parser.agent import ParserAgent
from agents.common.models import Citation


class ParserAgentExecutor:
    """
    A2A protocol bridge for the Parser Agent.
    
    Receives text via A2A messages, invokes ParserAgent.parse(),
    and returns structured citations as A2A response.
    """
    
    def __init__(self):
        self.agent = ParserAgent()

    async def execute(
        self,
        task: Task,
        message: Message
    ) -> AsyncIterator[tuple[TaskState, Message | None, list[Artifact] | None]]:
        """
        Execute the parsing task.
        
        Args:
            task: The A2A task context
            message: Incoming message containing text to parse
            
        Yields:
            Tuple of (state, response_message, artifacts)
        """
        # Extract text from the incoming message
        text_to_parse = self._extract_text(message)
        
        if not text_to_parse:
            yield (
                TaskState.FAILED,
                Message(
                    role=Role.AGENT,
                    parts=[TextPart(text="Error: No text provided to parse")]
                ),
                None
            )
            return
        
        try:
            # Parse the citations
            citations: list[Citation] = self.agent.parse(text_to_parse)
            
            # Convert to JSON-serializable format
            citations_data = [c.model_dump() for c in citations]
            
            # Create response message with results
            response_parts: list[Part] = [
                TextPart(text=f"Found {len(citations)} citation(s)"),
                DataPart(data={"citations": citations_data})
            ]
            
            yield (
                TaskState.COMPLETED,
                Message(role=Role.AGENT, parts=response_parts),
                None
            )
            
        except Exception as e:
            yield (
                TaskState.FAILED,
                Message(
                    role=Role.AGENT,
                    parts=[TextPart(text=f"Error parsing citations: {str(e)}")]
                ),
                None
            )

    def _extract_text(self, message: Message) -> str:
        """Extract text content from an A2A message."""
        text_parts = []
        for part in message.parts:
            if isinstance(part, TextPart):
                text_parts.append(part.text)
        return "\n".join(text_parts)
