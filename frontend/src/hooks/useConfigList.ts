import { useCallback, useEffect, useState } from "react";

export interface Config {
  key: string;
  config: Record<string, unknown>;
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
      const configs = await fetch("/s/").then((r) => r.json());
      setConfigs(configs);
    }

    fetchConfigs();
  }, []);

  const saveConfig = useCallback(
    async (key: string, config: Config["config"]) => {
      const saved = await fetch("/s/", {
        method: "PUT",
        body: JSON.stringify({ key, config }),
      }).then((r) => r.json());
      setConfigs((configs) => [
        ...configs.filter((c) => c.key !== saved.key),
        saved,
      ]);
    },
    []
  );

  const enterConfig = useCallback((key: string | null) => {
    setCurrent(key);
  }, []);

  return {
    configs,
    currentConfig: configs.find((c) => c.key === current) || null,
    saveConfig,
    enterConfig,
  };
}
