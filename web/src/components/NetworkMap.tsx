import type { ResultItem } from "../lib/types";

export function NetworkMap({ results }: { results: ResultItem[] }) {
  const net = results.find((r) => r.module_name === "network_map" && r.status === "ok");
  const geo = results.find((r) => r.module_name === "ip_geo" && r.status === "ok");
  if (!net) return <div className="card text-sm text-gray-500">No network/ASN data.</div>;

  const asn = net.data.asn ?? {};
  const prefixes: any[] = net.data.prefixes ?? [];
  const upstreams: any[] = net.data.peers?.upstreams ?? [];

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="card">
        <h3 className="text-neon text-sm mb-2">Autonomous System</h3>
        <dl className="text-xs space-y-1">
          <Row k="ASN" v={asn.asn ? `AS${asn.asn}` : "—"} />
          <Row k="Name" v={asn.name} />
          <Row k="Description" v={asn.description} />
          <Row k="Country" v={asn.country} />
          <Row k="RIR" v={asn.rir} />
          <Row k="IP" v={net.data.ip} />
          {geo && <Row k="Location" v={`${geo.data.city ?? ""}, ${geo.data.country ?? ""}`} />}
        </dl>
      </div>
      <div className="card">
        <h3 className="text-neon text-sm mb-2">Upstream peers ({upstreams.length})</h3>
        <div className="flex flex-wrap gap-1 max-h-40 overflow-y-auto">
          {upstreams.map((u) => (
            <span key={u.asn} className="tag" title={u.name}>
              AS{u.asn}
            </span>
          ))}
          {upstreams.length === 0 && <span className="text-xs text-gray-500">none</span>}
        </div>
      </div>
      <div className="card md:col-span-2">
        <h3 className="text-neon text-sm mb-2">Announced prefixes ({net.data.prefix_count ?? prefixes.length})</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-1 text-xs font-mono">
          {prefixes.slice(0, 40).map((p, i) => (
            <span key={i} className="text-gray-400 truncate" title={p.name}>
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
      <dt className="text-gray-500">{k}</dt>
      <dd className="text-gray-200 text-right truncate">{v ?? "—"}</dd>
    </div>
  );
}
