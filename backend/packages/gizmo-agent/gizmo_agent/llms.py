from langchain.chat_models import ChatOpenAI
from langchain.chat_models import ChatAnthropic, ChatFireworks, ChatOllama

LLM_OPTIONS = {
    "gpt-3.5-turbo": ChatOpenAI(model_name="gpt-3.5-turbo"),
    "gpt-4": ChatOpenAI(model_name="gpt-4"),
    "claude-2": ChatAnthropic(model_name="claude-2"),
    "zephyr-fireworks": ChatFireworks(model="accounts/fireworks/models/zephyr-7b-beta"),
    "zephyr-ollama": ChatOllama(model="zephyr"),
}
