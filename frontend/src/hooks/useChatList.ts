import { useCallback, useState } from "react";
import { useStatePersist } from "./useStatePersist";

export interface Message {
  type: string;
  content: string;
  additional_kwargs?: object;
}

export interface Chat {
  id: string;
  name?: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ChatListProps {
  chats: Chat[];
  currentChat: Chat | null;
  createChat: (name: string, messages: Message[]) => Promise<Chat>;
  updateChat: (id: string, update: Partial<Chat>) => Promise<void>;
  enterChat: (id: string | null) => void;
}

export function useChatList(): ChatListProps {
  const [chats, setChats] = useStatePersist<Chat[]>([], "chats");
  const [current, setCurrent] = useState<string | null>(null);

  const createChat = useCallback(
    async (name: string, messages: Message[]) => {
      const chat = {
        id: Math.random().toString(36).substr(2, 9),
        name,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: messages,
      };
      setChats((chats) => [...chats, chat]);
      setCurrent(chat.id);
      return chat;
    },
    [setChats]
  );

  const updateChat = useCallback(
    async (id: string, update: Partial<Chat>) => {
      setChats((chats) =>
        chats.map((chat) => (chat.id === id ? { ...chat, ...update } : chat))
      );
    },
    [setChats]
  );

  const enterChat = useCallback((id: string | null) => {
    setCurrent(id);
  }, []);

  return {
    chats,
    currentChat: chats.find((c) => c.id === current) || null,
    createChat,
    updateChat,
    enterChat,
  };
}
