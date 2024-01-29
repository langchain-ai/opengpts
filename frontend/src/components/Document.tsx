import { useMemo, useState } from "react";
import { cn } from "../utils/cn";

export interface PageDocument {
  page_content: string;
  metadata: Record<string, unknown>;
}

function PageDocument(props: { document: PageDocument; className?: string }) {
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
          "flex min-w-0 max-w-full gap-4 overflow-hidden px-2 transition-colors hover:bg-divider-500/25 active:bg-divider-500/50",
          props.className
        )}
        onClick={() => setOpen(true)}
      >
        <span className="min-w-0 flex-grow overflow-hidden text-ellipsis whitespace-nowrap text-left">
          {props.document.page_content.trim().replace(/\n/g, " ")}
        </span>
      </button>
    );
  }

  return (
    <button
      className={cn(
        "flex gap-4 px-2 text-left transition-colors hover:bg-divider-500/25 active:bg-divider-500/50",
        props.className
      )}
      onClick={() => setOpen(false)}
    >
      <span className="flex flex-col gap-4">
        <span className="whitespace-pre-wrap">
          {props.document.page_content}
        </span>

        <span className="flex flex-col flex-wrap items-start gap-2">
          {metadata.map(({ key, value }, idx) => {
            return (
              <span
                className="rounded-md bg-divider-500 p-1 px-1.5 text-xs"
                key={idx}
              >
                <span className="mr-1.5 font-mono font-bold">{key}</span>
                <span className="whitespace-pre-wrap">{value}</span>
              </span>
            );
          })}
        </span>
      </span>
    </button>
  );
}

export function DocumentList(props: { documents: PageDocument[] }) {
  return (
    <div className="flex flex-col items-stretch gap-4 rounded-lg ring-1 ring-gray-300 overflow-hidden">
      <div className="mx-2 grid divide-y empty:hidden">
        {props.documents.map((document, idx) => (
          <PageDocument document={document} key={idx} className="py-3" />
        ))}
      </div>
    </div>
  );
}
