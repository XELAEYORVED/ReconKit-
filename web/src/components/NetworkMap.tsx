import type { ResultItem } from "../lib/types";

export function NetworkMap({ results }: { results: ResultItem[] }) {
  const net = results.find((r) => r.module_name === "network_map" && r.status === "ok");
  const geo = results.find((r) => r.module_name === "ip_geo" && r.status === "ok");
  if (!net) return <div className="card text-sm text-muted">Pas de données réseau (ASN) pour ce scan.</div>;

  const asn = net.data.asn ?? {};
  const prefixes: any[] = net.data.prefixes ?? [];
  const upstreams: any[] = net.data.peers?.upstreams ?? [];

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div className="card">
        <h3 className="font-semibold text-ink mb-2">Réseau (système autonome)</h3>
        <dl className="text-[13px] space-y-1.5">
          <Row k="ASN" v={asn.asn ? `AS${asn.asn}` : "—"} />
          <Row k="Opérateur" v={asn.name} />
          <Row k="Organisation" v={asn.description} />
          <Row k="Pays" v={asn.country} />
          <Row k="Registre" v={asn.rir} />
          <Row k="IP" v={net.data.ip} />
          {geo && <Row k="Lieu" v={`${geo.data.city ?? ""}, ${geo.data.country ?? ""}`} />}
        </dl>
      </div>
      <div className="card">
        <h3 className="font-semibold text-ink mb-2">Fournisseurs amont ({upstreams.length})</h3>
        <div className="flex flex-wrap gap-1 max-h-40 overflow-y-auto">
          {upstreams.map((u) => (
            <span key={u.asn} className="tag" title={u.name}>
              AS{u.asn}
            </span>
          ))}
          {upstreams.length === 0 && <span className="text-xs text-muted">aucun</span>}
        </div>
      </div>
      <div className="card md:col-span-2">
        <h3 className="font-semibold text-ink mb-2">Plages d'IP annoncées ({net.data.prefix_count ?? prefixes.length})</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-1 text-xs font-mono">
          {prefixes.slice(0, 40).map((p, i) => (
            <span key={i} className="text-muted truncate" title={p.name}>
              {p.prefix}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v?: any }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="text-muted">{k}</dt>
      <dd className="text-ink text-right truncate">{v ?? "—"}</dd>
    </div>
  );
}
