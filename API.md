# API Getting Started

This documentation covers how to get started with the API that backs OpenGPTs.
This allows you to easily integrate it with a different frontend of your choice.

For full API documentation, see [localhost:8100/docs](localhost:8100/docs) after deployment.

If you want to see the API docs before deployment, check out the [hosted docs here](https://opengpts-example-vz4y4ooboq-uc.a.run.app/docs).

## Create an Assistant

First, let's use the API to create an assistant. 
This should look something like:

```python
import requests
requests.post('http://127.0.0.1:8100/assistants', json={
  "name": "bar",
  "config": {"configurable": {}},
  "public": True
}, cookies= {"opengpts_user_id": "foo"}).content
```
This is creating an assistant with name `"bar"`, with default configuration, that is public, and is associated with user `"foo"` (we are using cookies as a mock auth method).

This should return something like:

```shell
b'{"assistant_id":"9c7d7e6e-654b-4eaa-b160-f19f922fc63b","name":"string","config":{"configurable":{}},"updated_at":"2023-11-20T16:24:30.520340","public":true,"user_id":"foo"}'
```

The config parameters allows you to set the LLM used, the instructions of the assistant and also the tools used.


```
{
  "name": "bar",
  "config": {
    "configurable": {
      "type": "agent",
      "type==agent/agent_type": "GPT 3.5 Turbo",
      "type==agent/system_message": "You are a helpful assistant",
      "type==agent/tools": ["Wikipedia"]
  },
  "public": True
}
```
This creates an assistant with the name `"bar"`, with GPT 3.5 Turbo, with a prompt `"You are a helpful assistant"` using the Wikipedia tool , that is public.

Available tools names can be found in the AvailableTools class in backend/packages/gizmo-agent/gizmo_agent/tools.py
Available llms can be found in GizmoAgentType in backend/packages/gizmo-agent/gizmo_agent/agent_types/__init__.py

## Create a thread

We can now create a thread.
Notably different from OpenAI's assistant API, we require starting the thread with an assistant ID.

```python
import requests
requests.post('http://127.0.0.1:8100/threads', cookies= {"opengpts_user_id": "foo"}, json={
    "name": "hi",
    "assistant_id": "9c7d7e6e-654b-4eaa-b160-f19f922fc63b"
}).content
```

This is creating a thread, named `"hi"`, with the assistant ID that we just created, for the same user.

This should return something like:

```shell
b'{"thread_id":"231dc7f3-33ee-4040-98fe-27f6e2aa8b2b","assistant_id":"9c7d7e6e-654b-4eaa-b160-f19f922fc63b","name":"hi","updated_at":"2023-11-20T16:26:39.083817","user_id":"foo"}'
```

## Add a message

We can check the thread, and see that it is currently empty:

```python
import requests
requests.get(
    'http://127.0.0.1:8100/threads/231dc7f3-33ee-4040-98fe-27f6e2aa8b2b/messages', 
    cookies= {"opengpts_user_id": "foo"}
).content
```
```shell
b'{"messages":[]}'
```

Let's add a message to the thread!

```python
import requests
requests.post(
    'http://127.0.0.1:8100/threads/231dc7f3-33ee-4040-98fe-27f6e2aa8b2b/messages', 
    cookies= {"opengpts_user_id": "foo"}, json={
        "messages": [{
            "content": "hi! my name is bob",
            "type": "human",
        }]
    }
).content
```

If we now run the command to see the thread, we can see that there is now a message on that thread

```python
import requests
requests.get(
    'http://127.0.0.1:8100/threads/231dc7f3-33ee-4040-98fe-27f6e2aa8b2b/messages', 
    cookies= {"opengpts_user_id": "foo"}
).content
```
```shell
b'{"messages":[{"content":"hi! my name is bob","additional_kwargs":{},"type":"human","example":false}]}'
```

## Run the assistant on that thread

We can now run the assistant on that thread.

```python
import requests
requests.post('http://127.0.0.1:8100/runs', cookies= {"opengpts_user_id": "foo"}, json={
    "assistant_id": "9c7d7e6e-654b-4eaa-b160-f19f922fc63b",
    "thread_id": "231dc7f3-33ee-4040-98fe-27f6e2aa8b2b",
    "input": {
        "messages": []
    }
}).content
```
This runs the thread with the same id that we just created, with the assistant that we created, with no additional input messages (see below for how to add input messages).

If we now check the thread, we can see (after a bit) that there is a message from the AI.

```python
import requests
requests.get('http://127.0.0.1:8100/threads/231dc7f3-33ee-4040-98fe-27f6e2aa8b2b/messages', cookies= {"opengpts_user_id": "foo"}).content
```
```shell
b'{"messages":[{"content":"hi! my name is bob","additional_kwargs":{},"type":"human","example":false},{"content":"Hello, Bob! How can I assist you today?","additional_kwargs":{"agent":{"return_values":{"output":"Hello, Bob! How can I assist you today?"},"log":"Hello, Bob! How can I assist you today?","type":"AgentFinish"}},"type":"ai","example":false}]}'
```

## Run the assistant on the thread with new messages

We can also run the assistant on a thread and add new messages at the same time.
Continuing the example above, we can run:

```python
import requests
requests.post('http://127.0.0.1:8100/runs', cookies= {"opengpts_user_id": "foo"}, json={
    "assistant_id": "9c7d7e6e-654b-4eaa-b160-f19f922fc63b",
    "thread_id": "231dc7f3-33ee-4040-98fe-27f6e2aa8b2b",
    "input": {
        "messages": [{
            "content": "whats my name? respond in spanish",
            "type": "human",
        }
        ]
    }
}).content
```

Then, if we call the threads endpoint after a bit we can see the human message - as well as an AI message - get added to the thread.

```python
import requests
requests.get('http://127.0.0.1:8100/threads/231dc7f3-33ee-4040-98fe-27f6e2aa8b2b/messages', cookies= {"opengpts_user_id": "foo"}).content
```

```shell
b'{"messages":[{"content":"hi! my name is bob","additional_kwargs":{},"type":"human","example":false},{"content":"Hello, Bob! How can I assist you today?","additional_kwargs":{"agent":{"return_values":{"output":"Hello, Bob! How can I assist you today?"},"log":"Hello, Bob! How can I assist you today?","type":"AgentFinish"}},"type":"ai","example":false},{"content":"whats my name? respond in spanish","additional_kwargs":{},"type":"human","example":false},{"content":"Tu nombre es Bob.","additional_kwargs":{"agent":{"return_values":{"output":"Tu nombre es Bob."},"log":"Tu nombre es Bob.","type":"AgentFinish"}},"type":"ai","example":false}]}'
```

## Stream
One thing we can do is stream back responses.
This works for both messages as well as tokens.
Below is an example of streaming back tokens for a response.

```python
import requests
import json
response = requests.post(
    'http://127.0.0.1:8100/runs/stream', 
    cookies= {"opengpts_user_id": "foo"}, json={
    "assistant_id": "9c7d7e6e-654b-4eaa-b160-f19f922fc63b",
    "thread_id": "231dc7f3-33ee-4040-98fe-27f6e2aa8b2b",
    "input": {
        "messages": [{
            "content": "have a good day!",
            "type": "human",
        }]
    }
})
res = []
if response.status_code == 200:
    # Iterate over the response
    for line in response.iter_lines():
        if line:  # filter out keep-alive new lines
            string_line = line.decode("utf-8")
            # Only look at where data i returned
            if string_line.startswith('data'):
                json_string = string_line[len('data: '):]
                # Get the json response - contains a list of all messages
                json_value = json.loads(json_string)
                if "messages" in json_value:
                    # Get the content from the last message
                    # If you want to display multiple messages (eg if agent takes intermediate steps) you will need to change this logic
                    print(json_value['messages'][-1]['content'])
else:
    print(f"Failed to retrieve data: {response.status_code}")
```

This streams the following:

```shell
You
You too
You too!
You too! If
You too! If you
You too! If you have
You too! If you have any
You too! If you have any other
You too! If you have any other questions
You too! If you have any other questions,
You too! If you have any other questions, feel
You too! If you have any other questions, feel free
You too! If you have any other questions, feel free to
You too! If you have any other questions, feel free to ask
You too! If you have any other questions, feel free to ask.
You too! If you have any other questions, feel free to ask.
You too! If you have any other questions, feel free to ask.
```
