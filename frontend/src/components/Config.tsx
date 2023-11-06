import { ConfigListProps } from "../hooks/useConfigList";
import { SchemaField, Schemas } from "../hooks/useSchemas";

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
}) {
  return (
    <div>
      <Label id={props.id} title={props.title} />
      <textarea
        rows={4}
        name={props.id}
        id={props.id}
        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
        defaultValue={props.value}
        readOnly={props.readonly}
        disabled={props.readonly}
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
                defaultChecked={option === props.value}
                className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-600"
                disabled={props.readonly}
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
                defaultChecked={props.value.includes(option)}
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
                disabled={props.readonly}
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
  const values = props.config?.config ?? props.configDefaults;
  const readonly = true;
  return (
    <>
      <div className="font-semibold text-lg leading-6 text-gray-600 mb-4">
        Bot Configuration
      </div>
      <form className="flex flex-col gap-8">
        {Object.entries(
          props.configSchema?.properties.configurable.properties ?? {}
        ).map(([key, value]) => {
          const title = value.title;
          if (value.allOf?.length === 1) {
            value = value.allOf[0];
          }
          if (value.type === "string" && value.enum) {
            return (
              <SingleOptionField
                key={key}
                id={key}
                field={value}
                title={title}
                value={values?.configurable?.[key] as string}
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
                readonly={readonly}
              />
            );
          } else if (value.type === "array" && value.items?.enum) {
            return (
              <MultiOptionField
                key={key}
                id={key}
                field={value}
                title={title}
                value={values?.configurable?.[key] as string[]}
                readonly={readonly}
              />
            );
          }
        })}
      </form>
    </>
  );
}
