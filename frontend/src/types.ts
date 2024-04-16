export interface FunctionDefinition {
  name?: string;
  arguments?: string;
}

export interface MessageDocument {
  page_content: string;
  metadata: Record<string, unknown>;
}

export interface Message {
  id: string;
  role: string;
  content: string | MessageDocument[] | object;
  name?: string;
  additional_kwargs?: {
    name?: string;
    function_call?: FunctionDefinition;
    tool_calls?: {
      id: string;
      function?: FunctionDefinition;
    }[];
  };
  example: boolean;
}

export interface Chat {
  assistant_id: string;
  thread_id: string;
  name: string;
  updated_at: string;
}
