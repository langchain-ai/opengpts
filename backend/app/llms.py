import os
from functools import lru_cache
import httpx
import boto3
from langchain_community.chat_models import BedrockChat, ChatAnthropic, ChatFireworks
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import AzureChatOpenAI, ChatOpenAI


@lru_cache(maxsize=4)
def get_openai_llm(gpt_4: bool = False, azure: bool = False):
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url is not None or proxy_url != "":
        http_client = httpx.AsyncClient(proxies=proxy_url)
    else:
        http_client = None
    if not azure:
        if gpt_4:
            llm = ChatOpenAI(
                http_client=http_client,
                model="gpt-4-1106-preview",
                temperature=0,
                streaming=True,
            )
        else:
            llm = ChatOpenAI(
                http_client=http_client,
                model="gpt-3.5-turbo-1106",
                temperature=0,
                streaming=True,
            )
    else:
        llm = AzureChatOpenAI(
            http_client=http_client,
            temperature=0,
            deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
            openai_api_base=os.environ["AZURE_OPENAI_API_BASE"],
            openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
            streaming=True,
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
        model = ChatAnthropic(temperature=0, max_tokens_to_sample=2000)
    return model


@lru_cache(maxsize=1)
def get_google_llm():
    return ChatVertexAI(
        model_name="gemini-pro", convert_system_message_to_human=True, streaming=True
    )


@lru_cache(maxsize=1)
def get_mixtral_fireworks():
    return ChatFireworks(model="accounts/fireworks/models/mixtral-8x7b-instruct")
