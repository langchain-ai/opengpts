import { ConfigList } from "./ConfigList";
import { Schemas } from "../hooks/useSchemas";
import TypingBox from "./TypingBox";
import { Config } from "./Config";
import { ConfigListProps } from "../hooks/useConfigList";
import { cn } from "../utils/cn";
import { MessageWithFiles } from "../utils/formTypes.ts";

interface NewChatProps extends ConfigListProps {
  configSchema: Schemas["configSchema"];
  configDefaults: Schemas["configDefaults"];
  startChat: (message: MessageWithFiles) => Promise<void>;
  isDocumentRetrievalActive: boolean;
}

export function NewChat(props: NewChatProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-stretch",
        props.currentConfig ? "pb-[76px]" : "pb-6",
      )}
    >
      <div className="flex-1 flex flex-col md:flex-row lg:items-stretch self-stretch">
        <div className="w-72 border-r border-gray-200 pr-6">
          <ConfigList
            configs={props.configs}
            currentConfig={props.currentConfig}
            enterConfig={props.enterConfig}
          />
        </div>

        <main className="flex-1">
          <div className="px-4">
            <Config
              key={props.currentConfig?.assistant_id}
              config={props.currentConfig}
              configSchema={props.configSchema}
              configDefaults={props.configDefaults}
              saveConfig={props.saveConfig}
            />
          </div>
        </main>
      </div>
      <div className="fixed left-0 lg:left-72 bottom-0 right-0 p-4">
        <TypingBox
          onSubmit={props.startChat}
          isDocumentRetrievalActive={props.isDocumentRetrievalActive}
        />
      </div>
    </div>
  );
}
