export type MessageWithFiles = {
  message: string;
  files: File[];
};

export interface Tool {
  id: string;
  type: string;
  name: string;
  description: string;
  config: ToolConfig;
}

export interface ToolConfig {
  [key: string]: string;
}

export interface ToolSchema {
  type: string;
  name: string;
  description: string;
  multiUse: boolean;
  config: ToolConfigSchema;
}

interface PropertySchema {
  type: string;
  title?: string;
  default?: string; // Assuming default values are strings
}

export interface ToolConfigSchema {
  title: string;
  type: string;
  required: string[];
  properties: {
    [key: string]: PropertySchema;
  };
}
