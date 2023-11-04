from .openai_functions import get_openai_function_agent
from .xml import get_xml_agent
from enum import Enum

class GizmoAgentType(str, Enum):
    OPENAI_FUNCTIONS = "OPENAI_FUNCTIONS"
    XML = "XML"


__all__ = ["get_openai_function_agent", "get_xml_agent", "GizmoAgentType"]
