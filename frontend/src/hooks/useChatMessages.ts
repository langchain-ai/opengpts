import { useEffect, useState } from "react";
import { Message } from "./useChatList";
import { StreamState } from "./useStreamState";

async function getMessages(threadId: string) {
  const { messages } = await fetch(`/threads/${threadId}/messages`, {
    headers: {
      Accept: "application/json",
    },
  }).then((r) => r.json());
  return messages;
}

export function useChatMessages(
  threadId: string | null,
  stream: StreamState | null
): Message[] | null {
  const [messages, setMessages] = useState<Message[] | null>(null);

  useEffect(() => {
    async function fetchMessages() {
      if (threadId) {
        setMessages(await getMessages(threadId));
      }
    }

    fetchMessages();

    return () => {
      setMessages(null);
    };
  }, [threadId]);

  useEffect(() => {
    async function fetchMessages() {
      if (threadId) {
        setMessages(await getMessages(threadId));
      }
    }

    if (stream?.status !== "inflight") {
      fetchMessages();
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream?.status]);

  return stream?.merge
    ? [...(messages ?? []), ...(stream.messages ?? [])]
    : stream?.messages ?? messages;
}
