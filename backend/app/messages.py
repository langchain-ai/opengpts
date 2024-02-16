from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from typing import Sequence

def select_conversation_messages(messages: Sequence[BaseMessage]):
    """Select only user input <> completion pairs and current scratchpad.

    Ignore previous scratchpads (function calls, etc)."""
    new_messages = []
    _messages = []
    for m in messages:
        if isinstance(m, HumanMessage):
            # if the last message in the existing run is NOT AIMessage, then
            # that means something interrupted it, so let's ignore this
            if not isinstance(_messages[-1], AIMessage):
                continue
            # Otherwise, we add the first (Human) and last (AI) message to the
            # full list of messages
            new_messages.append(_messages[0])
            new_messages.append(_messages[-1])
            # Start a new list of messages
            _messages = [m]
        else:
            _messages.append(m)
    # Now we add the final messages to the list of messages
    # This are all messages that are part of the current scratchpad
    new_messages.extend(_messages)
    return new_messages
