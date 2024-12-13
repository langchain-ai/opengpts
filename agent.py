from langchain.agents import Tool, initialize_agent
from langchain.chat_models import ChatOpenAI

def suggest_meeting_time(events):
    return "Next available slot: Tomorrow at 3 PM."

tool = Tool(name="Meeting Suggestion", func=suggest_meeting_time)
llm = ChatOpenAI(temperature=0)

agent = initialize_agent(tools=[tool], llm=llm, agent="zero-shot-react-description")

user_query = "Suggest a meeting time."
print(agent.run(user_query))
