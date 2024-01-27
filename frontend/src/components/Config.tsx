import { useEffect, useState } from "react";
import { marked } from "marked";
import { ShareIcon } from "@heroicons/react/24/outline";
import { useDropzone } from "react-dropzone";
import { orderBy } from "lodash";

import { ConfigListProps } from "../hooks/useConfigList";
import { SchemaField, Schemas } from "../hooks/useSchemas";
import { cn } from "../utils/cn";
import { FileUploadDropzone } from "./FileUpload";

const TYPES = {
  assistant: {
    id: "assistant",
    title: "Assistant",
    description:
      "A general-purpose assistant that can answer questions and use tools.",
  },
  chatbot: {
    id: "chatbot",
    title: "Chatbot",
    description: "A chatbot that can answer questions and have conversations.",
  },
  chat_retrieval: {
    id: "chat_retrieval",
    title: "RAG",
    description: "Chat with your documents as if they were people.",
  },
};

function Types(props: {
  field: SchemaField;
  value: string;
  readonly: boolean;
  setValue: (value: string) => void;
  alwaysExpanded?: boolean;
}) {
  const options =
    props.field.enum?.map((id) => TYPES[id as keyof typeof TYPES]) ?? [];
  return (
    <div>
      <div className="sm:hidden">
        <label htmlFor="tabs" className="sr-only">
          Select a tab
        </label>
        {/* Use an "onChange" listener to redirect the user to the selected tab URL. */}
        <select
          id="tabs"
          name="tabs"
          className="block w-full rounded-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
          defaultValue={options.find((o) => o.id === props.value)?.id}
          onChange={(e) => props.setValue(e.target.value)}
        >
          {options.map((option) => (
            <option key={option.id}>{option.title}</option>
          ))}
        </select>
      </div>
      <div className="hidden sm:block">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex" aria-label="Tabs">
            {options.map((option) => (
              <div
                key={option.id}
                className={cn(
                  props.value === option.id
                    ? "border-indigo-500 text-indigo-600"
                    : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700",
                  "w-1/4 border-b-2 py-4 px-1 text-center text-sm font-medium"
                )}
                aria-current={props.value === option.id ? "page" : undefined}
                onClick={() => props.setValue(option.id)}
              >
                {option.title}
              </div>
            ))}
          </nav>
        </div>
      </div>
    </div>
  );
}

function Label(props: { id: string; title: string }) {
  return (
    <label
      htmlFor={props.id}
      className="block font-medium leading-6 text-gray-400 mb-2"
    >
      {props.title}
    </label>
  );
}

function StringField(props: {
  id: string;
  field: SchemaField;
  value: string;
  title: string;
  readonly: boolean;
  setValue: (value: string) => void;
}) {
  return (
    <div>
      <Label id={props.id} title={props.title} />
      <textarea
        rows={4}
        name={props.id}
        id={props.id}
        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
        value={props.value}
        readOnly={props.readonly}
        disabled={props.readonly}
        onChange={(e) => props.setValue(e.target.value)}
      />
    </div>
  );
}

export default function SingleOptionField(props: {
  id: string;
  field: SchemaField;
  value: string;
  title: string;
  readonly: boolean;
  setValue: (value: string) => void;
}) {
  return (
    <div>
      <Label id={props.id} title={props.title} />
      <fieldset>
        <legend className="sr-only">{props.field.title}</legend>
        <div className="space-y-2">
          {orderBy(props.field.enum)?.map((option) => (
            <div key={option} className="flex items-center">
              <input
                id={`${props.id}-${option}`}
                name={props.id}
                type="radio"
                checked={option === props.value}
                className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-600"
                disabled={props.readonly}
                onChange={() => props.setValue(option)}
              />
              <label
                htmlFor={`${props.id}-${option}`}
                className="ml-3 block leading-6 text-gray-900"
              >
                {option}
              </label>
            </div>
          ))}
        </div>
      </fieldset>
    </div>
  );
}

const TOOL_DESCRIPTIONS = {
  Retrieval: "Look up information in uploaded files.",
  "DDG Search":
    "Search the web with [DuckDuckGo](https://pypi.org/project/duckduckgo-search/).",
  "Search (Tavily)":
    "Uses the [Tavily](https://app.tavily.com/) search engine. Includes sources in the response.",
  "Search (short answer, Tavily)":
    "Uses the [Tavily](https://app.tavily.com/) search engine. This returns only the answer, no supporting evidence.",
  "You.com Search":
    "Uses [You.com](https://you.com/) search, optimized responses for LLMs.",
  "SEC Filings (Kay.ai)":
    "Searches through SEC filings using [Kay.ai](https://www.kay.ai/).",
  "Press Releases (Kay.ai)":
    "Searches through press releases using [Kay.ai](https://www.kay.ai/).",
  Arxiv: "Searches [Arxiv](https://arxiv.org/).",
  PubMed: "Searches [PubMed](https://pubmed.ncbi.nlm.nih.gov/).",
  Wikipedia: "Searches [Wikipedia](https://pypi.org/project/wikipedia/).",
};

