import { useCallback, useEffect, useReducer, useState } from "react";
import orderBy from "lodash/orderBy";
import { v4 as uuidv4 } from "uuid";

export interface Message {
  type: string;
  content:
    | string
    | { page_content: string; metadata: Record<string, object> }[]
    | object;
  name?: string;
  additional_kwargs?: {
    name?: string;
    function_call?: {
      name?: string;
      arguments?: string;
    };
    tool_calls?: {
      function?: {
        name?: string;
        arguments?: string;
      };
    }[];
  };
  example: boolean;
}

export interface Chat {
  assistant_id: string;
  thread_id: string;
  name: string;
  updated_at: string;
}

export interface ChatListProps {
  chats: Chat[] | null;
  currentChat: Chat | null;
  createChat: (
    name: string,
    assistant_id: string,
    thread_id?: string,
  ) => Promise<Chat>;
  enterChat: (id: string | null) => void;
}

function chatsReducer(
  state: Chat[] | null,
  action: Chat | Chat[],
): Chat[] | null {
  state = state ?? [];
  if (!Array.isArray(action)) {
    const newChat = action;
    action = [
      ...state.filter((c) => c.thread_id !== newChat.thread_id),
      newChat,
    ];
  }
  return orderBy(action, "updated_at", "desc");
}

export function useChatList(): ChatListProps {
  const [chats, setChats] = useReducer(chatsReducer, null);
  const [current, setCurrent] = useState<string | null>(null);

  useEffect(() => {
    async function fetchChats() {
      const chats = await fetch("/threads/", {
        headers: {
          Accept: "application/json",
        },
      }).then((r) => r.json());
      setChats(chats);
    }

    fetchChats();
  }, []);

  const createChat = useCallback(
    async (
      name: string,
      assistant_id: string,
      thread_id: string = uuidv4(),
    ) => {
      const saved = await fetch(`/threads/${thread_id}`, {
        method: "PUT",
        body: JSON.stringify({ assistant_id, name }),
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      }).then((r) => r.json());
      setChats(saved);
      setCurrent(saved.thread_id);
      return saved;
    },
    [],
  );

  const enterChat = useCallback((id: string | null) => {
    setCurrent(id);
  }, []);

  return {
    chats,
    currentChat: chats?.find((c) => c.thread_id === current) || null,
    createChat,
    enterChat,
  };
}
