import os
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI


def get_openai_function_agent(tools, system_message, gpt_4: bool = False, azure: bool = False):
    if not azure:
        if gpt_4:
            llm = ChatOpenAI(model="gpt-4", temperature=0)
        else:
            llm = ChatOpenAI(temperature=0)
    else:
        llm = AzureChatOpenAI(
            temperature=0,
            deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    if tools:
        llm_with_tools = llm.bind(
            functions=[format_tool_to_openai_function(t) for t in tools]
        )
    else:
        llm_with_tools = llm
    agent = (
        {
            "messages": lambda x: x["messages"],
            "agent_scratchpad": lambda x: format_to_openai_functions(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )
    return agent
