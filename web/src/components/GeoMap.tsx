import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import type { ResultItem } from "../lib/types";

// Fix default marker icons (bundler strips the asset paths otherwise).
const icon = L.divIcon({
  className: "",
  html: `<div style="width:14px;height:14px;border-radius:50%;background:#0071e3;box-shadow:0 0 10px #0071e3;border:2px solid #ffffff"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

interface Point {
  lat: number;
  lon: number;
  label: string;
  detail: string;
}

export function GeoMap({ results }: { results: ResultItem[] }) {
  const points: Point[] = [];
  for (const r of results) {
    if (r.module_name === "ip_geo" && r.status === "ok" && r.data.lat && r.data.lon) {
      points.push({
        lat: r.data.lat,
        lon: r.data.lon,
        label: r.data.ip,
        detail: `${r.data.city ?? ""}, ${r.data.country ?? ""} · ${r.data.org ?? ""}`,
      });
    }
  }

  if (points.length === 0)
    return <div className="card text-sm text-muted">Pas de données de localisation pour ce scan.</div>;

  const center: [number, number] = [points[0].lat, points[0].lon];

  return (
    <div className="card !p-0 overflow-hidden">
      <MapContainer center={center} zoom={4} style={{ height: 480, width: "100%" }}>
        <TileLayer
          attribution="&copy; OpenStreetMap, &copy; CARTO"
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        {points.map((p, i) => (
          <Marker key={i} position={[p.lat, p.lon]} icon={icon}>
            <Popup>
              <b>{p.label}</b>
              <br />
              {p.detail}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