function MultiOptionField(props: {
  id: string;
  field: SchemaField;
  value: string[];
  title: string;
  readonly: boolean;
  setValue: (value: string[]) => void;
  descriptions?: Record<string, string>;
}) {
  return (
    <fieldset>
      <Label id={props.id} title={props.title ?? props.field.items?.title} />
      <div className="space-y-2">
        {orderBy(props.field.items?.enum)?.map((option) => (
          <div className="relative flex items-start" key={option}>
            <div className="flex h-6 items-center">
              <input
                id={`${props.id}-${option}`}
                aria-describedby="comments-description"
                name={`${props.id}-${option}`}
                type="checkbox"
                checked={props.value.includes(option)}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
                disabled={props.readonly}
                onChange={(e) => {
                  if (e.target.checked) {
                    props.setValue([...props.value, option]);
                  } else {
                    props.setValue(props.value.filter((v) => v !== option));
                  }
                }}
              />
            </div>
            <div className="ml-3 text-sm leading-6">
              <label
                htmlFor={`${props.id}-${option}`}
                className="text-gray-900"
              >
                {option}
              </label>
              {props.descriptions?.[option] && (
                <div
                  className="text-gray-500 prose prose-sm prose-a:text-gray-500"
                  dangerouslySetInnerHTML={{
                    __html: marked(props.descriptions[option]),
                  }}
                ></div>
              )}
            </div>
          </div>
        ))}
      </div>
    </fieldset>
  );
}

function PublicLink(props: { assistantId: string }) {
  const currentLink = window.location.href;
  const link = currentLink.includes("shared_id=")
    ? currentLink
    : currentLink + "?shared_id=" + props.assistantId;
  return (
    <div className="flex rounded-md shadow-sm mb-4">
      <button
        type="submit"
        className="relative -ml-px inline-flex items-center gap-x-1.5 rounded-l-md px-3 py-2 text-sm font-semibold text-gray-900 border border-gray-300 hover:bg-gray-50 bg-white"
        onClick={async (e) => {
          e.preventDefault();
          e.stopPropagation();
          await navigator.clipboard.writeText(link);
          window.alert("Copied to clipboard!");
        }}
      >
        <ShareIcon
          className="-ml-0.5 h-5 w-5 text-gray-400"
          aria-hidden="true"
        />
        Copy Public Link
      </button>
      <a
        className="rounded-none rounded-r-md py-1.5 px-2 text-gray-900 border border-l-0 border-gray-300 text-sm leading-6 line-clamp-1 flex-1 underline"
        href={link}
      >
        {link}
      </a>
    </div>
  );
}

function fileId(file: File) {
  return `${file.name}-${file.size}-${file.lastModified}`;
}

