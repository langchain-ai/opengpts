import { ConfigList } from "./ConfigList";
import { Schemas } from "../hooks/useSchemas";
import TypingBox from "./TypingBox";
import { Config } from "./Config";
import {
  ConfigListProps,
  Config as ConfigInterface,
} from "../hooks/useConfigList";
import { cn } from "../utils/cn";
import { MessageWithFiles } from "../utils/formTypes.ts";
import { useNavigate, useParams } from "react-router-dom";
import { useThreadAndAssistant } from "../hooks/useThreadAndAssistant.ts";

interface NewChatProps extends ConfigListProps {
  configSchema: Schemas["configSchema"];
  configDefaults: Schemas["configDefaults"];
  enterConfig: (id: string | null) => void;
  deleteConfig: (id: string) => Promise<void>;
  startChat: (
    config: ConfigInterface,
    message: MessageWithFiles,
  ) => Promise<void>;
}

export function NewChat(props: NewChatProps) {
  const navigator = useNavigate();
  const { assistantId } = useParams();

  const { assistantConfig, isLoading } = useThreadAndAssistant();

  if (isLoading) return <div>Loading...</div>;
  if (!assistantConfig)
    return <div>Could not find assistant with given id.</div>;

  return (
    <div
      className={cn(
        "flex flex-col items-stretch",
        assistantConfig ? "pb-[76px]" : "pb-6",
      )}
    >
      <div className="flex-1 flex flex-col md:flex-row lg:items-stretch self-stretch">
        <div className="md:w-72 border-r border-gray-200 pr-6">
          <ConfigList
            configs={props.configs}
            currentConfig={assistantConfig}
            enterConfig={(id) => navigator(`/assistant/${id}`)}
            deleteConfig={props.deleteConfig}
          />
        </div>

        <main className="flex-1">
          <div className="px-4">
            <Config
              key={assistantId}
              config={assistantConfig}
              configSchema={props.configSchema}
              configDefaults={props.configDefaults}
              saveConfig={props.saveConfig}
              enterConfig={props.enterConfig}
            />
          </div>
        </main>
      </div>
      <div className="fixed left-0 lg:left-72 bottom-0 right-0 p-4">
        <TypingBox
          onSubmit={async (msg: MessageWithFiles) => {
            if (assistantConfig) {
              await props.startChat(assistantConfig, msg);
            }
          }}
          currentConfig={assistantConfig}
          currentChat={null}
        />
      </div>
    </div>
  );
}
