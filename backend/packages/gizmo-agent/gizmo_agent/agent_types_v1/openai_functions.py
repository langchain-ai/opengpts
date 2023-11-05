from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain.load import load

assistant_system_message = """You are a helpful assistant. \
Use tools (only if necessary) to best answer the users questions."""


def get_openai_function_agent(llm, tools, system_message):
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
    agent = (
        {"messages": lambda x: [load(m) for m in x["messages"]]}
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )
    return agent
