import {
  PaperAirplaneIcon,
  ChatBubbleLeftIcon,
  XCircleIcon,
  DocumentPlusIcon,
  DocumentTextIcon,
  DocumentIcon,
} from "@heroicons/react/20/solid";
import { cn } from "../utils/cn";
import { Fragment, useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { MessageWithFiles } from "../utils/formTypes.ts";
import { DROPZONE_CONFIG, TYPE_NAME } from "../constants.ts";
import { Config } from "../hooks/useConfigList.ts";
import { Chat } from "../types";

function getFileTypeIcon(fileType: string) {
  switch (fileType) {
    case "text/plain":
    case "text/csv":
    case "text/html":
      return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
    case "application/pdf":
      return <DocumentIcon className="h-5 w-5 text-red-500" />;
    case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
    case "application/msword":
      return <DocumentIcon className="h-5 w-5 text-blue-500" />;
    default:
      return <DocumentIcon className="h-5 w-5 text-gray-500" />;
  }
}

function FileIcon(props: { fileType: string }) {
  return <div>{getFileTypeIcon(props.fileType)}</div>;
}

function convertBytesToReadableSize(bytes: number) {
  const units = ["bytes", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return `${bytes.toFixed(1)} ${units[i]}`;
}

export default function TypingBox(props: {
  onSubmit: (data: MessageWithFiles) => void;
  onInterrupt?: () => void;
  inflight?: boolean;
  currentConfig: Config;
  currentChat: Chat | null;
}) {
  const [inflight, setInflight] = useState(false);
  const isInflight = props.inflight || inflight;
  const [files, setFiles] = useState<File[]>([]);
  const [isDocumentRetrievalActive, setIsDocumentRetrievalActive] =
    useState(false);

  const { currentConfig, currentChat } = props;

  useEffect(() => {
    let configurable = null;
    if (currentConfig) {
      configurable = currentConfig.config?.configurable;
    }
    const agent_type = configurable?.["type"] as TYPE_NAME | null;
    if (agent_type === null || agent_type === "chatbot") {
      setIsDocumentRetrievalActive(false);
      return;
    }
    if (agent_type === "chat_retrieval") {
      setIsDocumentRetrievalActive(true);
      return;
    }
    const tools =
      (configurable?.["type==agent/tools"] as { name: string }[]) ?? [];
    setIsDocumentRetrievalActive(tools.some((t) => t.name === "Retrieval"));
  }, [currentConfig, currentChat]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prevFiles) => {
      const newFiles = acceptedFiles.filter(
        (acceptedFile) =>
          !prevFiles.some(
            (prevFile) =>
              prevFile.name === acceptedFile.name &&
              prevFile.size === acceptedFile.size,
          ),
      );
      return [...prevFiles, ...newFiles];
    });
  }, []);

  const { open } = useDropzone({
    ...DROPZONE_CONFIG,
    onDrop,
    // Disable click and keydown behavior
    noClick: true,
    noKeyboard: true,
  });

  const FilesToShow = files.map((file) => {
    const readableSize = convertBytesToReadableSize(file.size); // This would be a new utility function.
    return (
      <Fragment key={file.name}>
        <div className="flex items-center">
          <FileIcon fileType={file.type} />{" "}
          {/* New component to render file type icons */}
          <span className="ml-2">{file.name}</span>
        </div>
        <span className="text-sm text-gray-600">{readableSize}</span>
        <span
          className="justify-center not-prose ml-2 inline-flex items-center rounded-full text-xs font-medium cursor-pointer bg-gray-50 text-gray-600 relative top-[1px]"
          onClick={() => setFiles((files) => files.filter((f) => f !== file))}
        >
          <XCircleIcon className="h-4 w-4" />
        </span>
      </Fragment>
    );
  });

  return (
    <div className="flex flex-col">
      {files.length > 0 ? (
        <div
          className={cn(
            "self-end w-fit grid grid-cols-[auto,1fr,auto]" +
              " gap-2 p-2 bg-white rounded-md text-sm text-gray-900" +
              " shadow-sm border border-gray-300",
            isInflight && "opacity-50 cursor-not-allowed",
          )}
        >
          {FilesToShow}
        </div>
      ) : null}
      <form
        className="mt-2 flex rounded-md shadow-sm"
        onSubmit={async (e) => {
          e.preventDefault();
          if (isInflight) return;
          const form = e.target as HTMLFormElement;
          const message = form.message.value;
          if (!message) return;
          setInflight(true);
          await props.onSubmit({ message, files });
          setInflight(false);
          form.message.value = "";
          setFiles([]);
        }}
      >
        {" "}
        <div
          className={cn(
            "relative flex flex-grow items-stretch focus-within:z-10",
            isInflight && "opacity-50 cursor-not-allowed",
          )}
        >
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <ChatBubbleLeftIcon
              className="h-5 w-5 text-gray-400"
              aria-hidden="true"
            />
          </div>
          <input
            type="text"
            name="messsage"
            id="message"
            autoFocus
            autoComplete="off"
            className="block w-full rounded-none rounded-l-md border-0 py-1.5 pl-10 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            placeholder="Send a message"
            readOnly={isInflight}
          />
          {isDocumentRetrievalActive && (
            <div className="cursor-pointer absolute m-1 p-3 inset-y-0 right-0 flex items-center pr-3 hover:bg-gray-50">
              <DocumentPlusIcon
                className="h-5 w-5 text-gray-400"
                aria-hidden="true"
                onClick={open}
              />
            </div>
          )}
        </div>
        <button
          type="submit"
          disabled={isInflight && !props.onInterrupt}
          onClick={
            props.onInterrupt
              ? (e) => {
                  e.preventDefault();
                  props.onInterrupt?.();
                }
              : undefined
          }
          className={cn(
            "relative -ml-px inline-flex items-center gap-x-1.5 rounded-r-md px-3 " +
              "py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 bg-white",
            isInflight && !props.onInterrupt && "opacity-50 cursor-not-allowed",
          )}
        >
          {props.onInterrupt ? (
            <XCircleIcon
              className="-ml-0.5 h-5 w-5 text-gray-400"
              aria-hidden="true"
            />
          ) : (
            <PaperAirplaneIcon
              className="-ml-0.5 h-5 w-5 text-gray-400"
              aria-hidden="true"
            />
          )}
          {isInflight ? (props.onInterrupt ? "Cancel" : "Sending...") : "Send"}
        </button>
      </form>
    </div>
  );
}
