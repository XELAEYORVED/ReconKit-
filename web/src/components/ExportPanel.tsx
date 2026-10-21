import { api } from "../lib/api";

const FORMATS = [
  { fmt: "json", label: "JSON", desc: "Full raw data" },
  { fmt: "html", label: "HTML", desc: "Styled report" },
  { fmt: "markdown", label: "Markdown", desc: "Docs-friendly" },
  { fmt: "pdf", label: "PDF", desc: "Printable report" },
  { fmt: "csv", label: "CSV", desc: "Spreadsheet" },
  { fmt: "stix", label: "STIX 2.1", desc: "Threat intel" },
  { fmt: "misp", label: "MISP", desc: "MISP event" },
];

export function ExportPanel({ scanId }: { scanId: string }) {
  return (
    <div className="card">
      <h3 className="text-accent text-sm mb-3">Export</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {FORMATS.map((f) => (
          <a
            key={f.fmt}
            href={api.reportUrl(scanId, f.fmt)}
            className="btn btn-ghost text-left flex flex-col"
            download
          >
            <span className="font-semibold">{f.label}</span>
            <span className="text-[10px] text-muted">{f.desc}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
