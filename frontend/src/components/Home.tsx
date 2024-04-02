import { useCallback, useEffect, useMemo, useState } from "react";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import { Chat } from "./Chat";
import { ChatList } from "./ChatList";
import { Layout } from "./Layout";
import { NewChat } from "./NewChat";
import { Chat as ChatType, useChatList } from "../hooks/useChatList.ts";
import { useSchemas } from "../hooks/useSchemas";
import { useStreamState } from "../hooks/useStreamState";
import { useConfigList } from "../hooks/useConfigList";
import { Config } from "./Config";
import { MessageWithFiles } from "../utils/formTypes.ts";
import { TYPE_NAME } from "../constants.ts";

function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { configSchema, configDefaults } = useSchemas();
  const { chats, currentChat, createChat, enterChat } = useChatList();
  const { configs, currentConfig, saveConfig, enterConfig } = useConfigList();
  const { startStream, stopStream, stream } = useStreamState();
  const [isDocumentRetrievalActive, setIsDocumentRetrievalActive] =
    useState(false);

  useEffect(() => {
    let configurable = null;
    if (currentConfig) {
      configurable = currentConfig?.config?.configurable;
    }
    if (currentChat && configs) {
      const conf = configs.find(
        (c) => c.assistant_id === currentChat.assistant_id,
      );
      configurable = conf?.config?.configurable;
    }
    const agent_type = configurable?.["type"] as TYPE_NAME | null;
    if (agent_type === null || agent_type === "chatbot") {
      setIsDocumentRetrievalActive(false);
      return;
    }
    if (agent_type === "chat_retrieval") {
      setIsDocumentRetrievalActive(true);
      return;
    }
    const tools =
      (configurable?.["type==agent/tools"] as { name: string }[]) ?? [];
    setIsDocumentRetrievalActive(tools.some((t) => t.name === "Retrieval"));
  }, [currentConfig, currentChat, configs]);

  const startTurn = useCallback(
    async (message?: MessageWithFiles, chat: ChatType | null = currentChat) => {
      if (!chat) return;
      const config = configs?.find(
        (c) => c.assistant_id === chat.assistant_id,
      )?.config;
      if (!config) return;
      const files = message?.files || [];
      if (files.length > 0) {
        const formData = files.reduce((formData, file) => {
          formData.append("files", file);
          return formData;
        }, new FormData());
        formData.append(
          "config",
          JSON.stringify({ configurable: { thread_id: chat.thread_id } }),
        );
        await fetch(`/ingest`, {
          method: "POST",
          body: formData,
        });
      }
      await startStream(
        message
          ? [
              {
                content: message.message,
                additional_kwargs: {},
                type: "human",
                example: false,
              },
            ]
          : null,
        chat.assistant_id,
        chat.thread_id,
      );
    },
    [currentChat, startStream, configs],
  );

  const startChat = useCallback(
    async (message: MessageWithFiles) => {
      if (!currentConfig) return;
      const chat = await createChat(
        message.message,
        currentConfig.assistant_id,
      );
      return startTurn(message, chat);
    },
    [createChat, startTurn, currentConfig],
  );

  const selectChat = useCallback(
    async (id: string | null) => {
      if (currentChat) {
        stopStream?.(true);
      }
      enterChat(id);
      if (!id) {
        enterConfig(configs?.[0]?.assistant_id ?? null);
        window.scrollTo({ top: 0 });
      }
      if (sidebarOpen) {
        setSidebarOpen(false);
      }
    },
    [enterChat, stopStream, sidebarOpen, currentChat, enterConfig, configs],
  );

  const selectConfig = useCallback(
    (id: string | null) => {
      enterConfig(id);
      enterChat(null);
    },
    [enterConfig, enterChat],
  );

  const content = currentChat ? (
    <Chat
      chat={currentChat}
      startStream={startTurn}
      stopStream={stopStream}
      stream={stream}
      isDocumentRetrievalActive={isDocumentRetrievalActive}
    />
  ) : currentConfig ? (
    <NewChat
      startChat={startChat}
      configSchema={configSchema}
      configDefaults={configDefaults}
      configs={configs}
      currentConfig={currentConfig}
      saveConfig={saveConfig}
      enterConfig={selectConfig}
      isDocumentRetrievalActive={isDocumentRetrievalActive}
    />
  ) : (
    <Config
      className="mb-6"
      config={currentConfig}
      configSchema={configSchema}
      configDefaults={configDefaults}
      saveConfig={saveConfig}
    />
  );

  const currentChatConfig = configs?.find(
    (c) => c.assistant_id === currentChat?.assistant_id,
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
                selectConfig(currentChatConfig.assistant_id);
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
              configs.some((config) => config.assistant_id === c.assistant_id),
            );
          }, [chats, configs])}
          currentChat={currentChat}
          enterChat={selectChat}
          currentConfig={currentConfig}
          enterConfig={selectConfig}
        />
      }
    >
      {configSchema ? content : null}
    </Layout>
  );
}

export default Home;
