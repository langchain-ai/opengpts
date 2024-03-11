import { useEffect, useState } from "react";
import { Tool, ToolConfig, ToolSchema } from "../utils/formTypes.ts";

interface SchemaProperty {
  const?: string;
  default?: string;
  $ref?: string;
}

interface ToolsSchema {
  properties: {
    id: SchemaProperty;
    name: SchemaProperty;
    type: SchemaProperty;
    description: SchemaProperty;
    config: SchemaProperty;
  };
}

const resolveRef = (schema: ToolsSchema, ref: string): ToolConfig => {
  const paths = ref.substring(2).split("/");
  let result: Record<string, object> = schema as object as Record<
    string,
    object
  >;
  for (const path of paths) {
    result = result[path] as Record<string, object>;
  }
  return result as object as ToolConfig;
};

export function useToolsSchemas() {
  const [tools, setTools] = useState<ToolSchema[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch("/runs/tool_schemas")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        const processedTools = data.map((schema: ToolsSchema): Tool => {
          // Assuming config is always an object with properties
          // You'll need a more sophisticated approach if configs can be more complex or vary significantly between tools
          let configTemplate: ToolConfig = {};
          if (schema.properties.config?.$ref) {
            // Use the resolveRef function to get the actual config from the $ref
            configTemplate = resolveRef(schema, schema.properties.config.$ref);
          }
          return {
            id: schema.properties.id.const || "",
            name: schema.properties.name.const || "",
            type: schema.properties.type.default || "",
            description: schema.properties.description.const || "",
            config: configTemplate,
          };
        });
        setTools(processedTools);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching tools:", error);
        setError(error);
        setLoading(false);
      });
  }, []); // Empty dependency array means this effect runs once after the initial render

  return { tools, loading, error };
}
