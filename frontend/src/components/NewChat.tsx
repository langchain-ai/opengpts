import { ConfigList } from "./ConfigList";
import { useConfigList } from "../hooks/useConfigList";
import TypingBox from "./TypingBox";

export function NewChat(props: {
  startChat: (message: string) => Promise<void>;
}) {
  const { configs, currentConfig, saveConfig, enterConfig } = useConfigList();
  return (
    <div className="flex flex-col items-stretch">
      <div className="flex-1 flex flex-col lg:flex-row lg:items-stretch self-stretch">
        <div className="w-72 border-r border-gray-200 pr-6">
          <ConfigList
            configs={configs}
            currentConfig={currentConfig}
            enterConfig={enterConfig}
          />
        </div>

        <main className="flex-1">
          <div className="px-4">[Config fields go here]</div>
        </main>
      </div>
      <div className="fixed left-0 lg:left-72 bottom-0 right-0 p-4">
        <TypingBox onSubmit={props.startChat} />
      </div>
    </div>
  );
}
