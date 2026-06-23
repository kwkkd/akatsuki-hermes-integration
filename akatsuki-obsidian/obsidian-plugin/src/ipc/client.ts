import { JsonRpcRequest, JsonRpcResponse, AkatsukiEvent } from "../types/messages";

export class UnixSocketClient {
  private ws: WebSocket | null = null;
  private pending = new Map<string | number, {
    resolve: (v: unknown) => void;
    reject: (e: Error) => void;
    timer: ReturnType<typeof setTimeout>;
  }>();
  private seq = 0;
  private url: string;
  private eventHandlers = new Map<string, (evt: AkatsukiEvent) => void>();

  constructor(port: number) {
    this.url = `ws://127.0.0.1:${port}`;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => resolve();
      this.ws.onclose = () => this.reconnect();
      this.ws.onerror = (e) => reject(e);
      this.ws.onmessage = (msg) => this.onMessage(msg.data);
    });
  }

  async call<T = unknown>(method: string, params?: unknown, timeout = 10000): Promise<T> {
    const id = ++this.seq;
    const req: JsonRpcRequest = { jsonrpc: "2.0", id, method, params };
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Timeout: ${method}`));
      }, timeout);
      this.pending.set(id, { resolve: resolve as (v: unknown) => void, reject, timer });
      this.ws?.send(JSON.stringify(req));
    }) as Promise<T>;
  }

  on(event: string, handler: (evt: AkatsukiEvent) => void) {
    this.eventHandlers.set(event, handler);
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }

  private onMessage(raw: string) {
    try {
      const msg = JSON.parse(raw);
      if (msg.id !== undefined) {
        const pending = this.pending.get(msg.id);
        if (pending) {
          clearTimeout(pending.timer);
          this.pending.delete(msg.id);
          if (msg.error) pending.reject(new Error(msg.error.message));
          else pending.resolve(msg.result);
        }
      } else if (msg.method?.startsWith("event/")) {
        const evtName = msg.method.slice(6);
        const handler = this.eventHandlers.get(evtName);
        handler?.(msg as AkatsukiEvent);
      }
    } catch { /* ignore malformed */ }
  }

  private reconnect() {
    setTimeout(() => this.connect(), 1000);
  }
}
