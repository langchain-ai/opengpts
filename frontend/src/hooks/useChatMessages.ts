import { useEffect, useMemo, useState } from "react";
import { Message } from "./useChatList";
import { StreamState } from "./useStreamState";

// const MESSAGES_SEEN = new WeakSet<Message>();

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

  return useMemo(() => {
    // TODO replace this with less hacky logic
    const ignoreStream =
      !stream ||
      JSON.stringify(stream.messages) ===
        JSON.stringify(messages?.slice(-stream.messages?.length));

    return ignoreStream ? messages : [...(messages ?? []), ...stream.messages];
  }, [messages, stream]);
}
