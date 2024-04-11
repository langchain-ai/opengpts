import { useEffect, useMemo, useRef, useState } from "react";
import { Message } from "./useChatList";
import { StreamState, mergeMessagesById } from "./useStreamState";

async function getState(threadId: string) {
  const { values, next } = await fetch(`/threads/${threadId}/state`, {
    headers: {
      Accept: "application/json",
    },
  }).then((r) => r.json());
  return { values, next };
}

function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

export function useChatMessages(
  threadId: string | null,
  stream: StreamState | null,
  stopStream?: (clear?: boolean) => void,
): { messages: Message[] | null; next: string[] } {
  const [messages, setMessages] = useState<Message[] | null>(null);
  const [next, setNext] = useState<string[]>([]);
  const prevStreamStatus = usePrevious(stream?.status);

  useEffect(() => {
    async function fetchMessages() {
      if (threadId) {
        const { values, next } = await getState(threadId);
        setMessages(values);
        setNext(next);
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
        const { values, next } = await getState(threadId);
        setMessages(values);
        setNext(next);
        stopStream?.(true);
      }
    }

    if (prevStreamStatus === "inflight" && stream?.status !== "inflight") {
      setNext([]);
      fetchMessages();
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream?.status]);

  return useMemo(
    () => ({
      messages: mergeMessagesById(messages, stream?.messages),
      next,
    }),
    [messages, stream?.messages, next],
  );
}
