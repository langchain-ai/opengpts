import { PlusIcon, TrashIcon } from "@heroicons/react/24/outline";

import { Config, ConfigListProps } from "../hooks/useConfigList";
import { cn } from "../utils/cn";

function ConfigItem(props: {
  config: Config;
  currentConfig: ConfigListProps["currentConfig"];
  enterConfig: ConfigListProps["enterConfig"];
  removeConfig: ConfigListProps["removeConfig"];
}) {
  return (
    <li key={props.config.assistant_id}>
      <div
        onClick={() => props.enterConfig(props.config.assistant_id)}
        className={cn(
          props.config === props.currentConfig
            ? "bg-gray-50 text-indigo-600"
            : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
          "group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold cursor-pointer"
        )}
      >
        <span
          className={cn(
            props.config === props.currentConfig
              ? "text-indigo-600 border-indigo-600"
              : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white"
          )}
        >
          {props.config.name?.[0] ?? " "}
        </span>
        <span className="truncate w-full">
          {props.config.name}
          <TrashIcon className="text-red-600 hidden float-right group-hover:block h-4 w-4" onClick={() => props.removeConfig(props.config)} />
        </span>
      </div>
    </li>
  );
}

export function ConfigList(props: {
  configs: ConfigListProps["configs"];
  currentConfig: ConfigListProps["currentConfig"];
  enterConfig: ConfigListProps["enterConfig"];
}) {
  return (
    <>
      <div
        onClick={() => props.enterConfig(null)}
        className={cn(
          props.currentConfig === null
            ? "bg-gray-50 text-indigo-600"
            : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
          "group flex gap-x-3 rounded-md -mx-2 p-2 text-sm leading-6 font-semibold cursor-pointer"
        )}
      >
        <span
          className={cn(
            props.currentConfig === null
              ? "text-indigo-600 border-indigo-600"
              : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white"
          )}
        >
          <PlusIcon className="h-4 w-4" />
        </span>
        <span className="truncate">New Bot</span>
      </div>

      <div className="text-xs font-semibold leading-6 text-gray-400 mt-4">
        Your Saved Bots
      </div>
      <ul role="list" className="-mx-2 mt-2 space-y-1">
        {props.configs
          ?.filter((a) => a.mine)
          .map((assistant, index) => (
            <ConfigItem
              key={index}
              config={assistant}
              currentConfig={props.currentConfig}
              enterConfig={props.enterConfig}
              removeConfig={props.removeConfig}
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
          .map((assistant, index) => (
            <ConfigItem
              key={index}
              config={assistant}
              currentConfig={props.currentConfig}
              enterConfig={props.enterConfig}
              removeConfig={props.removeConfig}
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
