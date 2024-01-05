from enum import Enum

from .openai import get_openai_function_agent
from .cohere import get_cohere_function_agent
from .xml.agent import get_xml_agent


class GizmoAgentType(str, Enum):
    GPT_35_TURBO = "GPT 3.5 Turbo"
    # GPT_4 = "GPT 4"
    # AZURE_OPENAI = "GPT 4 (Azure OpenAI)"
    # CLAUDE2 = "Claude 2"
    # BEDROCK_CLAUDE2 = "Claude 2 (Amazon Bedrock)"
    COHERE_COMMAND = "Command (Cohere)"


__all__ = [
    "get_openai_function_agent",
    "get_cohere_function_agent",
    "get_xml_agent",
    "GizmoAgentType",
]
