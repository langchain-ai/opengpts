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
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

interface NewChatProps extends ConfigListProps {
  configSchema: Schemas["configSchema"];
  configDefaults: Schemas["configDefaults"];
  enterConfig: (id: string | null) => void;
  startChat: (assistantId: string, message: MessageWithFiles) => Promise<void>;
  isDocumentRetrievalActive: boolean;
}

export function NewChat(props: NewChatProps) {
  const navigator = useNavigate();
  const { assistantId } = useParams();
  const [selectedConfig, setSelectedConfig] = useState<ConfigInterface | null>(
    null,
  );

  useEffect(() => {
    if (assistantId) {
      (async () => {
        let matchingConfig =
          props.configs?.find((c) => c.assistant_id === assistantId) ?? null;
        if (!matchingConfig) {
          const response = await fetch(
            `/assistants/public/?shared_id=${assistantId}`,
            {
              headers: {
                Accept: "application/json",
              },
            },
          );
          matchingConfig = await response.json();
        }
        setSelectedConfig(matchingConfig);
      })();
    }
  }, [assistantId, props.configs]);

  return (
    <div
      className={cn(
        "flex flex-col items-stretch",
        selectedConfig ? "pb-[76px]" : "pb-6",
      )}
    >
      <div className="flex-1 flex flex-col md:flex-row lg:items-stretch self-stretch">
        <div className="w-72 border-r border-gray-200 pr-6">
          <ConfigList
            configs={props.configs}
            currentConfig={selectedConfig}
            enterConfig={(id) => navigator(`/assistant/${id}`)}
          />
        </div>

        <main className="flex-1">
          <div className="px-4">
            <Config
              key={assistantId}
              config={selectedConfig}
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
            if (selectedConfig) {
              await props.startChat(selectedConfig.assistant_id, msg);
            }
          }}
          isDocumentRetrievalActive={props.isDocumentRetrievalActive}
        />
      </div>
    </div>
  );
}
