import { useCallback, useEffect, useReducer, useState } from "react";
import orderBy from "lodash/orderBy";
import { v4 as uuidv4 } from "uuid";

export interface Config {
  assistant_id: string;
  name: string;
  updated_at: string;
  config: {
    configurable?: {
      tools?: string[];
      [key: string]: unknown;
    };
  };
  public: boolean;
  mine?: boolean;
}

export interface ConfigListProps {
  configs: Config[] | null;
  currentConfig: Config | null;
  saveConfig: (
    key: string,
    config: Config["config"],
    files: File[],
    isPublic: boolean
  ) => Promise<void>;
  enterConfig: (id: string | null) => void;
}

function configsReducer(
  state: Config[] | null,
  action: Config | Config[]
): Config[] | null {
  state = state ?? [];
  if (!Array.isArray(action)) {
    const newConfig = action;
    action = [
      ...state.filter((c) => c.assistant_id !== newConfig.assistant_id),
      newConfig,
    ];
  }
  return orderBy(action, "updated_at", "desc");
}

export function useConfigList(): ConfigListProps {
  const [configs, setConfigs] = useReducer(configsReducer, null);
  const [current, setCurrent] = useState<string | null>(null);

  useEffect(() => {
    async function fetchConfigs() {
      const searchParams = new URLSearchParams(window.location.search);
      const shared_id = searchParams.get("shared_id");
      const [myConfigs, publicConfigs] = await Promise.all([
        fetch("/assistants/", {
          headers: {
            Accept: "application/json",
          },
        })
          .then((r) => r.json())
          .then((li) => li.map((c: Config) => ({ ...c, mine: true }))),
        fetch(
          "/assistants/public/" + (shared_id ? `?shared_id=${shared_id}` : ""),
          {
            headers: {
              Accept: "application/json",
            },
          }
        ).then((r) => r.json()),
      ]);
      setConfigs(myConfigs.concat(publicConfigs));
      if (publicConfigs.find((a: Config) => a.assistant_id === shared_id)) {
        setCurrent(shared_id);
      }
    }

    fetchConfigs();
  }, []);

  const enterConfig = useCallback((key: string | null) => {
    setCurrent(key);
    window.scrollTo({ top: 0 });
  }, []);

  const saveConfig = useCallback(
    async (
      name: string,
      config: Config["config"],
      files: File[],
      isPublic: boolean,
      assistant_id: string = uuidv4()
    ) => {
      const formData = files.reduce((formData, file) => {
        formData.append("files", file);
        return formData;
      }, new FormData());
      formData.append(
        "config",
        JSON.stringify({ configurable: { assistant_id } })
      );
      const [saved] = await Promise.all([
        fetch(`/assistants/${assistant_id}`, {
          method: "PUT",
          body: JSON.stringify({ name, config, public: isPublic }),
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
        }).then((r) => r.json()),
        files.length
          ? fetch(`/ingest`, {
              method: "POST",
              body: formData,
            })
          : Promise.resolve(),
      ]);
      setConfigs({ ...saved, mine: true });
      enterConfig(saved.assistant_id);
    },
    [enterConfig]
  );

  return {
    configs,
    currentConfig: configs?.find((c) => c.assistant_id === current) || null,
    saveConfig,
    enterConfig,
  };
}
