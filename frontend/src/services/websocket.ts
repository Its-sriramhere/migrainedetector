export type WsEvent =
  | { type: "prediction_update"; risk_score: number; risk_level: string; timestamp: string; prediction_window_minutes: number; features: unknown[]; advice?: string[] }
  | { type: "alert_update"; id: number; risk_score: number; risk_level: string; message: string; timestamp: string; acknowledged: boolean; prediction_id: number | null; advice?: string[] };

export interface WsClient {
  send: (data: unknown) => void;
  close: () => void;
}

function wsUrl(userId: number): string {
  const apiBase = import.meta.env.VITE_API_URL ?? "";
  const host = apiBase
    ? new URL(import.meta.env.VITE_API_URL).host
    : window.location.host;
  const protocol = window.location.protocol === "https:" || apiBase.startsWith("https") ? "wss" : "ws";
  return `${protocol}://${host}/ws/${userId}?token=${encodeURIComponent(localStorage.getItem("mg_token") ?? "")}`;
}

/**
 * Opens a WebSocket to the backend and reconnects with backoff on failure.
 * Returns a handle. Call `onEvent` for each parsed message.
 */
export function openWebSocket(
  userId: number,
  onEvent: (event: WsEvent) => void,
  onStatus?: (connected: boolean) => void,
): WsClient {
  let socket: WebSocket | null = null;
  let closed = false;
  let retries = 0;

  const connect = () => {
    if (closed) return;
    try {
      socket = new WebSocket(wsUrl(userId));
    } catch {
      scheduleReconnect();
      return;
    }

    socket.onopen = () => {
      retries = 0;
      onStatus?.(true);
    };

    socket.onmessage = (message) => {
      try {
        const data = JSON.parse(message.data as string);
        onEvent(data as WsEvent);
      } catch {
        /* ignore malformed frames */
      }
    };

    socket.onclose = () => {
      onStatus?.(false);
      if (!closed) scheduleReconnect();
    };

    socket.onerror = () => {
      socket?.close();
    };
  };

  const scheduleReconnect = () => {
    if (closed) return;
    const delay = Math.min(15000, 1000 * 2 ** retries);
    retries += 1;
    setTimeout(connect, delay);
  };

  connect();

  return {
    send: (data) => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(data));
      }
    },
    close: () => {
      closed = true;
      socket?.close();
    },
  };
}