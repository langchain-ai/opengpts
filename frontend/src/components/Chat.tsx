import { useEffect, useRef } from "react";
import { Chat as ChatType } from "../hooks/useChatList";
import { StreamStateProps } from "../hooks/useStreamState";
import { useChatMessages } from "../hooks/useChatMessages";
import TypingBox from "./TypingBox";
import { Message } from "./Message";
import { ArrowDownCircleIcon } from "@heroicons/react/24/outline";
import { MessageWithFiles } from "../utils/formTypes.ts";

interface ChatProps extends Pick<StreamStateProps, "stream" | "stopStream"> {
  chat: ChatType;
  startStream: (message?: MessageWithFiles) => Promise<void>;
  isDocumentRetrievalActive: boolean;
}

function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

export function Chat(props: ChatProps) {
  const { messages, resumeable } = useChatMessages(
    props.chat.thread_id,
    props.stream,
    props.stopStream,
  );
  const prevMessages = usePrevious(messages);
  useEffect(() => {
    scrollTo({
      top: document.body.scrollHeight,
      behavior:
        prevMessages && prevMessages?.length === messages?.length
          ? "smooth"
          : undefined,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages]);
  return (
    <div className="flex-1 flex flex-col items-stretch pb-[76px] pt-2">
      {messages?.map((msg, i) => (
        <Message
          {...msg}
          key={i}
          runId={
            i === messages.length - 1 && props.stream?.status === "done"
              ? props.stream?.run_id
              : undefined
          }
        />
      ))}
      {(props.stream?.status === "inflight" || messages === null) && (
        <div className="leading-6 mb-2 animate-pulse font-black text-gray-400 text-lg">
          ...
        </div>
      )}
      {props.stream?.status === "error" && (
        <div className="flex items-center rounded-md bg-yellow-50 px-2 py-1 text-xs font-medium text-yellow-800 ring-1 ring-inset ring-yellow-600/20">
          An error has occurred. Please try again.
        </div>
      )}
      {resumeable && props.stream?.status !== "inflight" && (
        <div
          className="flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-800 ring-1 ring-inset ring-yellow-600/20 cursor-pointer"
          onClick={() => props.startStream()}
        >
          <ArrowDownCircleIcon className="h-5 w-5 mr-1" />
          Click to continue.
        </div>
      )}
      <div className="fixed left-0 lg:left-72 bottom-0 right-0 p-4">
        <TypingBox
          onSubmit={props.startStream}
          onInterrupt={
            props.stream?.status === "inflight" ? props.stopStream : undefined
          }
          inflight={props.stream?.status === "inflight"}
          isDocumentRetrievalActive={props.isDocumentRetrievalActive}
        />
      </div>
    </div>
  );
}
