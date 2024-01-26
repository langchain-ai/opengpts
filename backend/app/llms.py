from langchain_openai import AzureChatOpenAI, ChatOpenAI
import os
from langchain_community.chat_models import BedrockChat, ChatAnthropic
import boto3

def get_openai_llm(
        gpt_4: bool = False, azure: bool = False
):
    if not azure:
        if gpt_4:
            llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0, streaming=True)
        else:
            llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, streaming=True)
    else:
        llm = AzureChatOpenAI(
            temperature=0,
            deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
            openai_api_base=os.environ["AZURE_OPENAI_API_BASE"],
            openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
            streaming=True,
        )
    return llm


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
