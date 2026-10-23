import { api } from "../lib/api";
import { Icon } from "./Icon";

const FORMATS = [
  { fmt: "pdf", label: "PDF", desc: "Rapport à imprimer" },
  { fmt: "html", label: "HTML", desc: "Rapport à ouvrir dans le navigateur" },
  { fmt: "markdown", label: "Markdown", desc: "Pour une doc ou un wiki" },
  { fmt: "json", label: "JSON", desc: "Toutes les données brutes" },
  { fmt: "csv", label: "CSV", desc: "Pour Excel / tableur" },
  { fmt: "stix", label: "STIX 2.1", desc: "Format threat-intel" },
  { fmt: "misp", label: "MISP", desc: "Événement MISP" },
];

export function ExportPanel({ scanId }: { scanId: string }) {
  return (
    <div className="card">
      <h3 className="font-semibold text-ink">Télécharger le rapport</h3>
      <p className="text-xs text-muted mt-0.5 mb-3">Choisis un format. Le PDF est le plus simple à partager.</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {FORMATS.map((f) => (
          <a
            key={f.fmt}
            href={api.reportUrl(scanId, f.fmt)}
            className="flex items-center gap-3 rounded-xl border border-border/70 px-3 py-2.5 hover:border-accent hover:bg-accent/5 transition-colors"
            download
          >
            <span className="text-accent"><Icon name="download" size={16} /></span>
            <span className="min-w-0">
              <span className="block text-sm font-medium text-ink">{f.label}</span>
              <span className="block text-[11px] text-muted truncate">{f.desc}</span>
            </span>
          </a>
        ))}
      </div>
    </div>
  );
}
