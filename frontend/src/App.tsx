import { useCallback, useMemo, useState } from "react";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import { Chat } from "./components/Chat";
import { ChatList } from "./components/ChatList";
import { Layout } from "./components/Layout";
import { NewChat } from "./components/NewChat";
import { Chat as ChatType, useChatList } from "./hooks/useChatList";
import { useSchemas } from "./hooks/useSchemas";
import { useStreamState } from "./hooks/useStreamState";
import { useConfigList } from "./hooks/useConfigList";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { configSchema, configDefaults } = useSchemas();
  const { chats, currentChat, createChat, enterChat } = useChatList();
  const { configs, currentConfig, saveConfig, enterConfig } = useConfigList();
  const { startStream, stopStream, stream } = useStreamState();

  const startTurn = useCallback(
    async (message: string, chat: ChatType | null = currentChat) => {
      if (!chat) return;
      const config = configs?.find(
        (c) => c.assistant_id === chat.assistant_id
      )?.config;
      if (!config) return;
      await startStream(
        {
          messages: [
            {
              content: message,
              additional_kwargs: {},
              type: "human",
              example: false,
            },
          ],
        },
        chat.assistant_id,
        chat.thread_id
      );
    },
    [currentChat, startStream, configs]
  );

  const startChat = useCallback(
    async (message: string) => {
      if (!currentConfig) return;
      const chat = await createChat(message, currentConfig.assistant_id);
      return startTurn(message, chat);
    },
    [createChat, startTurn, currentConfig]
  );

  const selectChat = useCallback(
    async (id: string | null) => {
      if (currentChat) {
        stopStream?.(true);
      }
      enterChat(id);
      if (sidebarOpen) {
        setSidebarOpen(false);
      }
    },
    [enterChat, stopStream, sidebarOpen, currentChat]
  );

  const content = currentChat ? (
    <Chat
      chat={currentChat}
      startStream={startTurn}
      stopStream={stopStream}
      stream={stream}
    />
  ) : (
    <NewChat
      startChat={startChat}
      configSchema={configSchema}
      configDefaults={configDefaults}
      configs={configs}
      currentConfig={currentConfig}
      saveConfig={saveConfig}
      enterConfig={enterConfig}
    />
  );

  const currentChatConfig = configs?.find(
    (c) => c.assistant_id === currentChat?.assistant_id
  );

  return (
    <Layout
      subtitle={
        currentChatConfig ? (
          <span className="inline-flex gap-1 items-center">
            {currentChatConfig.name}
            <InformationCircleIcon
              className="h-5 w-5 cursor-pointer text-indigo-600"
              onClick={() => {
                enterChat(null);
                enterConfig(currentChatConfig.assistant_id);
              }}
            />
          </span>
        ) : null
      }
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      sidebar={
        <ChatList
          chats={useMemo(() => {
            if (configs === null || chats === null) return null;
            return chats.filter((c) =>
              configs.some((config) => config.assistant_id === c.assistant_id)
            );
          }, [chats, configs])}
          currentChat={currentChat}
          enterChat={selectChat}
        />
      }
    >
      {configSchema ? content : null}
    </Layout>
  );
}

export default App;
