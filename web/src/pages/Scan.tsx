import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/Layout";
import { ScanForm } from "../components/ScanForm";
import { ScanProgress } from "../components/ScanProgress";
import { ThreatScore } from "../components/ThreatScore";
import { useScanWebSocket } from "../hooks/useWebSocket";
import { useScan } from "../lib/api";
import { useScanStore } from "../stores/scanStore";

export function Scan() {
  const { id } = useParams();
  const { activeScanId, applyEvent, start, finished, setError, modules } = useScanStore();
  const scanId = id ?? activeScanId;

  useEffect(() => {
    if (id && id !== activeScanId) start(id);
  }, [id]);

  useScanWebSocket(scanId ?? null, applyEvent);
  // Polling fallback keeps data fresh even if the socket drops.
  const { data: scan } = useScan(scanId ?? undefined, !finished);

  useEffect(() => {
    if (scan?.status === "failed") setError(scan.error ?? "Le scan a échoué.");
  }, [scan?.status]);

  const done = scan?.status === "completed";
  const list = Object.values(modules);
  const found = list.filter((m) => m.status === "ok").length;
  const skipped = list.filter((m) => m.status === "skipped").length;

  return (
    <div className="max-w-4xl">
      <PageHeader
        title="Nouveau scan"
        subtitle="ReconKit n'interroge que des sources publiques : la cible ne voit rien passer."
      />
      <div className="space-y-5">
        <ScanForm />
        {scanId && (
          <>
            {done && (
              <div className="card !p-5 flex flex-col sm:flex-row items-center gap-5 bg-gradient-to-br from-white to-[#eef5ff]">
                <ThreatScore score={scan!.threat_score} size={120} />
                <div className="flex-1 text-center sm:text-left">
                  <div className="text-[18px] font-semibold text-ink">Scan de {scan!.target} terminé</div>
                  <div className="text-sm text-muted mt-1">
                    {list.length > 0
                      ? `${found} module(s) ont trouvé des informations${skipped ? `, ${skipped} ignoré(s) faute de clé API` : ""}.`
                      : "Les résultats sont prêts."}
                  </div>
                  {list.length > 0 && found === 0 && (
                    <div className="text-sm text-[#9a5b00] mt-2">
                      Aucun module n'a pu tourner pour ce type de cible. Essaie un nom de domaine, ou ajoute des clés
                      dans <Link to="/settings" className="underline">Réglages</Link>.
                    </div>
                  )}
                </div>
                <Link to={`/results/${scanId}`} className="btn btn-primary inline-flex items-center gap-2">
                  Voir les résultats <Icon name="arrow" size={16} />
                </Link>
              </div>
            )}
            {!(done && list.length === 0) && <ScanProgress />}
          </>
        )}
      </div>
    </div>
  );
}
