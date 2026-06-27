export interface JsonRpcRequest {
  jsonrpc: "2.0";
  id: string | number;
  method: string;
  params?: unknown;
}

export interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: string | number;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

export interface AkatsukiEvent {
  jsonrpc: "2.0";
  method: string;
  params: {
    type: string;
    source: "hermes" | "obsidian" | "sync";
    timestamp: number;
    payload: unknown;
  };
}

export interface NoteData {
  id: string;
  path: string;
  title: string;
  content: string;
  tags: string[];
  links: string[];
  frontmatter: Record<string, unknown>;
  checksum: string;
  version: number;
  created: number;
  modified: number;
  source: "hermes" | "obsidian" | "user";
}
