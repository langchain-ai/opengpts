import { PlusIcon } from "@heroicons/react/24/outline";

import { ConfigListProps } from "../hooks/useConfigList";
import { cn } from "../utils/cn";

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
        {props.configs.map((chat) => (
          <li key={chat.key}>
            <div
              onClick={() => props.enterConfig(chat.key)}
              className={cn(
                chat === props.currentConfig
                  ? "bg-gray-50 text-indigo-600"
                  : "text-gray-700 hover:text-indigo-600 hover:bg-gray-50",
                "group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold cursor-pointer"
              )}
            >
              <span
                className={cn(
                  chat === props.currentConfig
                    ? "text-indigo-600 border-indigo-600"
                    : "text-gray-400 border-gray-200 group-hover:border-indigo-600 group-hover:text-indigo-600",
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border text-[0.625rem] font-medium bg-white"
                )}
              >
                {chat.key?.[0] ?? " "}
              </span>
              <span className="truncate">{chat.key}</span>
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
