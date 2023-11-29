# Long-Term memory
Memory is one part of a cognitive architecture. 
Just as with cognitive architectures, we've found in practice that more application specific forms of memory can go a long way in increasing the reliability and performance of your application.

When we think of long term memory, the most general abstraction is:
- There exists some state that is tracked over time
- This state is updated at some period
- This state is combined into the prompt in some way


So when you're building your application, we would highly recommend asking the above questions:
- What is the state that is tracked?
- How is the state updated?
- How is the state used?

Of course, this is easier said than done. 
And then even if you are able to answer those questions, how can you actually build it?
We've decided to give this a go within OpenGPTs and build a specific type of chatbot with a specific form of memory.

We decided to build a chatbot that could reliably serve as a dungeon master for a game of dungeon and dragons. 
What is the specific type of memory we wanted for this?

**What is the state that is tracked?**

We wanted to first make sure to track the characters that we're involved in the game. Who they were, their descriptions, etc. This seems like something that should be known.
We then also wanted to track the state of the game itself. What had happened up to that point, where they were, etc.
We decided to split this into two distinct things - so we were actually tracking an updating two different states.

**How is the state updated?**

For the character description, we just wanted to update that once at beginning. So we wanted our chatbot to gather all relevant information, update that state, and then never update it again.
Afterwards, we wanted our chatbot to attempt to update the state of the game every turn. If it decides that no update is necessary, then we won't update it. Otherwise, we will override the current state of the game with an LLM generated new state.

**How is the state used?**

We wanted both the character description and the state of the game to always be inserted into the prompt. This is pretty straightforward since they were both text, so it was just some prompt engineering with some placeholders for those variables.

## Implementation
You can see the implementation for this in [this file](backend/packages/agent-executor/agent_executor/dnd.py).
This should be easily modifiable to track another state - to do so, you will want to update the prompts and maybe some of the channels that are written to.