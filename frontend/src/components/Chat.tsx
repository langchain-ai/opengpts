import { useEffect } from "react";
import { Chat as ChatType } from "../hooks/useChatList";
import { StreamStateProps } from "../hooks/useStreamState";
import TypingBox from "./TypingBox";
import { Message } from "./Message";

interface ChatProps extends Pick<StreamStateProps, "stream" | "stopStream"> {
  chat: ChatType;
  startStream: (message: string) => Promise<void>;
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
