import {useEffect, useState} from "react";
import {Tool} from "../utils/formTypes.ts";

export function useToolsSchemas() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
      fetch('/runs/tool_schemas')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
          console.log(data)
        setTools(data); // Assuming the response is the array of tools
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching tools:', error);
        setError(error);
        setLoading(false);
      });
  }, []); // Empty dependency array means this effect runs once after the initial render

  return { tools, loading, error };
}