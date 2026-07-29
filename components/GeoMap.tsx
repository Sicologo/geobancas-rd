"use client";

import { useEffect, useRef } from "react";
import maplibregl, { Map, MapMouseEvent } from "maplibre-gl";
import type { Banca, Escuela } from "@/lib/sample-data";

type Props = {
  data: Banca[];
  escuelas: Escuela[];
  showEscuelas: boolean;
  selectedId?: string;
  selectedEscuelaCodigo?: string;
  onSelect: (banca: Banca) => void;
  onSelectEscuela: (escuela: Escuela) => void;
};

const statusColor: Record<Banca["estatus"], string> = {
  Legal: "#2ecc71", Ilegal: "#ff5c73", Pendiente: "#f5b942", Suspendida: "#87a4bf",
};

function bancasGeoJSON(data: Banca[]): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return { type: "FeatureCollection", features: data.map((b) => ({
    type: "Feature", geometry: { type: "Point", coordinates: [b.lng, b.lat] },
    properties: { ...b, color: statusColor[b.estatus] },
  })) };
}

function escuelasGeoJSON(data: Escuela[]): GeoJSON.FeatureCollection<GeoJSON.Point> {
  return { type: "FeatureCollection", features: data.map((e) => ({
    type: "Feature", geometry: { type: "Point", coordinates: [e.lng, e.lat] }, properties: { ...e },
  })) };
}

const emptyLine: GeoJSON.FeatureCollection<GeoJSON.LineString> = { type: "FeatureCollection", features: [] };

