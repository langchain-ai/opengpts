from langchain.tools.render import render_text_description

from .prompts import conversational_prompt, parse_output


def get_xml_agent(model, tools, system_message):
    prompt = conversational_prompt.partial(
        tools=render_text_description(tools),
        tool_names=", ".join([t.name for t in tools]),
        system_message=system_message,
    )
    llm_with_stop = model.bind(stop=["</tool_input>"])

    agent = prompt | llm_with_stop | parse_output
    return agent
