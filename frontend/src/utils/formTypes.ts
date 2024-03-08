export type MessageWithFiles = {
  message: string;
  files: File[];
};

export interface Tool {
  id: string;
  name: string;
  config?: ToolConfig;
}

export interface ToolConfig {
  // TODO: Example properties, replace with actual config properties of your tools
  url?: string;
  apiKey?: string;
}
