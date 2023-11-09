import { useCallback, useEffect, useState } from "react";

export interface Message {
  type: string;
  content: string;
  name?: string;
  additional_kwargs?: {
    function_call?: {
      name?: string;
      arguments?: string;
    };
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
  chats: Chat[];
  currentChat: Chat | null;
  createChat: (
    name: string,
    assistant_id: string,
    thread_id?: string
  ) => Promise<Chat>;
  enterChat: (id: string | null) => void;
}

export function useChatList(): ChatListProps {
  const [chats, setChats] = useState<Chat[]>([]);
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
      thread_id: string = crypto.randomUUID()
    ) => {
      const saved = await fetch(`/threads/${thread_id}`, {
        method: "PUT",
        body: JSON.stringify({ assistant_id, name }),
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      }).then((r) => r.json());
      setChats((chats) => [
        ...chats.filter((c) => c.thread_id !== saved.thread_id),
        saved,
      ]);
      setCurrent(saved.thread_id);
      return saved;
    },
    []
  );

  const enterChat = useCallback((id: string | null) => {
    setCurrent(id);
  }, []);

  return {
    chats,
    currentChat: chats.find((c) => c.thread_id === current) || null,
    createChat,
    enterChat,
  };
}
