import {useEffect, useState} from "react";
import {Tool} from "../utils/formTypes.ts";
import { v4 as uuidv4 } from 'uuid';

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
        const processedTools = data.map((schema): Tool => {
                    // Assuming config is always an object with properties
                    // You'll need a more sophisticated approach if configs can be more complex or vary significantly between tools
                    const configTemplate = schema.properties.config?.$ref ? {} : undefined;
                    return {
                        id: schema.properties.id.const || uuidv4(),
                        name: schema.properties.name.const,
                        description: schema.properties.description.const,
                        config: configTemplate,
                    };
                });
        setTools(processedTools);
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