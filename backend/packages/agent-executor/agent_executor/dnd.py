import json

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.pydantic_v1 import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from permchain import BaseCheckpointAdapter, Channel, Pregel
from permchain.channels import LastValue, Topic

character_system_msg = """You are a dungeon master for a game of dungeons and dragons.

You are interacting with the first (and only) player in the game. \
Your job is to collect all needed information about their character. This will be used in the quest. \
Feel free to ask them as many questions as needed to get to the relevant information.
The relevant information is:
- Character's name
- Character's race (or species)
- Character's class
- Character's alignment

Once you have gathered enough information, write that info to `notebook`."""


class CharacterNotebook(BaseModel):
    """Notebook to write information to"""

    player_info: str = Field(
        description="Information about a player that you will remember over time"
    )


character_prompt = ChatPromptTemplate.from_messages(
    [("system", character_system_msg), MessagesPlaceholder(variable_name="messages")]
)

gameplay_system_msg = """You are a dungeon master for a game of dungeons and dragons.

You are leading a quest of one person. Their character description is here:

{character}

A summary of the game state is here:

{state}"""

game_prompt = ChatPromptTemplate.from_messages(
    [("system", gameplay_system_msg), MessagesPlaceholder(variable_name="messages")]
)


class StateNotebook(BaseModel):
    """Notebook to write information to"""

    state: str = Field(description="Information about the current game state")


state_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", gameplay_system_msg),
        MessagesPlaceholder(variable_name="messages"),
        (
            "human",
            "If any updates to the game state are neccessary, please update the state notebook. If none are, just say no.",
        ),
    ]
)


def _maybe_update_state(message: AnyMessage):
    if "function_call" in message.additional_kwargs:
        return Channel.write_to(
            "messages",
            state=json.loads(message.additional_kwargs["function_call"]["arguments"])[
                "state"
            ],
        )


def _maybe_update_character(message: AnyMessage):
    if "function_call" in message.additional_kwargs:
        args = json.loads(message.additional_kwargs["function_call"]["arguments"])
        return Channel.write_to(
            messages=AIMessage(content="Ready for the quest?"),
            character=args["player_info"],
        )


def create_dnd_bot(llm: BaseChatModel, checkpoint: BaseCheckpointAdapter):
    character_model = llm.bind(
        functions=[convert_pydantic_to_openai_function(CharacterNotebook)],
    )
    game_chain = game_prompt | llm | Channel.write_to("messages", check_update=True)
    state_model = llm.bind(
        functions=[convert_pydantic_to_openai_function(StateNotebook)],
        stream=False,
    )
    state_chain = (
        Channel.subscribe_to(["check_update"]).join(["messages", "character", "state"])
        | state_prompt
        | state_model
        | _maybe_update_state
    )
    character_chain = (
        character_prompt
        | character_model
        | Channel.write_to("messages")
        | _maybe_update_character
    )

    def _route_to_chain(_input):
        messages = _input["messages"]
        if not messages:
            return
        if not _input["character"] and isinstance(messages[-1], HumanMessage):
            return character_chain
        elif isinstance(messages[-1], HumanMessage):
            return game_chain

    executor = (
        Channel.subscribe_to(["messages"]).join(["character", "state"])
        | _route_to_chain
    )
    dnd = Pregel(
        chains={"executor": executor, "update_state": state_chain},
        channels={
            "messages": Topic(AnyMessage, accumulate=True),
            "character": LastValue(str),
            "state": LastValue(str),
            "check_update": LastValue(bool),
        },
        input=["messages"],
        output=["messages"],
        checkpoint=checkpoint,
    )
    return dnd
