import { useEffect, useState } from "react";
import { Message } from "../types";
import { StreamState } from "./useStreamState";

async function getHistories(threadId: string) {
  const response = await fetch(`/threads/${threadId}/history`, {
    headers: {
      Accept: "application/json",
    },
  }).then((r) => r.json());
  return response;
}

export interface History {
  values: Message[];
  next: string[];
  config: Record<string, unknown>;
}

export function useHistories(
  threadId: string | null,
  stream: StreamState | null,
): {
  histories: History[];
  setHistories: React.Dispatch<React.SetStateAction<History[]>>;
} {
  const [histories, setHistories] = useState<History[]>([]);

  useEffect(() => {
    async function fetchHistories() {
      if (threadId) {
        const histories = await getHistories(threadId);
        setHistories(histories);
      }
    }
    fetchHistories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId, stream?.status]);

  return { histories, setHistories };
}
