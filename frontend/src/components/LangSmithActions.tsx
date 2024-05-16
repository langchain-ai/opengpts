import {
  HandThumbDownIcon,
  HandThumbUpIcon,
  EllipsisHorizontalIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";
import { useState } from "react";

export function LangSmithActions(props: { runId: string, threadId: string }) {
  const [state, setState] = useState<{
    score: number;
    inflight: boolean;
  } | null>(null);
  const sendFeedback = async (score: number) => {
    setState({ score, inflight: true });

    // send feedback to LangSmith
    // this is a no-op if tracing is disabled in the backend
    await fetch(`/runs/feedback`, {
      method: "POST",
      body: JSON.stringify({
        run_id: props.runId,
        key: "user_score",
        score: score,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    // score thread, thread will be used as few shot example
    // few shot score must be 1 or 0
    const fewShotScore = score > 0 ? 1 : 0;
    await fetch(`/api/threads/${props.threadId}/state`, {
      method: "PATCH",
      body: JSON.stringify({
        metadata: {score: fewShotScore},
      }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    setState({ score, inflight: false });
  };
  return (
    <div className="flex mt-2 gap-2 flex-row">
      <button
        type="button"
        className="rounded-full p-1 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
        onClick={() => sendFeedback(1)}
      >
        {state?.score === 1 ? (
          state?.inflight ? (
            <EllipsisHorizontalIcon className="h-5 w-5" aria-hidden="true" />
          ) : (
            <CheckIcon className="h-5 w-5" aria-hidden="true" />
          )
        ) : (
          <HandThumbUpIcon className="h-5 w-5" aria-hidden="true" />
        )}
      </button>
      <button
        type="button"
        className="rounded-full p-1 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
        onClick={() => sendFeedback(0)}
      >
        {state?.score === 0 ? (
          state?.inflight ? (
            <EllipsisHorizontalIcon className="h-5 w-5" aria-hidden="true" />
          ) : (
            <CheckIcon className="h-5 w-5" aria-hidden="true" />
          )
        ) : (
          <HandThumbDownIcon className="h-5 w-5" aria-hidden="true" />
        )}
      </button>
    </div>
  );
}
