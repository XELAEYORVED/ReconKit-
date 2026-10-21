import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { ScanForm } from "../components/ScanForm";
import { ScanProgress } from "../components/ScanProgress";
import { useScanWebSocket } from "../hooks/useWebSocket";
import { useScan } from "../lib/api";
import { useScanStore } from "../stores/scanStore";

export function Scan() {
  const { id } = useParams();
  const { activeScanId, applyEvent, start, finished } = useScanStore();
  const scanId = id ?? activeScanId;

  useEffect(() => {
    if (id && id !== activeScanId) start(id);
  }, [id]);

  useScanWebSocket(scanId ?? null, applyEvent);
  // Polling fallback keeps data fresh even if the socket drops.
  const { data: scan } = useScan(scanId ?? undefined, !finished);

  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="text-xl text-accent">New Scan</h1>
      <ScanForm />
      {scanId && (
        <>
          <ScanProgress />
          {(finished || scan?.status === "completed") && (
            <Link to={`/results/${scanId}`} className="btn btn-primary inline-block">
              View full results →
            </Link>
          )}
        </>
      )}
    </div>
  );
}
