export const TYPES = {
  assistant: {
    id: "assistant",
    title: "Assistant",
    description:
      "These GPTs can use an arbitrary number of tools, and you can give them arbitrary instructions. The LLM itself is responsible for deciding which tools to call and how many times to call them. This makes them super powerful and flexible, but they can be unreliable at times! As such, only a subset of the most performant models work with these.",
    files: true,
  },
  chatbot: {
    id: "chatbot",
    title: "Chatbot",
    description:
      "These GPTs are solely parameterized by arbitrary instructions. This makes them great at taking on specific personas or characters. Because these are a relatively simple architecture, these work well with even less powerful models.",
    files: false,
  },
  chat_retrieval: {
    id: "chat_retrieval",
    title: "RAG",
    description:
      "These GPTs can be given an arbitrary number of files, and you can give them arbitrary instructions. During each interaction the files are searched once (and only once) for relevant information, and then GPT responds to the user. This makes them perfect if you want to create a simple GPT that has knowledge of external data. Because these are a relatively simple architecture, these work well with even less powerful models.",
    files: true,
  },
};
