import { useEffect, useState } from "react";
import { Tool, ToolSchema } from "../utils/formTypes.ts";
import { v4 as uuidv4 } from "uuid";

const resolveRef = (schema: object, ref: string) => {
  const paths = ref.substring(2).split("/");
  let result = schema;
  for (const path of paths) {
    result = result[path];
  }
  return result;
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
        const processedTools = data.map((schema: object): Tool => {
          // Assuming config is always an object with properties
          // You'll need a more sophisticated approach if configs can be more complex or vary significantly between tools
          let configTemplate;
          if (schema.properties.config?.$ref) {
            // Use the resolveRef function to get the actual config from the $ref
            configTemplate = resolveRef(schema, schema.properties.config.$ref);
          } else {
            configTemplate = undefined;
          }
          return {
            id: schema.properties.id.const || uuidv4(),
            name: schema.properties.name.const,
            type: schema.properties.type.default,
            description: schema.properties.description.const,
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
