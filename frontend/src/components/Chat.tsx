import { useEffect } from "react";
import { Chat as ChatType, Message as MessageType } from "../hooks/useChatList";
import { StreamStateProps } from "../hooks/useStreamState";
import { str } from "../utils/str";
import TypingBox from "./TypingBox";
import { cn } from "../utils/cn";
import { marked } from "marked";
import DOMPurify from "dompurify";

interface ChatProps extends Pick<StreamStateProps, "stream" | "stopStream"> {
  chat: ChatType;
  startStream: (message: string) => Promise<void>;
}

function Function(props: { call: boolean; name?: string; args?: string }) {
  return (
    <>
      {props.call && (
        <span className="text-gray-900 whitespace-pre-wrap break-words mr-2">
          Use
        </span>
      )}
      {props.name && (
        <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-sm font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10 relative -top-[1px] mr-2 mb-2">
          {props.name}
        </span>
      )}
      {props.args && (
        <div className="text-gray-900 whitespace-pre-wrap break-words">
          <div className="ring-1 ring-gray-300 rounded">
            <table className="divide-y divide-gray-300">
              <tbody>
                {Object.entries(JSON.parse(props.args)).map(
                  ([key, value], i) => (
                    <tr key={i}>
                      <td
                        className={cn(
                          i === 0 ? "" : "border-t border-transparent",
                          "py-1 px-3 table-cell text-sm border-r border-r-gray-300"
                        )}
                      >
                        <div className="font-medium text-gray-500">{key}</div>
                      </td>
                      <td
                        className={cn(
                          i === 0 ? "" : "border-t border-gray-200",
                          "py-1 px-3 table-cell"
                        )}
                      >
                        {str(value)}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

function Message(props: MessageType) {
  return (
    <div className="leading-6 flex flex-row mb-8">
      <div className="font-medium text-sm text-gray-400 uppercase mr-2 mt-1 w-24">
        {props.type}
      </div>
      <div className="flex-1">
        {props.type === "function" && (
          <Function call={false} name={props.name} />
        )}
        {props.additional_kwargs?.function_call && (
          <Function
            call={true}
            name={props.additional_kwargs.function_call.name}
            args={props.additional_kwargs.function_call.arguments}
          />
        )}
        {typeof props.content === "string" ? (
          <div
            className="text-gray-900 prose"
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(marked(props.content)).trim(),
            }}
          />
        ) : (
          <div className="text-gray-900 prose">{str(props.content)}</div>
        )}
      </div>
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