export default function GeoMap({ data, escuelas, showEscuelas, selectedId, selectedEscuelaCodigo, onSelect, onSelectEscuela }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const dataRef = useRef(data);
  const escuelasRef = useRef(escuelas);
  const onSelectRef = useRef(onSelect);
  const onSelectEscuelaRef = useRef(onSelectEscuela);

  useEffect(() => { dataRef.current = data; }, [data]);
  useEffect(() => { escuelasRef.current = escuelas; }, [escuelas]);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);
  useEffect(() => { onSelectEscuelaRef.current = onSelectEscuela; }, [onSelectEscuela]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const dominicanRepublicBounds: [[number, number], [number, number]] = [
      [-72.15, 17.30], // Suroeste: frontera, Pedernales y mar territorial cercano
      [-68.05, 20.15], // Noreste: costa norte, Samaná y La Altagracia
    ];

    const map = new maplibregl.Map({
      container: containerRef.current,
      center: [-70.1627, 18.7357],
      zoom: 7.15,
      minZoom: 6.6,
      maxZoom: 19,
      maxBounds: dominicanRepublicBounds,
      renderWorldCopies: false,
      style: { version: 8, glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: { osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap contributors" } },
        layers: [{ id: "osm", type: "raster", source: "osm" }] },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.FullscreenControl(), "top-right");

    map.on("load", () => {
      map.addSource("bancas", { type: "geojson", data: bancasGeoJSON(dataRef.current), cluster: true, clusterMaxZoom: 13, clusterRadius: 52 });
      map.addLayer({ id: "clusters", type: "circle", source: "bancas", filter: ["has", "point_count"], paint: {
        "circle-color": ["step", ["get", "point_count"], "#1593e5", 20, "#0c56b3", 100, "#08111d"],
        "circle-radius": ["step", ["get", "point_count"], 19, 20, 24, 100, 30], "circle-stroke-width": 3, "circle-stroke-color": "#f8fbff", "circle-opacity": .92,
      }});
      map.addLayer({ id: "cluster-count", type: "symbol", source: "bancas", filter: ["has", "point_count"], layout: {
        "text-field": ["get", "point_count_abbreviated"], "text-size": 12, "text-font": ["Open Sans Bold"], "text-allow-overlap": true,
      }, paint: { "text-color": "#f8fbff" } });
      map.addLayer({ id: "unclustered-point", type: "circle", source: "bancas", filter: ["!", ["has", "point_count"]], paint: {
        "circle-color": ["get", "color"], "circle-radius": 8, "circle-stroke-width": 3, "circle-stroke-color": "#f8fbff", "circle-opacity": .96,
      }});

      map.addSource("escuelas", { type: "geojson", data: escuelasGeoJSON(escuelasRef.current), cluster: true, clusterMaxZoom: 12, clusterRadius: 45 });
      map.addLayer({ id: "school-clusters", type: "circle", source: "escuelas", filter: ["has", "point_count"], layout: { visibility: "visible" }, paint: {
        "circle-color": "#8b5cf6", "circle-radius": ["step", ["get", "point_count"], 16, 20, 21, 100, 27], "circle-stroke-width": 3, "circle-stroke-color": "#f8fbff", "circle-opacity": .9,
      }});
      map.addLayer({ id: "school-cluster-count", type: "symbol", source: "escuelas", filter: ["has", "point_count"], layout: {
        visibility: "visible", "text-field": ["get", "point_count_abbreviated"], "text-size": 11, "text-font": ["Open Sans Bold"], "text-allow-overlap": true,
      }, paint: { "text-color": "#fff" } });
      map.addLayer({ id: "school-point", type: "circle", source: "escuelas", filter: ["!", ["has", "point_count"]], layout: { visibility: "visible" }, paint: {
        "circle-color": "#8b5cf6", "circle-radius": 7, "circle-stroke-width": 3, "circle-stroke-color": "#f8fbff", "circle-opacity": .96,
      }});

      map.addSource("proximity-line", { type: "geojson", data: emptyLine });
      map.addLayer({ id: "proximity-line", type: "line", source: "proximity-line", paint: { "line-color": "#22c9f4", "line-width": 3, "line-dasharray": [2, 2] } });

      const expandCluster = async (sourceName: string, layerName: string, event: MapMouseEvent) => {
        const features = map.queryRenderedFeatures(event.point, { layers: [layerName] });
        const clusterId = features[0]?.properties?.cluster_id;
        const source = map.getSource(sourceName) as maplibregl.GeoJSONSource;
        if (clusterId === undefined) return;
        const zoom = await source.getClusterExpansionZoom(clusterId);
        const coordinates = (features[0].geometry as GeoJSON.Point).coordinates as [number, number];
        map.easeTo({ center: coordinates, zoom });
      };
      map.on("click", "clusters", (e) => expandCluster("bancas", "clusters", e));
      map.on("click", "school-clusters", (e) => expandCluster("escuelas", "school-clusters", e));
      map.on("click", "unclustered-point", (event) => {
        const id = event.features?.[0]?.properties?.id as string | undefined;
        const banca = dataRef.current.find((item) => item.id === id);
        if (banca) onSelectRef.current(banca);
      });
      map.on("click", "school-point", (event) => {
        const codigo = event.features?.[0]?.properties?.codigo as string | undefined;
        const escuela = escuelasRef.current.find((item) => item.codigo === codigo);
        if (escuela) onSelectEscuelaRef.current(escuela);
      });
      ["clusters", "unclustered-point", "school-clusters", "school-point"].forEach((layer) => {
        map.on("mouseenter", layer, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; });
      });
    });
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  useEffect(() => { const map = mapRef.current; if (!map?.isStyleLoaded()) return; (map.getSource("bancas") as maplibregl.GeoJSONSource | undefined)?.setData(bancasGeoJSON(data)); }, [data]);
  useEffect(() => { const map = mapRef.current; if (!map?.isStyleLoaded()) return; (map.getSource("escuelas") as maplibregl.GeoJSONSource | undefined)?.setData(escuelasGeoJSON(escuelas)); }, [escuelas]);
  useEffect(() => {
    const map = mapRef.current; if (!map?.isStyleLoaded()) return;
    const visibility = showEscuelas ? "visible" : "none";
    ["school-clusters", "school-cluster-count", "school-point"].forEach((id) => map.setLayoutProperty(id, "visibility", visibility));
  }, [showEscuelas]);

  useEffect(() => {
    const map = mapRef.current; if (!map?.isStyleLoaded()) return;
    const source = map.getSource("proximity-line") as maplibregl.GeoJSONSource | undefined;
    const banca = data.find((item) => item.id === selectedId);
    if (!banca) { source?.setData(emptyLine); return; }
    map.flyTo({ center: [banca.lng, banca.lat], zoom: Math.max(map.getZoom(), 14), duration: 750 });
    const line: GeoJSON.FeatureCollection<GeoJSON.LineString> = { type: "FeatureCollection", features: [{ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [[banca.lng, banca.lat], [banca.escuelaLng, banca.escuelaLat]] } }] };
    source?.setData(line);
  }, [selectedId, data]);

  useEffect(() => {
    const map = mapRef.current; const escuela = escuelas.find((item) => item.codigo === selectedEscuelaCodigo); if (!map || !escuela) return;
    map.flyTo({ center: [escuela.lng, escuela.lat], zoom: Math.max(map.getZoom(), 14), duration: 750 });
  }, [selectedEscuelaCodigo, escuelas]);

  return <div ref={containerRef} className="map" aria-label="Mapa nacional de bancas y centros educativos" />;
}
