import { useEffect, useMemo, useRef, useState } from "react";
import { Message } from "./useChatList";
import { StreamState } from "./useStreamState";

async function getMessages(threadId: string) {
  const { messages, resumeable } = await fetch(
    `/threads/${threadId}/messages`,
    {
      headers: {
        Accept: "application/json",
      },
    },
  ).then((r) => r.json());
  return { messages, resumeable };
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
): { messages: Message[] | null; resumeable: boolean } {
  const [messages, setMessages] = useState<Message[] | null>(null);
  const [resumeable, setResumeable] = useState(false);
  const prevStreamStatus = usePrevious(stream?.status);

  useEffect(() => {
    async function fetchMessages() {
      if (threadId) {
        const { messages, resumeable } = await getMessages(threadId);
        setMessages(messages);
        setResumeable(resumeable);
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
        const { messages, resumeable } = await getMessages(threadId);
        setMessages(messages);
        setResumeable(resumeable);
        stopStream?.(true);
      }
    }

    if (prevStreamStatus === "inflight" && stream?.status !== "inflight") {
      setResumeable(false);
      fetchMessages();
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream?.status]);

  return useMemo(() => {
    const merged = (messages ?? [])?.slice();
    for (const msg of stream?.messages ?? []) {
      const foundIdx = merged.findIndex((m) => m.id === msg.id);
      if (foundIdx === -1) {
        merged.push(msg);
      } else {
        merged[foundIdx] = msg;
      }
    }
    return { messages: merged, resumeable };
  }, [messages, stream?.messages, resumeable]);
}
