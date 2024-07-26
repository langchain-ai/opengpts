import os
from enum import Enum
from functools import lru_cache
from urllib.parse import urlparse

import boto3
import httpx
import structlog
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import BedrockChat, ChatFireworks
from langchain_community.chat_models.ollama import ChatOllama
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import AzureChatOpenAI, ChatOpenAI

logger = structlog.get_logger(__name__)


class LLMType(str, Enum):
    GPT_4O_MINI = "GPT 4o Mini"
    GPT_4O = "GPT 4o"
    CLAUDE_3_5_SONNET = "Claude 3.5 Sonnet"
    GEMINI = "GEMINI"
    MIXTRAL = "Mixtral"
    OLLAMA = "Ollama"


@lru_cache(maxsize=4)
def get_openai_llm(model: str = "gpt-4o-mini", azure: bool = False):
    proxy_url = os.getenv("PROXY_URL")
    http_client = None
    if proxy_url:
        parsed_url = urlparse(proxy_url)
        if parsed_url.scheme and parsed_url.netloc:
            http_client = httpx.AsyncClient(proxies=proxy_url)
        else:
            logger.warn("Invalid proxy URL provided. Proceeding without proxy.")

    if not azure:
        try:
            openai_model = model
            llm = ChatOpenAI(
                http_client=http_client,
                model=openai_model,
                temperature=0,
            )
        except Exception as e:
            logger.error(
                f"Failed to instantiate ChatOpenAI due to: {str(e)}. Falling back to AzureChatOpenAI."
            )
            llm = AzureChatOpenAI(
                http_client=http_client,
                temperature=0,
                deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
                azure_endpoint=os.environ["AZURE_OPENAI_API_BASE"],
                openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
                openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
            )
    else:
        llm = AzureChatOpenAI(
            http_client=http_client,
            temperature=0,
            deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
            azure_endpoint=os.environ["AZURE_OPENAI_API_BASE"],
            openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
        )
    return llm


@lru_cache(maxsize=2)
def get_anthropic_llm(bedrock: bool = False):
    if bedrock:
        client = boto3.client(
            "bedrock-runtime",
            region_name="us-west-2",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
        model = BedrockChat(model_id="anthropic.claude-v2", client=client)
    else:
        model = ChatAnthropic(
            model_name="claude-3-5-sonnet-20240620",
            max_tokens_to_sample=2000,
            temperature=0,
        )
    return model


@lru_cache(maxsize=1)
def get_google_llm():
    return ChatVertexAI(
        model_name="gemini-pro", convert_system_message_to_human=True, streaming=True
    )


@lru_cache(maxsize=1)
def get_mixtral_fireworks():
    return ChatFireworks(model="accounts/fireworks/models/mixtral-8x7b-instruct")


@lru_cache(maxsize=1)
def get_ollama_llm():
    model_name = os.environ.get("OLLAMA_MODEL")
    if not model_name:
        model_name = "llama2"
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL")
    if not ollama_base_url:
        ollama_base_url = "http://localhost:11434"

    return ChatOllama(model=model_name, base_url=ollama_base_url)


def get_llm(
    llm_type: LLMType,
):
    if llm_type == LLMType.GPT_4O_MINI:
        llm = get_openai_llm(model="gpt-4o-mini")
    elif llm_type == LLMType.GPT_4O:
        llm = get_openai_llm(model="gpt-4o")
    elif llm_type == LLMType.CLAUDE_3_5_SONNET:
        llm = get_anthropic_llm()
    elif llm_type == LLMType.GEMINI:
        llm = get_google_llm()
    elif llm_type == LLMType.MIXTRAL:
        llm = get_mixtral_fireworks()
    else:
        raise ValueError(f"Unsupported LLM type: '{llm_type}'")
    return llm
