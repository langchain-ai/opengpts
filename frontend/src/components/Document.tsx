import { useMemo, useState } from "react";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/outline";
import { cn } from "../utils/cn";
import { MessageDocument } from "../types";
import { StringViewer } from "./String";

function isValidHttpUrl(str: string) {
  let url;

  try {
    url = new URL(str);
  } catch (_) {
    return false;
  }

  return url.protocol === "http:" || url.protocol === "https:";
}

function DocumentViewer(props: {
  document: MessageDocument;
  markdown?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  const metadata = useMemo(() => {
    return Object.keys(props.document.metadata)
      .sort((a, b) => {
        const aValue = JSON.stringify(props.document.metadata[a]);
        const bValue = JSON.stringify(props.document.metadata[b]);

        const aLines = aValue.split("\n");
        const bLines = bValue.split("\n");

        if (aLines.length !== bLines.length) {
          return aLines.length - bLines.length;
        }

        return aValue.length - bValue.length;
      })
      .map((key) => {
        const value = props.document.metadata[key];
        return {
          key,
          value:
            typeof value === "string" || typeof value === "number"
              ? `${value}`
              : JSON.stringify(value),
        };
      });
  }, [props.document.metadata]);

  if (!open) {
    return (
      <button
        className={cn(
          "flex items-start min-w-0 max-w-full gap-4 overflow-hidden px-4 transition-colors hover:bg-gray-50/50 active:bg-gray-50",
          props.className,
        )}
        onClick={() => setOpen(true)}
      >
        <ChevronRightIcon className="mt-[6px] h-4 w-4 text-gray-500" />
        <StringViewer
          className="min-w-0 flex-grow basis-0 overflow-hidden text-ellipsis whitespace-nowrap text-left max-w-none"
          value={props.document.page_content.trim().replace(/\n/g, " ")}
        />
      </button>
    );
  }

  return (
    <div
      className={cn(
        "flex items-start gap-4 px-4 text-left transition-colors hover:bg-gray-50/50 active:bg-gray-50",
        props.className,
      )}
    >
      <button onClick={() => setOpen(false)}>
        <ChevronDownIcon className="mt-[6px] h-4 w-4 text-gray-500" />
      </button>

      <span className="flex flex-grow basis-0 flex-col gap-4">
        <StringViewer
          value={props.document.page_content}
          markdown={props.markdown}
        />

        <span className="flex flex-col flex-wrap items-start gap-2">
          {metadata.map(({ key, value }, idx) => {
            return (
              <span
                className="rounded-md bg-divider-500 p-1 px-1.5 text-xs"
                key={idx}
              >
                <span className="mr-1.5 font-mono font-bold">{key}</span>
                {isValidHttpUrl(value) ? (
                  <a href={value} target="_blank" rel="noreferrer">
                    {value}
                  </a>
                ) : (
                  <span className="whitespace-pre-wrap">{value}</span>
                )}
              </span>
            );
          })}
        </span>
      </span>
    </div>
  );
}

export function DocumentList(props: {
  documents: MessageDocument[];
  markdown?: boolean;
}) {
  return (
    <div className="flex flex-col items-stretch gap-4 rounded-lg ring-1 ring-gray-300 overflow-hidden my-2">
      <div className="grid divide-y empty:hidden">
        {props.documents.map((document, idx) => (
          <DocumentViewer
            document={document}
            key={idx}
            className="py-3"
            markdown={props.markdown}
          />
        ))}
      </div>
    </div>
  );
}
