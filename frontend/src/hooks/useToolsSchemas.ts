import { useEffect, useState } from "react";
import { ToolConfigSchema, ToolSchema } from "../utils/formTypes.ts";
import { useSchemas } from "./useSchemas.ts";

interface SchemaItem {
  properties: {
    name: { const: string };
    type: { default: string };
    description: { const: string };
    config: ToolConfigSchema;
    multi_use: { const: boolean };
  };
}

interface ConfigSchema {
  properties: {
    configurable: {
      properties: {
        "type==agent/tools": {
          items: {
            anyOf: SchemaItem[];
          };
        };
      };
    };
  };
}

export function useToolsSchemas() {
  const schemas = useSchemas();

  const [tools, setTools] = useState<ToolSchema[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const configSchema = schemas?.configSchema as ConfigSchema | null;
    if (!configSchema) {
      setLoading(true);
      return;
    }

    const toolSchemas = configSchema.properties.configurable.properties[
      "type==agent/tools"
    ]?.items.anyOf as SchemaItem[] | undefined;
    if (!toolSchemas) {
      setLoading(true);
      return;
    }
    const processedTools = toolSchemas.map((schema): ToolSchema => {
      // Assuming config is always an object with properties
      // You'll need a more sophisticated approach if configs can be more complex or vary significantly between tools
      return {
        name: schema.properties.name.const || "",
        type: schema.properties.type.default || "",
        description: schema.properties.description.const || "",
        config: schema.properties.config || {},
        multiUse: schema.properties.multi_use.const || false,
      };
    });
    setLoading(false);
    setTools(processedTools);
  }, [schemas]);

  return { tools, loading };
}
