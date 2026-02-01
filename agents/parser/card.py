"""
Parser Agent - AgentCard Definition

Defines the identity, capabilities, and skills for the Citation Parser Agent.
"""
from a2a.types import AgentCard, AgentSkill


def get_parser_agent_card() -> AgentCard:
    """Returns the AgentCard for the Citation Parser Agent."""
    return AgentCard(
        name="Citation Parser Agent",
        description="Extracts citations from academic text. Supports DOI, URL, ISBN, and common citation formats (APA, MLA).",
        url="http://parser:8001",  # Docker service URL
        version="1.0.0",
        skills=[
            AgentSkill(
                id="parse_citations",
                name="Parse Citations",
                description="Extract structured citations from input text",
                tags=["parsing", "citations", "academic"],
                examples=[
                    "Parse this research paper for citations",
                    "Extract all DOIs from this text"
                ]
            )
        ],
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities={
            "streaming": False,
            "pushNotifications": False
        }
    )
