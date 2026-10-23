import { useState } from "react";
import { Link } from "react-router-dom";
import { api, useDeleteScan, useScanAnnotations, useScans } from "../lib/api";
import { riskColor, riskFromScore, timeAgo } from "../lib/format";
import { STATUS_LABEL, TYPE_LABEL } from "../lib/modules";
import type { Scan } from "../lib/types";
import { useScanStore } from "../stores/scanStore";

export function ScanHistory() {
  const [q, setQ] = useState("");
  const [favOnly, setFavOnly] = useState(false);
  const params = new URLSearchParams();
  if (q) params.set("target", q);
  if (favOnly) params.set("favorite", "true");
  const qs = params.toString();
  const { data: scans, isLoading } = useScans(qs ? `?${qs}` : "");
  const { compareA, compareB } = useScanStore();

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        <input
          className="input max-w-xs"
          placeholder="Rechercher une cible…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          onClick={() => setFavOnly((f) => !f)}
          className={`btn ${favOnly ? "btn-primary" : "btn-ghost"}`}
          title="Afficher seulement les favoris"
        >
          ★ Favoris
        </button>
        {compareA && compareB && (
          <Link to={`/compare/${compareA}/${compareB}`} className="btn btn-primary ml-auto">
            Comparer la sélection →
          </Link>
        )}
      </div>

      <div className="space-y-2">
        {(scans ?? []).map((s) => (
          <ScanRow key={s.id} scan={s} />
        ))}
        {!isLoading && (scans ?? []).length === 0 && (
          <div className="card text-center text-muted py-8">Aucun scan trouvé.</div>
        )}
      </div>
    </div>
  );
}

function ScanRow({ scan }: { scan: Scan }) {
  const [open, setOpen] = useState(false);
  const [tagDraft, setTagDraft] = useState("");
  const [noteDraft, setNoteDraft] = useState("");
  const del = useDeleteScan();
  const ann = useScanAnnotations();
  const { compareA, compareB, setCompare } = useScanStore();
  const level = riskFromScore(scan.threat_score);
  const checked = compareA === scan.id || compareB === scan.id;

  const pickCompare = () => {
    if (compareA === scan.id) setCompare(null, compareB);
    else if (compareB === scan.id) setCompare(compareA, null);
    else if (!compareA) setCompare(scan.id, compareB);
    else if (!compareB) setCompare(compareA, scan.id);
    else setCompare(scan.id, null);
  };

  return (
    <div className="card !p-0 overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3">
        <button
          onClick={() => ann.toggleFavorite.mutate(scan.id)}
          className={`text-lg leading-none transition-colors ${
            scan.favorite ? "text-accent" : "text-muted hover:text-accent"
          }`}
          title={scan.favorite ? "Retirer des favoris" : "Ajouter aux favoris"}
        >
          {scan.favorite ? "★" : "☆"}
        </button>
        <input type="checkbox" checked={checked} onChange={pickCompare} title="Cocher pour comparer" />
        <div className="min-w-0 flex-1">
          <Link to={scan.status === "failed" ? `/scan/${scan.id}` : `/results/${scan.id}`} className="font-medium text-ink hover:text-accent break-all">
            {scan.target}
          </Link>
          <div className="flex items-center gap-2 text-[11px] text-muted">
            <span>{TYPE_LABEL[scan.target_type] ?? scan.target_type}</span>
            <span>·</span>
            <span className={scan.status === "failed" ? "text-risk-critical" : ""}>{STATUS_LABEL[scan.status] ?? scan.status}</span>
            <span>·</span>
            <span>{timeAgo(scan.started_at)}</span>
            {scan.tags.map((t) => (
              <span key={t} className="tag">
                {t}
              </span>
            ))}
          </div>
        </div>
        <span className="font-mono text-lg tabular-nums" style={{ color: riskColor(level) }}>
          {scan.threat_score}
        </span>
        <button className="btn-ghost btn !py-1 !px-2 text-xs" onClick={() => setOpen((o) => !o)}>
          {open ? "Fermer" : "Annoter"}
        </button>
        <a href={api.reportUrl(scan.id, "pdf")} download className="text-muted hover:text-accent text-xs" title="Rapport PDF">
          ⤓
        </a>
        <button
          className="text-muted hover:text-risk-critical text-xs"
          onClick={() => del.mutate(scan.id)}
          title="Supprimer le scan"
        >
          ✕
        </button>
      </div>

      {open && (
        <div className="border-t border-border bg-base/40 px-4 py-3 space-y-3">
          <div>
            <div className="text-[11px] uppercase tracking-widest text-muted mb-1">Tags</div>
            <div className="flex flex-wrap items-center gap-1">
              {scan.tags.map((t) => (
                <span key={t} className="tag flex items-center gap-1">
                  {t}
                  <button
                    className="text-muted hover:text-risk-critical"
                    onClick={() => ann.removeTag.mutate({ id: scan.id, tag: t })}
                  >
                    ×
                  </button>
                </span>
              ))}
              <input
                className="input !py-1 !w-32 text-xs"
                placeholder="ajouter un tag…"
                value={tagDraft}
                onChange={(e) => setTagDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && tagDraft.trim()) {
                    ann.addTag.mutate({ id: scan.id, tag: tagDraft.trim() });
                    setTagDraft("");
                  }
                }}
              />
            </div>
          </div>

          <div>
            <div className="text-[11px] uppercase tracking-widest text-muted mb-1">Notes</div>
            <div className="space-y-1 mb-2">
              {scan.notes.map((n) => (
                <div key={n.id} className="flex items-start gap-2 text-sm bg-panel2 rounded-lg px-3 py-2">
                  <span className="flex-1 text-ink/80">{n.content}</span>
                  <span className="text-[10px] text-muted whitespace-nowrap">{timeAgo(n.created_at)}</span>
                  <button
                    className="text-muted hover:text-risk-critical"
                    onClick={() => ann.deleteNote.mutate({ id: scan.id, noteId: n.id })}
                  >
                    ×
                  </button>
                </div>
              ))}
              {scan.notes.length === 0 && <div className="text-xs text-muted">Pas encore de notes.</div>}
            </div>
            <div className="flex gap-2">
              <input
                className="input !py-1 text-sm"
                placeholder="Écris une note puis Entrée…"
                value={noteDraft}
                onChange={(e) => setNoteDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && noteDraft.trim()) {
                    ann.addNote.mutate({ id: scan.id, content: noteDraft.trim() });
                    setNoteDraft("");
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
