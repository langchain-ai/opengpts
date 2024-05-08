import { TYPES } from "../constants";
import { Config, ConfigListProps } from "../hooks/useConfigList";
import { cn } from "../utils/cn";
import { PencilSquareIcon, TrashIcon } from "@heroicons/react/24/outline";
import { Link } from "react-router-dom";

function ConfigItem(props: {
  config: Config;
  currentConfig: Config | null;
  enterConfig: (id: string | null) => void;
  deleteConfig: (id: string) => void;
}) {
  return (
    <li key={props.config.assistant_id}>
      <div
        onClick={() => props.enterConfig(props.config.assistant_id)}
        className={cn(
          props.config.assistant_id === props.currentConfig?.assistant_id
            ? "bg-gray-50 text-indigo-600"
            : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
          "group flex gap-x-3 rounded-md p-2 leading-6 cursor-pointer",
        )}
      >
        <span
          className={cn(
            props.config.assistant_id === props.currentConfig?.assistant_id
              ? "text-indigo-600 border-indigo-600"
              : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white",
          )}
        >
          {props.config.name?.[0] ?? " "}
        </span>
        <div className="flex flex-col">
          <span className="truncate text-sm font-medium">
            {props.config.name}
          </span>
          <span className="truncate text-xs">
            {
              TYPES[
                (props.config.config.configurable?.type ??
                  "agent") as keyof typeof TYPES
              ]?.title
            }
          </span>
        </div>
        <Link
          className="ml-auto w-5"
          to={`/assistant/${props.config.assistant_id}/edit`}
          onClick={(event) => event.stopPropagation()}
        >
          <PencilSquareIcon />
        </Link>
        <Link
          className="w-5"
          to="#"
          onClick={(event) => {
            event.preventDefault();
            if (
              window.confirm(
                `Are you sure you want to delete bot "${props.config.name}?"`,
              )
            ) {
              props.deleteConfig(props.config.assistant_id);
            }
          }}
        >
          <TrashIcon />
        </Link>
      </div>
    </li>
  );
}

export function ConfigList(props: {
  configs: ConfigListProps["configs"];
  currentConfig: Config | null;
  enterConfig: (id: string | null) => void;
  deleteConfig: (id: string) => void;
}) {
  return (
    <>
      <div className="text-xs font-semibold leading-6 text-gray-400">
        Your Saved Bots
      </div>
      <ul role="list" className="-mx-2 mt-2 space-y-1">
        {props.configs
          ?.filter((a) => a.mine)
          .map((assistant) => (
            <ConfigItem
              key={assistant.assistant_id}
              config={assistant}
              currentConfig={props.currentConfig}
              enterConfig={props.enterConfig}
              deleteConfig={props.deleteConfig}
            />
          )) ?? (
          <li className="leading-6 p-2 animate-pulse font-black text-gray-400 text-lg">
            ...
          </li>
        )}
      </ul>

      <div className="text-xs font-semibold leading-6 text-gray-400 mt-4">
        Public Bots
      </div>
      <ul role="list" className="-mx-2 mt-2 space-y-1">
        {props.configs
          ?.filter((a) => !a.mine)
          .map((assistant) => (
            <ConfigItem
              key={assistant.assistant_id}
              config={assistant}
              currentConfig={props.currentConfig}
              enterConfig={props.enterConfig}
              deleteConfig={props.deleteConfig}
            />
          )) ?? (
          <li className="leading-6 p-2 animate-pulse font-black text-gray-400 text-lg">
            ...
          </li>
        )}
      </ul>
    </>
  );
}
