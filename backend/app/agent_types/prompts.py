xml_template = """{system_message}

You have access to the following tools:

{tools}

In order to use a tool, you can use <tool></tool> and <tool_input></tool_input> tags. You will then get back a response in the form <observation></observation>
For example, if you have a tool called 'search' that could run a google search, in order to search for the weather in SF you would respond:

<tool>search</tool><tool_input>weather in SF</tool_input>
<observation>64 degrees</observation>

When you are done, you can respond as normal to the user.

Example 1:

Human: Hi!

Assistant: Hi! How are you?

Human: What is the weather in SF?
Assistant: <tool>search</tool><tool_input>weather in SF</tool_input>
<observation>64 degrees</observation>
It is 64 degrees in SF


Begin!"""
