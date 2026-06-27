export type JsonRpcCallback = (result: unknown) => void;
export type EventHandler = (event: { method: string; params: Record<string, unknown> }) => void;

interface PendingRequest {
  resolve: (value: unknown) => void;
  reject: (reason: Error) => void;
  timer: ReturnType<typeof setTimeout>;
}

const TIMEOUT_MS = 10000;

export class IpcClient {
  protected ws: WebSocket | null = null;
  protected requestId = 0;
  protected pending = new Map<string | number, PendingRequest>();
  protected eventHandlers = new Map<string, EventHandler>();
  protected connected = false;
  protected authenticated = false;
  protected url: string;
  protected reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  protected maxReconnectAttempts = 5;
  protected reconnectAttempts = 0;
  protected token: string | null = null;
  protected username: string | null = null;

  constructor(url: string) {
    this.url = url;
  }

  setCredentials(username: string, password: string): void {
    this.username = username;
    this.token = btoa(`${username}:${password}`);
  }

  setToken(token: string): void {
    this.token = token;
  }

  clearAuth(): void {
    this.token = null;
    this.username = null;
    this.authenticated = false;
  }

  async login(username: string, password: string): Promise<unknown> {
    const result = await this.call("auth/login", { username, password });
    if (result && typeof result === "object" && "token" in result) {
      this.token = (result as Record<string, unknown>).token as string;
      this.username = username;
      this.authenticated = true;
    }
    return result;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
      } catch (e) {
        reject(e);
        return;
      }

      this.ws.onopen = () => {
        this.connected = true;
        this.reconnectAttempts = 0;
        if (this.token) {
          this.ws!.send(JSON.stringify({
            jsonrpc: "2.0",
            id: "auth",
            method: "auth/authenticate",
            params: { token: this.token },
          }));
        }
        resolve();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.id === "auth" && msg.result) {
            this.authenticated = true;
          }
          this.dispatch(msg);
        } catch (e) {
          console.error("AKATSUKI IPC: failed to parse message", e);
        }
      };

      this.ws.onclose = () => {
        this.connected = false;
        this.authenticated = false;
        this.rejectAll(new Error("Connection closed"));
        this.attemptReconnect();
      };

      this.ws.onerror = () => {
        this.connected = false;
        this.authenticated = false;
        reject(new Error("WebSocket connection failed"));
      };
    });
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connected = false;
    this.authenticated = false;
  }

  async call(method: string, params: Record<string, unknown> = {}): Promise<unknown> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("Not connected");
    }
    const id = ++this.requestId;
    const msg: Record<string, unknown> = { jsonrpc: "2.0", id, method, params };
    if (this.token) {
      msg.token = this.token;
    }
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Request timed out: ${method}`));
      }, TIMEOUT_MS);
      this.pending.set(id, { resolve, reject, timer });
      this.ws!.send(JSON.stringify(msg));
    });
  }

  on(event: string, handler: EventHandler): void {
    this.eventHandlers.set(event, handler);
  }

  off(event: string): void {
    this.eventHandlers.delete(event);
  }

  isConnected(): boolean {
    return this.connected;
  }

  isAuthenticated(): boolean {
    return this.authenticated;
  }

  private dispatch(msg: { jsonrpc: string; id?: string | number; method?: string; result?: unknown; error?: { code: number; message: string }; params?: Record<string, unknown> }): void {
    if (msg.id === "auth") return;
    if (msg.method && msg.method.startsWith("event/")) {
      const eventName = msg.method.slice(6);
      const handler = this.eventHandlers.get(eventName);
      if (handler) {
        handler({ method: eventName, params: msg.params || {} });
      }
      return;
    }
    if (msg.id !== undefined && msg.id !== null) {
      const pending = this.pending.get(msg.id);
      if (pending) {
        clearTimeout(pending.timer);
        this.pending.delete(msg.id);
        if (msg.error) {
          pending.reject(new Error(msg.error.message));
        } else {
          pending.resolve(msg.result);
        }
      }
    }
  }

  private rejectAll(error: Error): void {
    for (const [id, pending] of this.pending) {
      clearTimeout(pending.timer);
      pending.reject(error);
    }
    this.pending.clear();
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(() => {});
    }, delay);
  }
}

export class UnixSocketClient extends IpcClient {
  constructor(port: number, host = "127.0.0.1") {
    super(`ws://${host}:${port}`);
  }
}

export class WebSocketClient extends IpcClient {
  constructor(port: number, host = "127.0.0.1") {
    super(`ws://${host}:${port}`);
  }
}