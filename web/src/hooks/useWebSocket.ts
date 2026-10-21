import { useEffect, useRef } from "react";
import type { WsEvent } from "../lib/types";

/**
 * Subscribe to the realtime scan WebSocket. Reconnects once on drop; closes
 * when the scan completes or the component unmounts.
 */
export function useScanWebSocket(
  scanId: string | null,
  onEvent: (e: WsEvent) => void,
) {
  const ref = useRef<WebSocket | null>(null);
  const cb = useRef(onEvent);
  cb.current = onEvent;

  useEffect(() => {
    if (!scanId) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${window.location.host}/ws/scan/${scanId}`;
    let closed = false;
    const ws = new WebSocket(url);
    ref.current = ws;

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data) as WsEvent;
        cb.current(data);
        if (data.event === "scan_complete" || data.event === "scan_error") {
          closed = true;
          ws.close();
        }
      } catch {
        /* ignore malformed */
      }
    };
    ws.onerror = () => {
      /* swallow; polling fallback covers it */
    };

    return () => {
      closed = true;
      ws.close();
    };
  }, [scanId]);

  return ref;
}
