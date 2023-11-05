import { useEffect, useState } from "react";
import { simplifySchema } from "../utils/simplifySchema";
import { getDefaults } from "../utils/defaults";

export interface Schemas {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  configSchema: null | any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  inputSchema: null | any;
  configDefaults: null | Record<string, unknown>;
  inputDefaults: null | Record<string, unknown>;
}

export function useSchemas() {
  const [schemas, setSchemas] = useState<Schemas>({
    configSchema: null,
    inputSchema: null,
    configDefaults: null,
    inputDefaults: null,
  });

  useEffect(() => {
    async function save() {
      const [configSchema, inputSchema] = await Promise.all([
        fetch("/config_schema")
          .then((r) => r.json())
          .then(simplifySchema),
        fetch("/input_schema")
          .then((r) => r.json())
          .then(simplifySchema),
      ]);
      setSchemas({
        configSchema,
        inputSchema,
        configDefaults: getDefaults(configSchema) as Record<string, unknown>,
        inputDefaults: getDefaults(inputSchema) as Record<string, unknown>,
      });
    }

    save();
  }, []);

  return schemas;
}
