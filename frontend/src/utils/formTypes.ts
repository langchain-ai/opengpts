export type MessageWithFiles = {
  message: string;
  files: File[];
};

export interface Tool {
  id: string;
  type: string;
  name: string;
  description: string;
  config: {
    [key: string]: string;
  };
}

export interface ToolSchema {
  id: string;
  type: string;
  name: string;
  description: string;
  config: ToolConfigSchema;
}

interface PropertySchema {
  type: string;
  title?: string;
  default?: string; // Assuming default values are strings
}

interface ToolConfigSchema {
  title: string;
  type: string;
  required: string[];
  properties: {
    [key: string]: PropertySchema;
  };
}
