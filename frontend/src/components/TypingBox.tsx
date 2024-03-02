import {
  PaperAirplaneIcon,
  ChatBubbleLeftIcon,
  XCircleIcon,
  DocumentPlusIcon,
} from "@heroicons/react/20/solid";
import { cn } from "../utils/cn";
import {useCallback, useState} from "react";
import {useDropzone} from "react-dropzone";
import {MessageWithFiles} from "../utils/formTypes.ts";

export default function TypingBox(props: {
  onSubmit: (data: MessageWithFiles) => Promise<void>;
  onInterrupt?: () => void;
  inflight?: boolean;
}) {
  const [inflight, setInflight] = useState(false);
  const isInflight = props.inflight || inflight;
  const [files, setFiles] = useState<File[]>([])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prevFiles => [...prevFiles, ...acceptedFiles]);
  }, []);

  const {open} = useDropzone({
    onDrop,
    // Disable click and keydown behavior
    noClick: true,
    noKeyboard: true
  });

  const FilesToShow = files.map(file => (
    <li key={file.name}>
      {file.name} - {file.size} bytes
    </li>
  ));

  return (
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
    >{files.length > 0 ? <ul>{FilesToShow}</ul> : null}
      <div
        className={cn(
          "relative flex flex-grow items-stretch focus-within:z-10",
          isInflight && "opacity-50 cursor-not-allowed"
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
        <div className="cursor-pointer absolute inset-y-0 right-0 flex items-center pr-3">
          <DocumentPlusIcon
              className="h-5 w-5 text-gray-400"
              aria-hidden="true"
              onClick={open}
          />
        </div>
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
          "relative -ml-px inline-flex items-center gap-x-1.5 rounded-r-md px-3 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 bg-white",
          isInflight && !props.onInterrupt && "opacity-50 cursor-not-allowed"
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
  );
}
