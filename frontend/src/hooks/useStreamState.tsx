/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { Message } from "../types";

export interface StreamState {
  status: "inflight" | "error" | "done";
  messages?: Message[] | Record<string, any>;
  run_id?: string;
}

export interface StreamStateProps {
  streams: {
    [tid: string]: StreamState;
  };
  startStream: (
    input: Message[] | Record<string, any> | null,
    thread_id: string,
    config?: Record<string, unknown>,
  ) => Promise<void>;
  stopStream?: (thread_id: string, clear?: boolean) => void;
}

export function useStreamState(): StreamStateProps {
  const [current, setCurrent] = useState<{ [tid: string]: StreamState }>({});
  const [controller, setController] = useState<AbortController | null>(null);

  const startStream = useCallback(
    async (
      input: Message[] | Record<string, any> | null,
      thread_id: string,
      config?: Record<string, unknown>,
    ) => {
      const controller = new AbortController();
      setController(controller);
      setCurrent((threads) => ({
        ...threads,
        [thread_id]: { status: "inflight", messages: input || [] },
      }));

      await fetchEventSource("/runs/stream", {
        signal: controller.signal,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input, thread_id, config }),
        openWhenHidden: true,
        onmessage(msg) {
          if (msg.event === "data") {
            const messages = JSON.parse(msg.data);
            setCurrent((threads) => ({
              ...threads,
              [thread_id]: {
                status: "inflight" as StreamState["status"],
                messages: mergeMessagesById(
                  threads[thread_id]?.messages,
                  messages,
                ),
                run_id: threads[thread_id]?.run_id,
              },
            }));
          } else if (msg.event === "metadata") {
            const { run_id } = JSON.parse(msg.data);
            setCurrent((threads) => ({
              ...threads,
              [thread_id]: {
                status: "inflight" as StreamState["status"],
                messages: threads[thread_id]?.messages,
                run_id,
              },
            }));
          } else if (msg.event === "error") {
            setCurrent((threads) => ({
              ...threads,
              [thread_id]: {
                status: "error",
                messages: threads[thread_id]?.messages,
                run_id: threads[thread_id]?.run_id,
              },
            }));
          }
        },
        onclose() {
          setCurrent((threads) => ({
            ...threads,
            [thread_id]: {
              status:
                threads[thread_id]?.status === "error"
                  ? threads[thread_id].status
                  : "done",
              messages: threads[thread_id]?.messages,
              run_id: threads[thread_id]?.run_id,
            },
          }));
          setController(null);
        },
        onerror(error) {
          setCurrent((threads) => ({
            ...threads,
            [thread_id]: {
              status: "error",
              messages: threads[thread_id]?.messages,
              run_id: threads[thread_id]?.run_id,
            },
          }));
          setController(null);
          throw error;
        },
      });
    },
    [],
  );

  const stopStream = useCallback(
    (thread_id: string, clear: boolean = false) => {
      controller?.abort();
      setController(null);
      if (clear) {
        setCurrent((threads) => ({
          ...threads,
          [thread_id]: {
            status: "done",
            run_id: threads[thread_id]?.run_id,
          },
        }));
      } else {
        setCurrent((threads) => ({
          ...threads,
          [thread_id]: {
            status: "done",
            messages: threads[thread_id]?.messages,
            run_id: threads[thread_id]?.run_id,
          },
        }));
      }
    },
    [controller],
  );

  return {
    startStream,
    stopStream,
    streams: current,
  };
}

export function mergeMessagesById(
  left: Message[] | Record<string, any> | null | undefined,
  right: Message[] | Record<string, any> | null | undefined,
): Message[] {
  const leftMsgs = Array.isArray(left) ? left : left?.messages;
  const rightMsgs = Array.isArray(right) ? right : right?.messages;

  const merged = (leftMsgs ?? [])?.slice();
  for (const msg of rightMsgs ?? []) {
    const foundIdx = merged.findIndex((m: any) => m.id === msg.id);
    if (foundIdx === -1) {
      merged.push(msg);
    } else {
      merged[foundIdx] = msg;
    }
  }
  return merged;
}
