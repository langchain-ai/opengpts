import { Chat as ChatType } from "../hooks/useChatList";
import { StreamStateProps } from "../hooks/useStreamState";
import { str } from "../utils/str";
import TypingBox from "./TypingBox";

interface ChatProps extends Pick<StreamStateProps, "stream" | "stopStream"> {
  chat: ChatType;
  startStream: (message: string) => Promise<void>;
}

function Message(props: {
  type: string;
  content: string;
  additional_kwargs?: object;
}) {
  return (
    <div className="leading-6 mb-2">
      <span className="font-medium text-sm text-gray-400 uppercase mr-2">
        {props.type}
      </span>{" "}
      <span className="text-gray-900 whitespace-pre-wrap break-words">
        {props.content}
      </span>
      {Object.keys(props.additional_kwargs ?? {}).length > 0 && (
        <span className="text-gray-900 whitespace-pre-wrap break-words">
          {str(props.additional_kwargs)}
        </span>
      )}
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
