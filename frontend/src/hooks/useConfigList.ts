import { useCallback, useEffect, useState } from "react";

export interface Config {
  assistant_id: string;
  name: string;
  updated_at: string;
  config: {
    configurable?: {
      [key: string]: unknown;
    };
  };
}

export interface ConfigListProps {
  configs: Config[];
  currentConfig: Config | null;
  saveConfig: (key: string, config: Config["config"]) => Promise<void>;
  enterConfig: (id: string | null) => void;
}

export function useConfigList(): ConfigListProps {
  const [configs, setConfigs] = useState<Config[]>([]);
  const [current, setCurrent] = useState<string | null>(null);

  useEffect(() => {
    async function fetchConfigs() {
      const configs = await fetch("/assistants/", {
        headers: {
          Accept: "application/json",
        },
      }).then((r) => r.json());
      setConfigs(configs);
    }

    fetchConfigs();
  }, []);

  const saveConfig = useCallback(
    async (
      name: string,
      config: Config["config"],
      assistant_id: string = crypto.randomUUID()
    ) => {
      const saved = await fetch(`/assistants/${assistant_id}`, {
        method: "PUT",
        body: JSON.stringify({ name, config }),
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      }).then((r) => r.json());
      setConfigs((configs) => [
        ...configs.filter((c) => c.assistant_id !== saved.assistant_id),
        saved,
      ]);
      setCurrent(saved.assistant_id);
    },
    []
  );

  const enterConfig = useCallback((key: string | null) => {
    setCurrent(key);
  }, []);

  return {
    configs,
    currentConfig: configs.find((c) => c.assistant_id === current) || null,
    saveConfig,
    enterConfig,
  };
}
