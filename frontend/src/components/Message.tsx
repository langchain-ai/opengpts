import { memo, useState } from "react";
import { MessageDocument, Message as MessageType } from "../types";
import { str } from "../utils/str";
import { cn } from "../utils/cn";
import { PencilSquareIcon } from "@heroicons/react/24/outline";
import { LangSmithActions } from "./LangSmithActions";
import { DocumentList } from "./Document";
import { omit } from "lodash";
import { StringViewer } from "./String";
import { ToolRequest, ToolResponse } from "./Tool";

function isDocumentContent(
  content: MessageType["content"],
): content is MessageDocument[] {
  return (
    Array.isArray(content) &&
    content.every((d) => typeof d === "object" && !!d && !!d.page_content)
  );
}

export function MessageContent(props: { content: MessageType["content"] }) {
  if (typeof props.content === "string") {
    if (!props.content.trim()) {
      return null;
    }
    return <StringViewer value={props.content} markdown />;
  } else if (isDocumentContent(props.content)) {
    return <DocumentList documents={props.content} />;
  } else if (
    Array.isArray(props.content) &&
    props.content.every(
      (it) => typeof it === "object" && !!it && typeof it.content === "string",
    )
  ) {
    return (
      <DocumentList
        markdown
        documents={props.content.map((it) => ({
          page_content: it.content,
          metadata: omit(it, "content"),
        }))}
      />
    );
  } else {
    let content = props.content;
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
    return <div className="text-gray-900 prose">{str(content)}</div>;
  }
}

export const MessageViewer = memo(function (
  props: MessageType & {
    runId?: string;
    startEditing?: () => void;
    alwaysShowControls?: boolean;
  },
) {
  const [open, setOpen] = useState(false);
  const contentIsDocuments =
    ["function", "tool"].includes(props.type) &&
    isDocumentContent(props.content);
  const showContent =
    ["function", "tool"].includes(props.type) && !contentIsDocuments
      ? open
      : true;
  return (
    <div className="flex flex-col mb-8 group">
      <div className="leading-6 flex flex-row">
        <div
          className={cn(
            "flex flex-row space-between mr-4",
            ["function", "tool"].includes(props.type) && "mt-1",
          )}
        >
          <div className="font-medium text-sm text-gray-400 uppercase mt-1 w-28 flex flex-col">
            {props.type}
          </div>
          {props.startEditing && (
            <PencilSquareIcon
              className={cn(
                "w-6 h-6 cursor-pointer shrink-0 transition-opacity duration-100",
                props.alwaysShowControls
                  ? "opacity-40 hover:opacity-90"
                  : "opacity-0 group-hover:opacity-40 group-hover:hover:opacity-90",
              )}
              onMouseUp={props.startEditing}
            />
          )}
        </div>
        <div className="flex-1">
          {["function", "tool"].includes(props.type) && (
            <ToolResponse
              name={props.name}
              open={open}
              setOpen={contentIsDocuments ? undefined : setOpen}
            />
          )}
          {props.tool_calls?.map((call) => (
            <ToolRequest key={call.id} {...call} />
          ))}
          {showContent && <MessageContent content={props.content} />}
        </div>
      </div>
      {props.runId && (
        <div className="mt-2 pl-[148px]">
          <LangSmithActions runId={props.runId} />
        </div>
      )}
    </div>
  );
});
