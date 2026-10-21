import { useEffect, useMemo, useRef, useState } from "react";
import type { RelationGraph as Graph, GraphNode } from "../lib/types";

interface Sim extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  fixed?: boolean;
}

const SEVERITY_COLOR: Record<string, string> = {
  safe: "#22c55e",
  attention: "#f59e0b",
  critical: "#ef4444",
  medium: "#eab308",
  high: "#f97316",
  low: "#22c55e",
};
const TYPE_RADIUS: Record<string, number> = {
  target: 16,
  ip: 11,
  subdomain: 8,
  asn: 12,
  service: 9,
  vuln: 10,
};

/** Dependency-light force-directed graph rendered as interactive SVG. */
export function RelationGraph({ graph }: { graph: Graph }) {
  const W = 760;
  const H = 520;
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [view, setView] = useState({ x: 0, y: 0, k: 1 });
  const [filter, setFilter] = useState<string | null>(null);
  const dragRef = useRef<{ id: string | null; panning: boolean }>({ id: null, panning: false });
  const [, force] = useState(0);

  const nodes = useRef<Sim[]>([]);
  const edges = useMemo(() => graph.edges ?? [], [graph]);

  // Initialize node positions once per graph.
  useEffect(() => {
    nodes.current = (graph.nodes ?? []).map((n, i) => {
      const angle = (i / Math.max(1, graph.nodes.length)) * Math.PI * 2;
      const isTarget = n.type === "target";
      return {
        ...n,
        x: W / 2 + (isTarget ? 0 : Math.cos(angle) * 180 + (Math.random() - 0.5) * 40),
        y: H / 2 + (isTarget ? 0 : Math.sin(angle) * 180 + (Math.random() - 0.5) * 40),
        vx: 0,
        vy: 0,
        fixed: isTarget,
      };
    });
    force((x) => x + 1);
  }, [graph]);

  // Force simulation loop.
  useEffect(() => {
    let raf = 0;
    const byId = () => Object.fromEntries(nodes.current.map((n) => [n.id, n]));
    const tick = () => {
      const ns = nodes.current;
      const map = byId();
      // Repulsion.
      for (let i = 0; i < ns.length; i++) {
        for (let j = i + 1; j < ns.length; j++) {
          const a = ns[i];
          const b = ns[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let d2 = dx * dx + dy * dy || 0.01;
          const f = 2200 / d2;
          const d = Math.sqrt(d2);
          dx /= d;
          dy /= d;
          if (!a.fixed) {
            a.vx += dx * f;
            a.vy += dy * f;
          }
          if (!b.fixed) {
            b.vx -= dx * f;
            b.vy -= dy * f;
          }
        }
      }
      // Springs.
      for (const e of edges) {
        const a = map[e.source];
        const b = map[e.target];
        if (!a || !b) continue;
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 0.01;
        const diff = (d - 90) * 0.02;
        dx = (dx / d) * diff;
        dy = (dy / d) * diff;
        if (!a.fixed) {
          a.vx += dx;
          a.vy += dy;
        }
        if (!b.fixed) {
          b.vx -= dx;
          b.vy -= dy;
        }
      }
      // Centering + integrate.
      for (const n of ns) {
        if (n.fixed || dragRef.current.id === n.id) continue;
        n.vx += (W / 2 - n.x) * 0.002;
        n.vy += (H / 2 - n.y) * 0.002;
        n.vx *= 0.85;
        n.vy *= 0.85;
        n.x += n.vx;
        n.y += n.vy;
      }
      force((x) => (x + 1) % 1000000);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [edges]);

  const toLocal = (e: React.MouseEvent) => {
    const rect = svgRef.current!.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left - view.x) / view.k,
      y: (e.clientY - rect.top - view.y) / view.k,
    };
  };

  const onMove = (e: React.MouseEvent) => {
    if (dragRef.current.id) {
      const p = toLocal(e);
      const n = nodes.current.find((x) => x.id === dragRef.current.id);
      if (n) {
        n.x = p.x;
        n.y = p.y;
        n.vx = n.vy = 0;
      }
    } else if (dragRef.current.panning) {
      setView((v) => ({ ...v, x: v.x + e.movementX, y: v.y + e.movementY }));
    }
  };

  const types = Array.from(new Set((graph.nodes ?? []).map((n) => n.type)));
  const map = Object.fromEntries(nodes.current.map((n) => [n.id, n]));

  if (!graph.nodes?.length)
    return <div className="card text-sm text-gray-500">No graph data for this scan.</div>;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-300">Relation Graph</span>
        <div className="flex flex-wrap gap-1">
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(filter === t ? null : t)}
              className={`tag ${filter === t ? "ring-1 ring-neon text-neon" : ""}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        className="w-full bg-base rounded-lg border border-border cursor-move select-none"
        style={{ height: 520 }}
        onMouseDown={(e) => {
          if (e.target === svgRef.current) dragRef.current.panning = true;
        }}
        onMouseMove={onMove}
        onMouseUp={() => (dragRef.current = { id: null, panning: false })}
        onMouseLeave={() => (dragRef.current = { id: null, panning: false })}
        onWheel={(e) => {
          const k = Math.min(3, Math.max(0.4, view.k * (e.deltaY < 0 ? 1.1 : 0.9)));
          setView((v) => ({ ...v, k }));
        }}
      >
        <g transform={`translate(${view.x},${view.y}) scale(${view.k})`}>
          {edges.map((e, i) => {
            const a = map[e.source];
            const b = map[e.target];
            if (!a || !b) return null;
            const dim = filter && a.type !== filter && b.type !== filter;
            return (
              <line
                key={i}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke={dim ? "#1f2937" : "#334155"}
                strokeWidth={1}
                opacity={dim ? 0.2 : 0.7}
              />
            );
          })}
          {nodes.current.map((n) => {
            const dim = filter && n.type !== filter;
            const rad = TYPE_RADIUS[n.type] ?? 8;
            const color = SEVERITY_COLOR[n.severity] ?? "#22d3ee";
            return (
              <g
                key={n.id}
                transform={`translate(${n.x},${n.y})`}
                opacity={dim ? 0.25 : 1}
                onMouseDown={(e) => {
                  e.stopPropagation();
                  dragRef.current.id = n.id;
                }}
                className="cursor-pointer"
              >
                <circle r={rad} fill={color} stroke="#0a0a0f" strokeWidth={2} />
                <text
                  x={rad + 4}
                  y={4}
                  fontSize={10}
                  fill="#cbd5e1"
                  className="font-mono pointer-events-none"
                >
                  {n.label.length > 26 ? n.label.slice(0, 24) + "…" : n.label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      <div className="mt-2 flex gap-3 text-[10px] text-gray-500">
        <span>● <span className="text-risk-low">safe</span></span>
        <span>● <span className="text-risk-medium">attention</span></span>
        <span>● <span className="text-risk-critical">critical</span></span>
        <span className="ml-auto">drag nodes · scroll to zoom · drag canvas to pan</span>
      </div>
    </div>
  );
}
