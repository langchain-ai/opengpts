import { PlusIcon, EllipsisVerticalIcon } from "@heroicons/react/24/outline";
import { useState, useEffect } from "react";

import { ChatListProps } from "../hooks/useChatList";
import { cn } from "../utils/cn";
import { useThreadAndAssistant } from "../hooks/useThreadAndAssistant.ts";
import { ConfigListProps } from "../hooks/useConfigList.ts";

export function ChatList(props: {
  chats: ChatListProps["chats"];
  configs: ConfigListProps["configs"];
  enterChat: (id: string | null) => void;
  deleteChat: (id: string) => void;
  enterConfig: (id: string | null) => void;
}) {
  const { currentChat, assistantConfig } = useThreadAndAssistant();

  // State for tracking which chat's menu is visible
  const [visibleMenu, setVisibleMenu] = useState<string | null>(null);

  // Event listener to close the menu when clicking outside of it
  useEffect(() => {
    const closeMenu = () => setVisibleMenu(null);
    window.addEventListener("click", closeMenu);
    return () => window.removeEventListener("click", closeMenu);
  }, []);

  return (
    <>
      <div
        onClick={() => props.enterChat(null)}
        className={cn(
          !currentChat && assistantConfig
            ? "bg-gray-50 text-indigo-600"
            : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
          "group flex gap-x-3 rounded-md -mx-2 p-2 leading-6 font-semibold cursor-pointer",
        )}
      >
        <span
          className={cn(
            !currentChat && assistantConfig
              ? "text-indigo-600 border-indigo-600"
              : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white",
          )}
        >
          <PlusIcon className="h-4 w-4" />
        </span>
        <span className="truncate">New Chat</span>
      </div>

      <div
        onClick={() => props.enterConfig(null)}
        className={cn(
          !assistantConfig
            ? "bg-gray-50 text-indigo-600"
            : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
          "mt-1 group flex gap-x-3 rounded-md -mx-2 p-2 leading-6 font-semibold cursor-pointer",
        )}
      >
        <span
          className={cn(
            !assistantConfig
              ? "text-indigo-600 border-indigo-600"
              : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white",
          )}
        >
          <PlusIcon className="h-4 w-4" />
        </span>
        <span className="truncate">New Bot</span>
      </div>

      <div className="text-xs font-semibold leading-6 text-gray-400 mt-4">
        Your chats
      </div>
      <ul role="list" className="-mx-2 mt-2 space-y-1">
        {props.chats?.map((chat) => (
          <li
            key={chat.thread_id}
            className={cn(
              chat.thread_id === currentChat?.thread_id
                ? "bg-gray-50 text-indigo-600"
                : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
              "flex justify-between items-center p-2 rounded-md hover:bg-gray-50 cursor-pointer",
            )}
          >
            <div
              onClick={() => props.enterChat(chat.thread_id)}
              className={cn(
                "group flex items-center gap-x-3 rounded-md px-2 leading-6 cursor-pointer flex-grow min-w-0",
              )}
            >
              <span
                className={cn(
                  chat.thread_id === currentChat?.thread_id
                    ? "text-indigo-600 border-indigo-600"
                    : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white",
                )}
              >
                {chat.name?.[0] ?? " "}
              </span>
              <div className="flex flex-col truncate">
                <span className="truncate flex-grow min-w-0">{chat.name}</span>
                <span className="truncate flex-grow min-w-0 text-xs text-gray-400">
                  {
                    props.configs?.find(
                      (config) => config.assistant_id === chat.assistant_id,
                    )?.name
                  }
                </span>
              </div>
            </div>
            {/* Ellipsis Button */}
            <button
              onClick={(event) => {
                event.stopPropagation(); // Prevent triggering click for the chat item
                setVisibleMenu(
                  visibleMenu === chat.thread_id ? null : chat.thread_id,
                );
              }}
              className="p-1 rounded-full hover:bg-gray-200"
            >
              <EllipsisVerticalIcon className="h-5 w-5" />
            </button>
            {/* Menu Dropdown */}
            {visibleMenu === chat.thread_id && (
              <div className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                <div
                  className="py-1"
                  role="menu"
                  aria-orientation="vertical"
                  aria-labelledby="options-menu"
                >
                  <a
                    href="#"
                    className="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100"
                    role="menuitem"
                    onClick={(event) => {
                      event.preventDefault();
                      if (
                        window.confirm(
                          `Are you sure you want to delete chat "${chat.name}"?`,
                        )
                      ) {
                        props.deleteChat(chat.thread_id);
                      }
                    }}
                  >
                    Delete
                  </a>
                </div>
              </div>
            )}
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