export function Config(props: {
  className?: string;
  configSchema: Schemas["configSchema"];
  configDefaults: Schemas["configDefaults"];
  config: ConfigListProps["currentConfig"];
  saveConfig: ConfigListProps["saveConfig"];
}) {
  const [values, setValues] = useState(
    props.config?.config ?? props.configDefaults
  );
  const [files, setFiles] = useState<File[]>([]);
  const dropzone = useDropzone({
    multiple: true,
    accept: {
      "text/*": [".txt", ".csv", ".htm", ".html"],
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
      "application/msword": [".doc"],
    },
    maxSize: 10_000_000, // Up to 10 MB file size.
  });
  const [isPublic, setPublic] = useState(props.config?.public ?? false);
  useEffect(() => {
    setValues(props.config?.config ?? props.configDefaults);
  }, [props.config, props.configDefaults]);
  useEffect(() => {
    if (dropzone.acceptedFiles.length > 0) {
      setValues((values) => ({
        configurable: {
          ...values?.configurable,
          tools: [
            ...((values?.configurable?.tools ?? []) as string[]).filter(
              (tool) => tool !== "Retrieval"
            ),
            "Retrieval",
          ],
        },
      }));
      const acceptedFileIds = dropzone.acceptedFiles.map(fileId);
      setFiles((files) => [
        ...files.filter((f) => !acceptedFileIds.includes(fileId(f))),
        ...dropzone.acceptedFiles,
      ]);
    }
  }, [dropzone.acceptedFiles]);
  const [inflight, setInflight] = useState(false);
  const readonly = !!props.config && !inflight;
  const typeKey = "type";
  const typeField =
    props.configSchema?.properties.configurable.properties[typeKey];
  if (!values?.configurable?.[typeKey] && typeField) {
    return (
      <Types
        field={typeField}
        value={values?.configurable?.[typeKey] as string}
        setValue={(value: string) =>
          setValues({
            ...values,
            configurable: { ...values!.configurable, [typeKey]: value },
          })
        }
        readonly={readonly}
      />
    );
  }
  return (
    <div className={props.className}>
      {typeField && (
        <Types
          field={typeField}
          value={values?.configurable?.[typeKey] as string}
          setValue={(value: string) =>
            setValues({
              ...values,
              configurable: { ...values!.configurable, [typeKey]: value },
            })
          }
          readonly={readonly}
        />
      )}
      <div className="flex gap-2 items-center justify-between font-semibold text-lg leading-6 text-gray-600 mb-4">
        <span>
          Bot: {props.config?.name ?? "New Bot"}{" "}
          <span className="font-normal">
            {props.config ? "(read-only)" : ""}
          </span>
        </span>
      </div>
      {props.config?.public && (
        <PublicLink assistantId={props.config?.assistant_id} />
      )}
      <form
        className={cn("flex flex-col gap-8")}
        onSubmit={async (e) => {
          e.preventDefault();
          e.stopPropagation();
          const form = e.target as HTMLFormElement;
          const key = form.key.value;
          if (!key) return;
          setInflight(true);
          await props.saveConfig(key, values!, files, isPublic);
          setInflight(false);
        }}
      >
        <div
          className={cn(
            "flex flex-col gap-8",
            readonly && "opacity-50 cursor-not-allowed"
          )}
        >
          {Object.entries(
            props.configSchema?.properties.configurable.properties ?? {}
          ).map(([key, value]) => {
            const title = value.title;
            if (value.allOf?.length === 1) {
              value = value.allOf[0];
            }
            if (key.split("/")[0].includes("==")) {
              const [parentKey, parentValue] = key.split("/")[0].split("==");
              if (values?.configurable?.[parentKey] !== parentValue) {
                return null;
              }
            } else {
              return null;
            }
            if (value.type === "string" && value.enum) {
              return (
                <SingleOptionField
                  key={key}
                  id={key}
                  field={value}
                  title={title}
                  value={values?.configurable?.[key] as string}
                  setValue={(value: string) =>
                    setValues({
                      ...values,
                      configurable: { ...values!.configurable, [key]: value },
                    })
                  }
                  readonly={readonly}
                />
              );
            } else if (value.type === "string") {
              return (
                <StringField
                  key={key}
                  id={key}
                  field={value}
                  title={title}
                  value={values?.configurable?.[key] as string}
                  setValue={(value: string) =>
                    setValues({
                      ...values,
                      configurable: { ...values!.configurable, [key]: value },
                    })
                  }
                  readonly={readonly}
                />
              );
            } else if (
              value.type === "array" &&
              value.items?.type === "string" &&
              value.items?.enum
            ) {
              return (
                <MultiOptionField
                  key={key}
                  id={key}
                  field={value}
                  title={title}
                  value={values?.configurable?.[key] as string[]}
                  setValue={(value: string[]) =>
                    setValues({
                      ...values,
                      configurable: { ...values!.configurable, [key]: value },
                    })
                  }
                  readonly={readonly}
                  descriptions={TOOL_DESCRIPTIONS}
                />
              );
            }
          })}
          {!props.config && (
            <FileUploadDropzone
              state={dropzone}
              files={files}
              setFiles={setFiles}
            />
          )}
          {}
          <SingleOptionField
            id="public"
            field={{
              type: "string",
              title: "public",
              description: "",
              enum: ["Yes", "No"],
            }}
            title="Create a public link?"
            value={isPublic ? "Yes" : "No"}
            setValue={(value: string) => setPublic(value === "Yes")}
            readonly={readonly}
          />
        </div>
        {!props.config && (
          <div className="flex flex-row">
            <div className="relative flex flex-grow items-stretch focus-within:z-10">
              <input
                type="text"
                name="key"
                id="key"
                autoComplete="off"
                className="block w-full rounded-none rounded-l-md border-0 py-1.5 pl-4 text-gray-900 ring-1 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 ring-inset ring-gray-300"
                placeholder="Name your bot"
              />
            </div>
            <button
              type="submit"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm leading-5 font-medium rounded-r-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600"
            >
              {inflight ? "Saving..." : "Save"}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
