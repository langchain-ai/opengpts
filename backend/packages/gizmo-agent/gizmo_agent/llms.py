from langchain.chat_models import ChatOpenAI
from langchain.chat_models import ChatAnthropic, ChatFireworks

def _get_llm_gpt_35_turbo():
    return ChatOpenAI(model_name="gpt-3.5-turbo")


def _get_llm_gpt_4():
    return ChatOpenAI(model_name="gpt-4")


def _get_llm_claude2():
    return ChatAnthropic(model_name="claude-2")


def _get_llm_zephyr():
    return ChatFireworks(model="accounts/fireworks/models/zephyr-7b-beta")