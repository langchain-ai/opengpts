import { useCallback, useEffect, useMemo, useState } from "react";
import { useStatePersist } from "./useStatePersist";
import { Schemas } from "./useSchemas";

export interface Config {
  key: string;
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

export function useConfigListServer(): ConfigListProps {
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
      setCurrent(saved.key);
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

export function useConfigList(
  configDefaults: Schemas["configDefaults"]
): ConfigListProps {
  const [savedConfigs, setConfigs] = useStatePersist<Config[]>([], "configs");
  const [current, setCurrent] = useState<string | null>("Default");

  const saveConfig = useCallback(
    async (key: string, config: Config["config"]) => {
      const saved = { key, config };

      setConfigs((configs) => [
        ...configs.filter((c) => c.key !== saved.key),
        saved,
      ]);
      setCurrent(saved.key);
    },
    [setConfigs]
  );

  const enterConfig = useCallback((key: string | null) => {
    setCurrent(key);
  }, []);

  const configs = useMemo(
    () => [
      ...(configDefaults
        ? [{ key: "Default", config: configDefaults, readOnly: true }]
        : []),
      ...savedConfigs,
    ],
    [savedConfigs, configDefaults]
  );

  return {
    configs,
    currentConfig: configs.find((c) => c.key === current) || null,
    saveConfig,
    enterConfig,
  };
}
