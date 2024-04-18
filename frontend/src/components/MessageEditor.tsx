import { memo } from "react";
import type { Message, ToolCall } from "../types";
import { str } from "../utils/str";
import { cn } from "../utils/cn";
import {
  XCircleIcon,
  PlusCircleIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { StringEditor } from "./StringEditor";
import { JsonEditor } from "./JsonEditor";
import { useThreadAndAssistant } from "../hooks/useThreadAndAssistant";
import { v4 } from "uuid";

function ToolCallEditor(props: {
  value: ToolCall;
  onChange: (newValue: ToolCall) => void;
  onRemove: () => void;
  availableTools: string[];
}) {
  return (
    <div className="flex flex-col">
      <div className="flex w-full items-center gap-2">
        <span className="text-gray-900 whitespace-pre-wrap break-words">
          Use
        </span>
        <div className="flex flex-col">
          {props.value.name !== undefined && (
            <select
              onChange={(e) =>
                props.onChange({ ...props.value, name: e.target.value })
              }
              className="rounded-md bg-gray-50 px-2 py-1 text-sm font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10 -top-[1px] mr-auto focus:ring-0 w-40"
              value={props.value.name}
            >
              {props.availableTools.map((tool) => (
                <option key={tool} value={tool}>
                  {tool}
                </option>
              ))}
            </select>
          )}
        </div>

        <TrashIcon
          className="w-5 h-5 cursor-pointer opacity-50"
          onClick={props.onRemove}
        />
      </div>
      <div className="text-gray-900 whitespace-pre-wrap break-words mt-2 mb-4 ring-1 ring-gray-300 rounded">
        <table className="my-0 divide-gray-300">
          <tbody>
            {Object.entries(props.value.args).map(([key, value], i) => (
              <tr key={i}>
                <td
                  className={cn(
                    i === 0 ? "" : "border-t border-transparent",
                    "p-2 table-cell text-sm border-r border-r-gray-300 w-0 min-w-[128px]",
                  )}
                >
                  <input
                    className="rounded-md font-medium text-sm text-gray-500 px-2 py-1 focus:ring-0"
                    value={key}
                    onChange={(e) => {
                      const newKey = e.target.value;
                      props.onChange({
                        ...props.value,
                        args: Object.fromEntries(
                          Object.entries(props.value.args).map(([k, v]) => [
                            k === key ? newKey : k,
                            v,
                          ]),
                        ),
                      });
                    }}
                  />
                </td>
                <td
                  className={cn(
                    i === 0 ? "" : "border-t border-gray-200",
                    "p-2 table-cell",
                  )}
                >
                  <div className="flex items-center">
                    <StringEditor
                      className="py-0 px-0 prose text-sm leading-normal bg-white"
                      value={str(value)?.toString()}
                      onChange={(newValue) => {
                        props.onChange({
                          ...props.value,
                          args: {
                            ...props.value.args,
                            [key]: newValue,
                          },
                        });
                      }}
                    />
                    <TrashIcon
                      className="w-4 h-4 ml-2 cursor-pointer opacity-50"
                      onClick={() => {
                        props.onChange({
                          ...props.value,
                          args: Object.fromEntries(
                            Object.entries(props.value.args).filter(
                              ([k]) => k !== key,
                            ),
                          ),
                        });
                      }}
                    />
                  </div>
                </td>
              </tr>
            ))}

            <tr>
              <td
                className={cn(
                  "p-2 opacity-50 cursor-pointer flex gap-1 items-center",
                  "" in props.value.args && "opacity-20 pointer-events-none",
                )}
                onClick={
                  "" in props.value.args
                    ? undefined
                    : () => {
                        props.onChange({
                          ...props.value,
                          args: {
                            ...props.value.args,
                            "": "",
                          },
                        });
                      }
                }
              >
                <PlusCircleIcon className="w-6 h-6" />
                Add argument
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ToolCallsEditor(props: {
  message: Message;
  onUpdate: (newValue: Message) => void;
}) {
  const { assistantConfig } = useThreadAndAssistant();
  const availableTools =
    assistantConfig?.config.configurable?.["type==agent/tools"]?.map(
      (t) => t.type,
    ) ?? [];
  if (!props.message.tool_calls?.length && !availableTools.length) {
    return null;
  }
  return (
    <div>
      {props.message.tool_calls?.map((toolCall, i) => (
        <ToolCallEditor
          key={i}
          value={toolCall}
          onChange={(newValue) => {
            props.onUpdate({
              ...props.message,
              tool_calls: props.message.tool_calls?.map((tc, j) =>
                j === i ? newValue : tc,
              ),
            });
          }}
          onRemove={() => {
            props.onUpdate({
              ...props.message,
              tool_calls: props.message.tool_calls?.filter((_, j) => j !== i),
            });
          }}
          availableTools={availableTools}
        />
      ))}
      <div
        className="pl-2 flex items-center gap-1 cursor-pointer opacity-50"
        onClick={() => {
          props.onUpdate({
            ...props.message,
            tool_calls: [
              ...(props.message.tool_calls ?? []),
              { id: v4(), name: availableTools[0], args: {} },
            ],
          });
        }}
      >
        <PlusCircleIcon className={cn("w-6 h-6")} />
        Add tool call
      </div>
    </div>
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
        <div className="prose flex flex-col w-[65ch] gap-2">
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
