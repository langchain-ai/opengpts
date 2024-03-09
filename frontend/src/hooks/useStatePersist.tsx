import React, { useEffect, useState } from "react";

const PREFIX = "langgizmo-";

export function useStatePersist<T>(
  defaultValue: T,
  key: string,
): [T, React.Dispatch<React.SetStateAction<T>>] {
  const [state, setState] = useState<T>(() => {
    const storageValue = localStorage.getItem(PREFIX + key);

    if (storageValue) {
      return JSON.parse(storageValue);
    } else {
      return defaultValue;
    }
  });

  useEffect(() => {
    localStorage.setItem(PREFIX + key, JSON.stringify(state));
  }, [state, key]);

  return [state, setState];
}
