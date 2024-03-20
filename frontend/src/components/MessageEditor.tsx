import { memo } from "react";
import type { Message } from "../types";
import { str } from "../utils/str";
import { cn } from "../utils/cn";
import {
  XCircleIcon,
  ChevronDownIcon,
  PlusCircleIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { StringEditor } from "./StringEditor";
import { JsonEditor } from "./JsonEditor";

// TODO adapt (and use) or remove
function Function(props: {
  call: boolean;
  name?: string;
  onNameChange?: (newValue: string) => void;
  argsEntries?: [string, unknown][];
  onArgsEntriesChange?: (newValue: [string, unknown][]) => void;
  onRemovePressed?: () => void;
  open?: boolean;
  setOpen?: (open: boolean) => void;
}) {
  return (
    <div className="flex flex-col mt-1">
      <div className="flex w-full">
        <div className="flex flex-col">
          {props.call && (
            <span className="text-gray-900 whitespace-pre-wrap break-words mr-2 uppercase opacity-50 text-xs mb-1">
              Tool:
            </span>
          )}
          {props.name !== undefined && (
            <input
              onChange={(e) => props.onNameChange?.(e.target.value)}
              className="rounded-md bg-gray-50 px-2 py-1 text-sm font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10 -top-[1px] mr-auto focus:ring-0"
              value={props.name}
            />
          )}
        </div>

        <TrashIcon
          className="w-4 h-4 ml-2 cursor-pointer opacity-50"
          onClick={props.onRemovePressed}
        />
      </div>
      {!props.call && props.setOpen && (
        <span
          className={cn(
            "mr-auto inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-sm font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10 cursor-pointer relative top-1",
            props.open && "mb-2",
          )}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            props.setOpen?.(!props.open);
          }}
        >
          <ChevronDownIcon
            className={cn("h-5 w-5 transition", props.open ? "rotate-180" : "")}
          />
        </span>
      )}
      {props.argsEntries && (
        <div className="text-gray-900 whitespace-pre-wrap break-words">
          <span className="text-gray-900 whitespace-pre-wrap break-words mr-2 uppercase text-xs opacity-50">
            Arguments:
          </span>
          <div className="ring-1 ring-gray-300 rounded">
            <table className="mt-0 divide-gray-300">
              <tbody>
                {props.argsEntries.map(([key, value], i) => (
                  <tr key={i}>
                    <td
                      className={cn(
                        i === 0 ? "" : "border-t border-transparent",
                        "py-1 px-3 table-cell text-sm border-r border-r-gray-300 w-0 min-w-[128px]",
                      )}
                    >
                      <input
                        className="rounded-md font-medium text-sm text-gray-500 px-2 py-1 focus:ring-0"
                        value={key}
                        onChange={(e) => {
                          if (props.argsEntries !== undefined) {
                            props.onArgsEntriesChange?.([
                              ...props.argsEntries.slice(0, i),
                              [e.target.value, value],
                              ...props.argsEntries.slice(i + 1),
                            ]);
                          }
                        }}
                      />
                    </td>
                    <td
                      className={cn(
                        i === 0 ? "" : "border-t border-gray-200",
                        "py-1 px-3 table-cell",
                      )}
                    >
                      <div className="flex items-center">
                        <StringEditor
                          className="py-0 px-0 prose text-sm leading-normal bg-white"
                          value={str(value)?.toString()}
                          onChange={(newValue) => {
                            if (props.argsEntries !== undefined) {
                              props.onArgsEntriesChange?.([
                                ...props.argsEntries.slice(0, i),
                                [key, newValue],
                                ...props.argsEntries.slice(i + 1),
                              ]);
                            }
                          }}
                        />
                        <TrashIcon
                          className="w-4 h-4 ml-2 cursor-pointer opacity-50"
                          onClick={() => {
                            if (props.argsEntries !== undefined) {
                              props.onArgsEntriesChange?.([
                                ...props.argsEntries.slice(0, i),
                                ...props.argsEntries.slice(i + 1),
                              ]);
                            }
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}

                <tr>
                  <td></td>
                  <td className="px-3 py-2">
                    <PlusCircleIcon
                      className="ml-auto w-6 h-6 cursor-pointer opacity-50"
                      onClick={() => {
                        if (props.argsEntries === undefined) {
                          return;
                        }
                        props.onArgsEntriesChange?.([
                          ...props.argsEntries,
                          ["", ""],
                        ]);
                      }}
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export function ToolCallsEditor(props: {
  message: Message;
  onUpdate: (newValue: Message) => void;
}) {
  return (
    <JsonEditor
      value={JSON.stringify(props.message.tool_calls, null, 2)}
      onChange={(newValue) => {
        try {
          props.onUpdate({
            ...props.message,
            tool_calls: JSON.parse(newValue),
          });
        } catch (e) {
          console.error(e);
        }
      }}
    />
  );
}

export function MessageContentEditor(props: {
  message: Message;
  onUpdate: (newValue: Message) => void;
}) {
  if (typeof props.message.content === "string") {
    if (!props.message.content.trim()) {
      return null;
    }
    return (
      <StringEditor
        onChange={(newValue) =>
          props.onUpdate({
            ...props.message,
            content: newValue,
          })
        }
        className="text-gray-900 text-md leading-normal prose min-w-[65ch] bg-white"
        value={props.message.content}
      />
    );
  }
  let content = props.message.content;
  if (Array.isArray(content)) {
    content = content.filter((it) =>
      typeof it === "object" && !!it && "type" in it
        ? it.type !== "tool_use"
        : true,
    );
  }
  if (
    Array.isArray(content)
      ? content.length === 0
      : Object.keys(content).length === 0
  ) {
    return null;
  }

  return (
    <JsonEditor
      value={JSON.stringify(content, null, 2)}
      onChange={(newValue) => {
        try {
          props.onUpdate({
            ...props.message,
            content: JSON.parse(newValue),
          });
        } catch (e) {
          console.error(e);
        }
      }}
    />
  );
}

export const MessageEditor = memo(function (props: {
  message: Message;
  onUpdate: (newValue: Message) => void;
  abandonEdits: () => void;
}) {
  const isToolRes = ["function", "tool"].includes(props.message.type);
  return (
    <div className="flex flex-col mb-8 group">
      <div className="leading-6 flex flex-row">
        <div
          className={cn(
            "flex flex-row space-between mr-4",
            isToolRes && "mt-1",
          )}
        >
          <div className="font-medium text-sm text-gray-400 uppercase mt-1 w-28 flex flex-col">
            {props.message.type}
          </div>

          <XCircleIcon
            className="w-6 h-6 cursor-pointer shrink-0 opacity-40 hover:opacity-100 transition-opacity duration-100"
            onMouseUp={props.abandonEdits}
          />
        </div>
        <div className="prose flex flex-col w-[65ch]">
          <MessageContentEditor
            message={props.message}
            onUpdate={props.onUpdate}
          />
          {props.message.type === "ai" && props.message.tool_calls && (
            <ToolCallsEditor
              message={props.message}
              onUpdate={props.onUpdate}
            />
          )}
        </div>
      </div>
    </div>
  );
});
