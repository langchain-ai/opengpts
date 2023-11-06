import { useCallback, useEffect, useState } from "react";
import { Chat } from "./components/Chat";
import { ChatList } from "./components/ChatList";
import { Layout } from "./components/Layout";
import { NewChat } from "./components/NewChat";
import { useChatList } from "./hooks/useChatList";
import { useSchemas } from "./hooks/useSchemas";
import { useStreamState } from "./hooks/useStreamState";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { configSchema, inputSchema, configDefaults, inputDefaults } =
    useSchemas();
  const { chats, currentChat, createChat, updateChat, enterChat } =
    useChatList();
  const { startStream, stopStream, stream } = useStreamState();

  const startChat = useCallback(
    async (message: string) => {
      const chat = await createChat(message, [
        { type: "human", content: message },
      ]);
      return startStream({ messages: chat.messages }, configDefaults);
    },
    [createChat, startStream, configDefaults]
  );

  const startTurn = useCallback(
    async (message: string) => {
      if (!currentChat) return;
      const messages = [
        ...currentChat.messages,
        { type: "human", content: message },
      ];
      await Promise.all([
        updateChat(currentChat.id, { messages }),
        startStream({ messages }, configDefaults),
      ]);
    },
    [currentChat, startStream, configDefaults, updateChat]
  );

  const selectChat = useCallback(
    async (id: string | null) => {
      stopStream?.();
      enterChat(id);
      if (sidebarOpen) {
        setSidebarOpen(false);
      }
    },
    [enterChat, stopStream, sidebarOpen]
  );

  useEffect(() => {
    if (stream?.status === "done" && currentChat) {
      updateChat(currentChat.id, {
        messages: [
          ...currentChat.messages,
          ...stream.messages.filter((m) => !currentChat.messages.includes(m)),
        ],
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream?.status, updateChat]);

  return (
    <Layout
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      sidebar={
        <ChatList
          chats={chats}
          currentChat={currentChat}
          enterChat={selectChat}
        />
      }
    >
      {currentChat ? (
        <Chat
          chat={currentChat}
          startStream={startTurn}
          stopStream={stopStream}
          stream={stream}
        />
      ) : (
        <NewChat startChat={startChat} />
      )}
    </Layout>
  );
}

export default App;
