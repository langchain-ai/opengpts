import {
  HandThumbDownIcon,
  HandThumbUpIcon,
  EllipsisHorizontalIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";
import { useState } from "react";

export function LangSmithActions(props: { runId: string }) {
  const [state, setState] = useState<{
    score: number;
    inflight: boolean;
  } | null>(null);
  const sendFeedback = async (score: number) => {
    setState({ score, inflight: true });
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
