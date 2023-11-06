import { useEffect } from "react";
import { Chat as ChatType, Message as MessageType } from "../hooks/useChatList";
import { StreamStateProps } from "../hooks/useStreamState";
import { str } from "../utils/str";
import TypingBox from "./TypingBox";

interface ChatProps extends Pick<StreamStateProps, "stream" | "stopStream"> {
  chat: ChatType;
  startStream: (message: string) => Promise<void>;
}

function Function(props: { call: boolean; name?: string; args?: string }) {
  return (
    <>
      {props.call && (
        <span className="text-gray-900 whitespace-pre-wrap break-words mr-2">
          Call function
        </span>
      )}
      {props.name && (
        <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10 relative -top-0.5 mr-2">
          {props.name}
        </span>
      )}
      {props.call && (
        <span className="text-gray-900 whitespace-pre-wrap break-words mr-2">
          with
        </span>
      )}
      {props.args && (
        <span className="text-gray-900 whitespace-pre-wrap break-words">
          {str(props.args)}
        </span>
      )}
    </>
  );
}

function Message(props: MessageType) {
  return (
    <div className="leading-6 mb-4">
      <span className="font-medium text-sm text-gray-400 uppercase mr-2">
        {props.type}
      </span>
      {props.type === "function" && <Function call={false} name={props.name} />}
      {props.additional_kwargs?.function_call && (
        <Function
          call={true}
          name={props.additional_kwargs.function_call.name}
          args={props.additional_kwargs.function_call.arguments}
        />
      )}
      <span className="text-gray-900 whitespace-pre-wrap break-words">
        {props.content}
      </span>
    </div>
  );
}

export function Chat(props: ChatProps) {
  const messages = [
    ...props.chat.messages,
    ...(props.stream?.messages.filter(
      (msg) => !props.chat.messages.includes(msg)
    ) ?? []),
  ];
  useEffect(() => {
    scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth",
    });
  }, [props.chat.messages, props.stream?.messages]);
  return (
    <div className="flex-1 flex flex-col items-stretch pb-[76px] pt-2">
      {messages.map((msg, i) => (
        <Message {...msg} key={i} />
      ))}
      {props.stream?.status === "inflight" && (
        <div className="leading-6 mb-2 animate-pulse font-black text-gray-400 text-lg">
          ...
        </div>
      )}
      <div className="fixed left-0 lg:left-72 bottom-0 right-0 p-4">
        <TypingBox
          onSubmit={props.startStream}
          disabled={props.stream?.status === "inflight"}
        />
      </div>
    </div>
  );
}
