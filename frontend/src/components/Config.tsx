import { ConfigListProps } from "../hooks/useConfigList";
import { SchemaField, Schemas } from "../hooks/useSchemas";
import { useEffect, useState } from "react";
import { cn } from "../utils/cn";

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
          {props.field.enum?.map((option) => (
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

function MultiOptionField(props: {
  id: string;
  field: SchemaField;
  value: string[];
  title: string;
  readonly: boolean;
  setValue: (value: string[]) => void;
}) {
  return (
    <fieldset>
      <Label id={props.id} title={props.title ?? props.field.items?.title} />
      <div className="space-y-2">
        {props.field.items?.enum?.map((option) => (
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
            </div>
          </div>
        ))}
      </div>
    </fieldset>
  );
}

export function Config(props: {
  configSchema: Schemas["configSchema"];
  configDefaults: Schemas["configDefaults"];
  config: ConfigListProps["currentConfig"];
  saveConfig: ConfigListProps["saveConfig"];
}) {
  const [values, setValues] = useState(
    props.config?.config ?? props.configDefaults
  );
  useEffect(() => {
    setValues(props.config?.config ?? props.configDefaults);
  }, [props.config, props.configDefaults]);
  const readonly = !!props.config;
  return (
    <>
      <div className="font-semibold text-lg leading-6 text-gray-600 mb-4">
        Bot: {props.config?.key ?? "New Bot"}{" "}
        <span className="font-normal">{props.config ? "(read-only)" : ""}</span>
      </div>
      <form
        className={cn(
          "flex flex-col gap-8",
          readonly && "opacity-50 cursor-not-allowed"
        )}
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          const form = e.target as HTMLFormElement;
          const key = form.key.value;
          if (!key) return;
          props.saveConfig(key, values!);
        }}
      >
        {Object.entries(
          props.configSchema?.properties.configurable.properties ?? {}
        ).map(([key, value]) => {
          const title = value.title;
          if (value.allOf?.length === 1) {
            value = value.allOf[0];
          }
          if (key === "agent_type") {
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
          } else if (key === "system_message") {
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
          } else if (key === "tools") {
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
              />
            );
          }
        })}
        {!props.config && (
          <div className="flex flex-row">
            <div className="relative flex flex-grow items-stretch focus-within:z-10">
              <input
                type="text"
                name="key"
                id="key"
                autoFocus
                autoComplete="off"
                className="block w-full rounded-none rounded-l-md border-0 py-1.5 pl-4 text-gray-900 ring-1 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 ring-inset ring-gray-300"
                placeholder="Name your bot"
              />
            </div>
            <button
              type="submit"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm leading-5 font-medium rounded-r-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600"
            >
              Save
            </button>
          </div>
        )}
      </form>
    </>
  );
}
