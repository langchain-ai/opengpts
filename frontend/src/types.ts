export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
}

export interface MessageDocument {
  page_content: string;
  metadata: Record<string, unknown>;
}

export interface Message {
  id: string;
  type: string;
  content: string | MessageDocument[] | object;
  name?: string;
  tool_calls?: ToolCall[];
  example: boolean;
}

export interface Chat {
  assistant_id: string;
  thread_id: string;
  name: string;
  updated_at: string;
}
