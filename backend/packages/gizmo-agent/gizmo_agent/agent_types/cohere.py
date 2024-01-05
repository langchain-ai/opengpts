import json

from langchain.chat_models import ChatCohere
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import AIMessage, HumanMessage
from langchain.schema import AgentAction, AgentFinish


def _collapse_messages(messages):
    log = ""
    if isinstance(messages[-1], AIMessage):
        scratchpad = messages[:-1]
        final = messages[-1]
    else:
        scratchpad = messages
        final = None
    if len(scratchpad) % 2 != 0:
        raise ValueError("Unexpected")
    for i in range(0, len(scratchpad), 2):
        action = messages[i]
        observation = messages[i + 1]
        log += f"{action.content}<observation>{observation.content}</observation>"
    if final is not None:
        log += final.content
    return AIMessage(content=log)

def construct_chat_history(messages):
    collapsed_messages = []
    temp_messages = []
    for message in messages:
        if isinstance(message, HumanMessage):
            if temp_messages:
                collapsed_messages.append(_collapse_messages(temp_messages))
                temp_messages = []
            collapsed_messages.append(message)
        else:
            temp_messages.append(message)

    # Don't forget to add the last non-human message if it exists
    if temp_messages:
        collapsed_messages.append(_collapse_messages(temp_messages))

    return collapsed_messages

def get_cohere_function_agent(tools, system_message):
    llm = ChatCohere(model="command-nightly", streaming=True, temperature=0.2)

    prompt = conversational_prompt.partial(
        tools=render_json_description(tools),
        tool_names=", ".join([t.name for t in tools]),
        system_message=system_message,
    )
    llm_with_stop = llm.bind(stop=["</tool_input>"])
    agent = (
        {"messages": lambda x: construct_chat_history(x["messages"])}
        | prompt
        | llm_with_stop
        | parse_output
    )
    return agent

template = """{system_message}

Instead of responding with text, you may invoke any of the following tools that will provide useful information for a future response:

{tools}

If any tool seems relevant to the user's question, be sure to invoke it to provide more information for the user.
In order to use a tool, respond with the name of the tool surrounded with the tags <tool></tool>, and input for the tool with the tags <tool_input></tool_input> tags.
The user will invoke the tool and return the response surrounded by the tags <observation></observation>.

For example, if the user asks "What is the weather in SF?", you can respond with:

<tool>search</tool><tool_input>weather in SF</tool_input>

The user may respond with something like this:

<observation>64 degrees</observation>

After receiving the observation, respond to the as normal, including information from the observation.

Example conversation:

User: What is the weather in San Fransisco?
Chatbot: <tool>weather_search</tool><tool_input>weather in San Fransisco</tool_input>
User: <observation>64 degrees</observation>
Chatbot: It is 64 degrees in SF
"""  # noqa: E501

conversational_prompt = ChatPromptTemplate.from_messages(
    [
        ("user", template),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

def parse_output(message):
    text = message.content
    if "</tool>" in text:
        tool, tool_input, *rest = text.split("</tool>")
        _tool = tool.split("<tool>")[1]
        _tool_input = ""
        if "<tool_input>" in tool_input:
            _tool_input = tool_input.split("<tool_input>")[1]
        if "</tool_input>" in _tool_input:
            _tool_input = _tool_input.split("</tool_input>")[0]
        return AgentAction(tool=_tool, tool_input=_tool_input, log=text)
    else:
        return AgentFinish(return_values={"output": text}, log=text)

def tool_to_object(tool):
    inputs = []
    for input_name, input_schema in tool.args_schema.schema().get("properties").items():
        inputs.append({
            "name": input_name,
            "description": input_schema.get("description"),
            "type": input_schema.get("type"),
        })

    return {
        "name": tool.name,
        "definition": {
            "description": tool.description,
            "inputs": inputs,
        }
    }

def render_json_description(tools):
    return json.dumps([tool_to_object(tool) for tool in tools])
