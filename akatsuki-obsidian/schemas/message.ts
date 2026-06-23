export const enum MessageType {
  REQUEST  = "request",
  RESPONSE = "response",
  EVENT    = "event",
  ERROR    = "error",
  STREAM   = "stream",
  PING     = "ping",
  PONG     = "pong",
}

export const enum ErrorCode {
  // JSON-RPC standard
  PARSE_ERROR      = -32700,
  INVALID_REQUEST  = -32600,
  METHOD_NOT_FOUND = -32601,
  INVALID_PARAMS   = -32602,
  INTERNAL_ERROR   = -32603,
  // Application
  NOT_AUTHORIZED   = -32001,
  NOTE_NOT_FOUND   = -32002,
  SYNC_CONFLICT    = -32003,
  RATE_LIMITED     = -32004,
  TIMEOUT          = -32005,
}

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
  error?: JsonRpcError;
}

export interface JsonRpcError {
  code: number;
  message: string;
  data?: unknown;
}

export interface AkatsukiEvent {
  jsonrpc: "2.0";
  method: string;       // "event/<event_name>"
  params: {
    type: string;
    source: "hermes" | "obsidian" | "sync";
    timestamp: number;
    payload: unknown;
    ttl?: number;
  };
}
