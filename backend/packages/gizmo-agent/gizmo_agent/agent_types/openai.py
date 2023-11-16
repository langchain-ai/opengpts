import os

from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function


def get_openai_function_agent(
    tools, system_message, gpt_4: bool = False, azure: bool = False
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
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    if tools:
        llm_with_tools = llm.bind(
            functions=[format_tool_to_openai_function(t) for t in tools]
        )
    else:
        llm_with_tools = llm
    agent = prompt | llm_with_tools | OpenAIFunctionsAgentOutputParser()
    return agent
