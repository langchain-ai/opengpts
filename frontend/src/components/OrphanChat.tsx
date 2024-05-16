import { useEffect, useState } from "react";
import { Config } from "../hooks/useConfigList";
import { Chat } from "../types";
import { getAssistants } from "../api/assistants";
import { useThreadAndAssistant } from "../hooks/useThreadAndAssistant";

export function OrphanChat(props: {
  chat: Chat;
  updateChat: (
    name: string,
    thread_id: string,
    assistant_id: string | null,
  ) => Promise<Chat>;
}) {
  const [newConfigId, setNewConfigId] = useState(null as string | null);
  const [configs, setConfigs] = useState<Config[]>([]);
  const { invalidateChat } = useThreadAndAssistant();

  const update = async () => {
    if (!newConfigId) {
      alert("Please select a bot.");
      return;
    }
    const updatedChat = await props.updateChat(
      props.chat.thread_id,
      props.chat.name,
      newConfigId,
    );
    invalidateChat(updatedChat.thread_id);
  };

  const botTypeToName = (botType: string) => {
    switch (botType) {
      case "chatbot":
        return "Chatbot";
      case "chat_retrieval":
        return "RAG";
      case "agent":
        return "Assistant";
      default:
        return botType;
    }
  };

  useEffect(() => {
    async function fetchConfigs() {
      const configs = await getAssistants();
      const suitableConfigs = configs
        ? configs.filter(
            (config) =>
              config.config.configurable?.type ===
              props.chat.metadata?.assistant_type,
          )
        : [];
      setConfigs(suitableConfigs);
    }

    fetchConfigs();
  }, [props.chat.metadata?.assistant_type]);

  return (
    <div className="flex-1 flex flex-col items-stretch pb-[76px] pt-2">
      {configs.length ? (
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            await update();
          }}
          className="space-y-4 max-w-xl w-full px-4"
        >
          <div className="inline-flex items-center rounded-md bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-700">
            This chat has no bot attached. To continue chatting, please attach a
            bot.
          </div>
          <div className="flex flex-row flex-1">
            <div className="relative flex flex-grow items-stretch focus-within:z-10">
              <select
                className="block w-full rounded-none rounded-l-md border-0 py-1.5 pl-4 text-gray-900 ring-1 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 ring-inset ring-gray-300"
                onChange={(event) => setNewConfigId(event.target.value)}
              >
                <option value="">Select a bot</option>
                {configs.map((config, index) => (
                  <option key={index} value={config.assistant_id}>
                    {config.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm leading-5 font-medium rounded-r-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600"
            >
              Save
            </button>
          </div>
        </form>
      ) : (
        <div className="inline-flex items-center px-2 py-1">
          <div className="rounded-md bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-700">
            This chat has no bot attached. To continue chatting, you need to
            attach a bot. However, there are no suitable bots available for this
            chat. Please create a new bot with type{" "}
            {botTypeToName(props.chat.metadata?.assistant_type as string)} and
            try again.
          </div>
        </div>
      )}
    </div>
  );
}
