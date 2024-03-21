import { useCallback, useMemo, useState } from "react";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import { Chat } from "./components/Chat";
import { ChatList } from "./components/ChatList";
import { Layout } from "./components/Layout";
import { NewChat } from "./components/NewChat";
import { useChatList } from "./hooks/useChatList";
import { useSchemas } from "./hooks/useSchemas";
import { useStreamState } from "./hooks/useStreamState";
import {
  useConfigList,
  Config as ConfigInterface,
} from "./hooks/useConfigList";
import { Config } from "./components/Config";
import { MessageWithFiles } from "./utils/formTypes.ts";
import { Route, Routes, useNavigate } from "react-router-dom";
import { useThreadAndAssistant } from "./hooks/useThreadAndAssistant.ts";
import { NotFound } from "./components/NotFound.tsx";

function App() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { chats, createChat } = useChatList();
  const { configs, saveConfig } = useConfigList();
  const { startStream, stopStream, stream } = useStreamState();
  const { configSchema, configDefaults } = useSchemas();

  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const currentChat =
    chats?.find((chat) => chat.thread_id === currentChatId) ?? null;
  const [assistantConfig, setAssistantConfig] = useState<ConfigInterface | null>(null);

  const startTurn = useCallback(
    async (
      message: MessageWithFiles | null,
      thread_id: string,
      assistant_id: string,
    ) => {
      const files = message?.files || [];
      if (files.length > 0) {
        const formData = files.reduce((formData, file) => {
          formData.append("files", file);
          return formData;
        }, new FormData());
        formData.append(
          "config",
          JSON.stringify({ configurable: { thread_id } }),
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
        assistant_id,
        thread_id,
      );
    },
    [startStream],
  );

  const startChat = useCallback(
    async (config: ConfigInterface, message: MessageWithFiles) => {
      const chat = await createChat(message.message, config.assistant_id);
      navigate(`/thread/${chat.thread_id}`);
      return startTurn(message, chat.thread_id, chat.assistant_id);
    },
    [createChat, navigate, startTurn],
  );

  const selectChat = useCallback(
    async (id: string | null) => {
      if (currentChat) {
        stopStream?.(true);
      }
      if (!id) {
        const firstAssistant = configs?.[0]?.assistant_id ?? null;
        navigate(firstAssistant ? `/assistant/${firstAssistant}` : "/");
        window.scrollTo({ top: 0 });
      } else {
        navigate(`/thread/${id}`);
      }
      if (sidebarOpen) {
        setSidebarOpen(false);
      }
    },
    [currentChat, sidebarOpen, stopStream, configs, navigate],
  );

  const selectConfig = useCallback(
    (id: string | null) => {
      setCurrentChatId(null);
      navigate(id ? `/assistant/${id}` : "/");
    },
    [navigate],
  );

  return (
    <Layout
      subtitle={
        assistantConfig ? (
          <span className="inline-flex gap-1 items-center">
            {assistantConfig.name}
            <InformationCircleIcon
              className="h-5 w-5 cursor-pointer text-indigo-600"
              onClick={() => {
                selectConfig(assistantConfig.assistant_id);
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
            return chats;
          }, [chats, configs])}
          currentChat={currentChat}
          enterChat={selectChat}
          currentConfig={assistantConfig || null}
          enterConfig={selectConfig}
        />
      }
    >
      <Routes>
        <Route
          path="/thread/:chatId"
          element={
            <Chat
              startStream={startTurn}
              stopStream={stopStream}
              stream={stream}
              setCurrentChatId={setCurrentChatId}
              setCurrentConfig={setAssistantConfig}
            />
          }
        />
        <Route
          path="/assistant/:assistantId"
          element={
            <NewChat
              startChat={startChat}
              configSchema={configSchema}
              configDefaults={configDefaults}
              configs={configs}
              saveConfig={saveConfig}
              enterConfig={selectConfig}
              setCurrentConfig={setAssistantConfig}
            />
          }
        />
        <Route
          path="/"
          element={
            <Config
              className="mb-6"
              config={null}
              configSchema={configSchema}
              configDefaults={configDefaults}
              saveConfig={saveConfig}
              enterConfig={selectConfig}
              setCurrentConfig={setAssistantConfig}
            />
          }
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

export default App;
