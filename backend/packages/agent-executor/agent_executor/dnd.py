from permchain import Channel, Pregel, ReservedChannels
from permchain.channels import Topic, LastValue
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import HumanMessage, AIMessage, AnyMessage
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
import json
from langchain.pydantic_v1 import BaseModel, Field

template1 = """You are a dungeon master for a game of dungeons and dragons.

You are interacting with the first (and only) player in the game. \
Your job is to collect all needed information about their character. This will be used in the quest. \
Feel free to ask them as many questions as needed to get to the relevant information.

Once you have gathered enough information, write that info to `notebook`."""





class CharacterNotebook(BaseModel):
    """Notebook to write information to"""
    player_info: str = Field(description="Information about a player that you will remember over time")


character_prompt = ChatPromptTemplate.from_messages([
    ("system", template1),
    MessagesPlaceholder(variable_name="messages")
])

template2 = """You are a dungeon master for a game of dungeons and dragons.

You are leading a quest of one person. Their character description is here:

{character}

A summary of the game state is here:

{state}"""

prompt2 = ChatPromptTemplate.from_messages([
    ("system", template2),
    MessagesPlaceholder(variable_name="messages")
])

class StateNotebook(BaseModel):
    """Notebook to write information to"""
    state: str = Field(description="Information about the current game state")

prompt_update = ChatPromptTemplate.from_messages([
    ("system", template2),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "If any updates to the game state are neccessary, please update the state notebook. If none are, just say no.")
])


def _update_if_necc(message):
    if "function_call" in message.additional_kwargs:
        return (lambda x: json.loads(message.additional_kwargs['function_call']['arguments'])['state']) | Channel.write_to("state")
    else:
        return None

def _optional_save(message):
    if "function_call" in message.additional_kwargs:
        return (lambda x: json.loads(message.additional_kwargs['function_call']['arguments'])['player_info']) | Channel.write_to("character") | Channel.write_to(
            messages = lambda x: AIMessage(content="ready for the quest?")
        )
    else:
        return None





def create_dnd_bot(llm):
    character_model = llm.bind(functions=[convert_pydantic_to_openai_function(CharacterNotebook)])
    chain2 = prompt2 | llm | Channel.write_to("messages") | Channel.write_to(check_update=True)
    model_update = llm.bind(functions=[convert_pydantic_to_openai_function(StateNotebook)])
    chain_update = Channel.subscribe_to(["check_update"]).join(
        ["messages", "character", "state"]) | prompt_update | model_update | _update_if_necc
    character_chain = character_prompt | character_model | Channel.write_to("messages") | _optional_save

    def _route_to_chain(_input):
        messages = _input['messages']
        if not _input['character']:
            if isinstance(messages[-1], HumanMessage):
                return character_chain
            else:
                # If we don't even have character developed yet, then end
                if not _input['character']:
                    return None
                raise ValueError
        else:
            if isinstance(messages[-1], HumanMessage):
                return chain2
            else:
                return None

    executor = Channel.subscribe_to(["messages"]).join(["character", "state"]) | _route_to_chain
    dnd = Pregel(
        chains={"executor": executor, "update": chain_update},
        channels={
            "messages": Topic(AnyMessage, accumulate=True),
            "character": LastValue(str),
            "state": LastValue(str),
            "check_update": LastValue(bool),
        },
        input=["messages"],
        output=["messages"],
    )
    return dnd




