import { PlusIcon } from "@heroicons/react/24/outline";

import { ChatListProps } from "../hooks/useChatList";
import { cn } from "../utils/cn";

export function ChatList(props: {
  chats: ChatListProps["chats"];
  currentChat: ChatListProps["currentChat"];
  enterChat: ChatListProps["enterChat"];
}) {
  return (
    <>
      <div
        onClick={() => props.enterChat(null)}
        className={cn(
          props.currentChat === null
            ? "bg-gray-50 text-indigo-600"
            : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
          "group flex gap-x-3 rounded-md -mx-2 p-2 text-sm leading-6 font-semibold cursor-pointer"
        )}
      >
        <span
          className={cn(
            props.currentChat === null
              ? "text-indigo-600 border-indigo-600"
              : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white"
          )}
        >
          <PlusIcon className="h-4 w-4" />
        </span>
        <span className="truncate">New Chat</span>
      </div>

      <div className="text-xs font-semibold leading-6 text-gray-400 mt-4">
        Your chats
      </div>
      <ul role="list" className="-mx-2 mt-2 space-y-1">
        {props.chats?.map((chat) => (
          <li key={chat.thread_id}>
            <div
              onClick={() => props.enterChat(chat.thread_id)}
              className={cn(
                chat === props.currentChat
                  ? "bg-gray-50 text-indigo-600"
                  : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
                "group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold cursor-pointer"
              )}
            >
              <span
                className={cn(
                  chat === props.currentChat
                    ? "text-indigo-600 border-indigo-600"
                    : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white"
                )}
              >
                {chat.name?.[0] ?? " "}
              </span>
              <span className="truncate">{chat.name}</span>
            </div>
          </li>
        )) ?? (
          <li className="leading-6 p-2 animate-pulse font-black text-gray-400 text-lg">
            ...
          </li>
        )}
      </ul>
    </>
  );
}
