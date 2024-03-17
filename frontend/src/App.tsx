import { useCallback, useEffect, useMemo, useState } from "react";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import { Chat } from "./components/Chat";
import { ChatList } from "./components/ChatList";
import { Layout } from "./components/Layout";
import { NewChat } from "./components/NewChat";
import { Chat as ChatType, useChatList } from "./hooks/useChatList";
import { useSchemas } from "./hooks/useSchemas";
import { useStreamState } from "./hooks/useStreamState";
import { useConfigList } from "./hooks/useConfigList";
import { Config } from "./components/Config";
import { MessageWithFiles } from "./utils/formTypes.ts";
import { TYPE_NAME } from "./constants.ts";
import { Route, Routes, useNavigate, useParams } from "react-router-dom";

function NotFound() {
  return <div>Page not found.</div>;
}

function App() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { configSchema, configDefaults } = useSchemas();
  const { chats, createChat } = useChatList();
  const { configs, saveConfig } = useConfigList();
  const { startStream, stopStream, stream } = useStreamState();
  const [isDocumentRetrievalActive, setIsDocumentRetrievalActive] =
    useState(false);

  const { assistantId, chatId } = useParams();
  const currentConfig =
    configs?.find((config) => config.assistant_id === assistantId) ?? null;
  const currentChat = chats?.find((chat) => chat.thread_id === chatId) ?? null;

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
      navigate(`/thread/${chat.thread_id}`);
      return startTurn(message, chat);
    },
    [createChat, startTurn, currentConfig],
  );

  const selectChat = useCallback(
    async (id: string | null) => {
      if (currentChat) {
        stopStream?.(true);
      }
      if (!id) {
        const firstAssistant = configs?.[0]?.assistant_id ?? null;
        navigate(firstAssistant ? `/assistant/${firstAssistant}` : "");
        window.scrollTo({ top: 0 });
      } else {
        navigate(`/thread/${id}`);
      }
      if (sidebarOpen) {
        setSidebarOpen(false);
      }
    },
    [stopStream, sidebarOpen, currentChat, configs],
  );

  const selectConfig = useCallback((id: string | null) => {
    navigate(id ? `/assistant/${id}` : "");
  }, []);

  const content = (
    <Routes>
      <Route
        path="/thread/:chatId"
        element={
          <Chat
            chat={currentChat!}
            startStream={startTurn}
            stopStream={stopStream}
            stream={stream}
            isDocumentRetrievalActive={isDocumentRetrievalActive}
          />
        }
      />
      <Route
        path="/thread/new"
        element={
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
        }
      />
      <Route
        path="/assistant/new"
        element={
          <Config
            className="mb-6"
            config={currentConfig}
            configSchema={configSchema}
            configDefaults={configDefaults}
            saveConfig={saveConfig}
            enterConfig={selectConfig}
          />
        }
      />
      <Route
        path="/assistant/:assistantId"
        element={
          <Config
            config={currentConfig}
            className="mb-6"
            configSchema={configSchema}
            configDefaults={configDefaults}
            saveConfig={saveConfig}
            enterConfig={selectConfig}
          />
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
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

export default App;
