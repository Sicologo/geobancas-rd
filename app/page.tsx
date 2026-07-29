"use client";

import { useEffect, useMemo, useState } from "react";
import GeoMap from "@/components/GeoMap";
import {
  expandirBanca, expandirEscuela,
  type Banca, type BancasPayload, type Escuela, type EscuelasPayload,
} from "@/lib/sample-data";

const all = "Todos";
const formatDistance = (meters: number) => meters < 1000 ? `${Math.round(meters)} m` : `${(meters / 1000).toFixed(2)} km`;
const LOTTERY_SCHOOL_LIMIT_M = 200;

function haversineMeters(lat1: number, lng1: number, lat2: number, lng2: number) {
  const radius = 6371000;
  const toRad = (value: number) => value * Math.PI / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return radius * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function attachNearestSchool(banca: Banca, schools: Escuela[]): Banca {
  if (!schools.length) return banca;
  let nearest = schools[0];
  let nearestDistance = haversineMeters(banca.lat, banca.lng, nearest.lat, nearest.lng);
  for (let i = 1; i < schools.length; i += 1) {
    const school = schools[i];
    const distance = haversineMeters(banca.lat, banca.lng, school.lat, school.lng);
    if (distance < nearestDistance) { nearest = school; nearestDistance = distance; }
  }
  return {
    ...banca,
    escuelaCercanaCodigo: nearest.codigo,
    escuelaCercanaNombre: nearest.nombre,
    escuelaDistanciaM: Math.round(nearestDistance * 10) / 10,
    escuelaLat: nearest.lat,
    escuelaLng: nearest.lng,
  };
}

export default function Home() {
  const [bancas, setBancas] = useState<Banca[]>([]);
  const [escuelas, setEscuelas] = useState<Escuela[]>([]);
  const [datasetMeta, setDatasetMeta] = useState({ total: 70136, mapped: 0, pending: 70136 });
  const [schoolMeta, setSchoolMeta] = useState({ total: 0, mapped: 0, invalid: 0, source: "" });
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState(all);
  const [province, setProvince] = useState(all);
  const [risk, setRisk] = useState(all);
  const [selected, setSelected] = useState<Banca | null>(null);
  const [selectedSchool, setSelectedSchool] = useState<Escuela | null>(null);
  const [showSchools, setShowSchools] = useState(true);
  const [filtersOpen, setFiltersOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true); setLoadError(null);
    Promise.all([
      fetch("/data/bancas.json", { cache: "force-cache" }).then((r) => {
        if (!r.ok) throw new Error("No fue posible cargar la base de bancas");
        return r.json() as Promise<BancasPayload>;
      }),
      fetch("/data/escuelas.json", { cache: "force-cache" }).then((r) => {
        if (!r.ok) throw new Error("No fue posible cargar el listado de escuelas");
        return r.json() as Promise<EscuelasPayload>;
      }),
    ]).then(([bancasPayload, escuelasPayload]) => {
      if (!active) return;
      setBancas(bancasPayload.records.map(expandirBanca));
      setEscuelas(escuelasPayload.records.map(expandirEscuela));
      setDatasetMeta(bancasPayload.meta);
      setSchoolMeta(escuelasPayload.meta);
      setLoading(false);
    }).catch((error: unknown) => {
      if (!active) return;
      console.error(error);
      setLoadError(error instanceof Error ? error.message : "No fue posible cargar los datos geográficos");
      setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const provinces = useMemo(() => [all, ...Array.from(new Set(bancas.map((b) => b.provincia))).sort()], [bancas]);
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return bancas.filter((b) => {
      const matchesQuery = !q || [b.id, b.nombre, b.propietario, b.provincia, b.municipio, b.sector, b.direccion, b.escuelaCercanaNombre].some((v) => v.toLowerCase().includes(q));
      return matchesQuery && (status === all || b.estatus === status) && (province === all || b.provincia === province) && (risk === all || b.riesgo === risk);
    });
  }, [bancas, query, status, province, risk]);

  const filteredSchools = useMemo(() => province === all ? escuelas : escuelas.filter((e) => e.provincia === province), [escuelas, province]);
  const totals = useMemo(() => ({ total: datasetMeta.total, ubicadas: datasetMeta.mapped, escuelas: schoolMeta.mapped, pendientes: datasetMeta.pending }), [datasetMeta, schoolMeta]);
  const clearFilters = () => { setQuery(""); setStatus(all); setProvince(all); setRisk(all); setSelected(null); setSelectedSchool(null); };

  useEffect(() => { if (selected && !filtered.some((item) => item.id === selected.id)) setSelected(null); }, [filtered, selected]);

  const selectBanca = (banca: Banca) => {
    setSelectedSchool(null);
    setShowSchools(true);
    setSelected(attachNearestSchool(banca, escuelas));
  };
  const selectSchool = (school: Escuela) => { setSelected(null); setSelectedSchool(school); };
  const openNearestSchool = () => {
    if (!selected) return;
    const school = escuelas.find((e) => e.codigo === selected.escuelaCercanaCodigo);
    if (school) { setShowSchools(true); setSelectedSchool(school); }
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand-lockup"><div className="brand-mark">GB</div><div><strong>GeoBancas RD</strong><span>Supervisión territorial nacional</span></div></div>
        <div className="header-actions"><button className="ghost-button">Exportar</button><button className="primary-button">Importar base</button><div className="user-chip"><span>SC</span><div><strong>Sicologo</strong><small>Administrador</small></div></div></div>
      </header>

      <section className="map-workspace">
        <GeoMap data={filtered} escuelas={filteredSchools} showEscuelas={showSchools} selectedId={selected?.id} selectedEscuelaCodigo={selectedSchool?.codigo} onSelect={selectBanca} onSelectEscuela={selectSchool} />

        {(loading || loadError) && <div className={`data-state ${loadError ? "error" : ""}`} role="status"><div className="data-state-icon">{loadError ? "!" : <span className="loader" />}</div><div><strong>{loadError ? "No se pudieron cargar los datos" : "Cargando capas geográficas"}</strong><span>{loadError ?? "Preparando bancas, escuelas y distancias…"}</span></div></div>}

        <aside className={`control-panel ${filtersOpen ? "open" : "closed"}`}>
          <div className="panel-head"><div><span className="eyebrow">Control geográfico</span><h1>Mapa nacional</h1></div><button className="icon-button" onClick={() => setFiltersOpen(false)} aria-label="Cerrar filtros">×</button></div>
          <label className="search-box"><span>⌕</span><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar banca, código, propietario o escuela" /></label>
          <div className="filter-grid">
            <label><span>Provincia</span><select value={province} onChange={(e) => setProvince(e.target.value)}>{provinces.map((p) => <option key={p}>{p}</option>)}</select></label>
            <label><span>Estatus</span><select value={status} onChange={(e) => setStatus(e.target.value)}><option>Todos</option><option>Legal</option><option>Ilegal</option><option>Pendiente</option><option>Suspendida</option></select></label>
            <label><span>Nivel de riesgo</span><select value={risk} onChange={(e) => setRisk(e.target.value)}><option>Todos</option><option>Bajo</option><option>Moderado</option><option>Alto</option></select></label>
          </div>
          <div className="layer-switch"><div><strong>Capa de escuelas</strong><small>{filteredSchools.length.toLocaleString("es-DO")} centros con coordenadas</small></div><button className={showSchools ? "active" : ""} onClick={() => setShowSchools((v) => !v)} aria-pressed={showSchools}><span /></button></div>
          <div className="filter-footer"><strong>{loading ? "Cargando…" : `${filtered.length.toLocaleString("es-DO")} bancas visibles`}</strong><button onClick={clearFilters}>Limpiar filtros</button></div>
          <div className="legend"><strong>Leyenda</strong><div><span className="dot legal" />Legal</div><div><span className="dot pending" />Pendiente</div><div><span className="dot illegal" />Ilegal</div><div><span className="dot suspended" />Suspendida</div><div><span className="dot school" />Escuela</div></div>
        </aside>

        {!filtersOpen && <button className="open-panel" onClick={() => setFiltersOpen(true)}>Filtros</button>}
        <section className="map-stats"><article><span>Total registradas</span><strong>{totals.total.toLocaleString("es-DO")}</strong></article><article><span>Con ubicación</span><strong>{totals.ubicadas.toLocaleString("es-DO")}</strong></article><article><span>Escuelas ubicadas</span><strong>{totals.escuelas.toLocaleString("es-DO")}</strong></article><article><span>Por validar</span><strong>{totals.pendientes.toLocaleString("es-DO")}</strong></article></section>
        <div className="map-tools"><button title="Capas" onClick={() => setShowSchools((v) => !v)}>▱</button><button title="Mapa de calor">◉</button><button title="Medir distancia">↔</button></div>

        {selected && <aside className="detail-card">
          <div className="detail-top"><div><span className="record-code">{selected.id}</span><h2>{selected.nombre}</h2></div><button onClick={() => setSelected(null)}>×</button></div>
          <div className="status-row"><span className={`status-badge ${selected.estatus.toLowerCase()}`}>{selected.estatus}</span><span className={`risk-badge ${selected.riesgo.toLowerCase()}`}>Riesgo {selected.riesgo}</span></div>
          <dl><div><dt>Propietario</dt><dd>{selected.propietario}</dd></div><div><dt>Ubicación</dt><dd>{selected.sector}, {selected.municipio}</dd></div><div><dt>Dirección</dt><dd>{selected.direccion}</dd></div><div><dt>Coordenadas</dt><dd>{selected.lat.toFixed(6)}, {selected.lng.toFixed(6)}</dd></div></dl>
          <div className="proximity-box school-proximity">
            <span>Escuela más cercana</span>
            <strong>{selected.escuelaCercanaNombre || "No identificada"}</strong>
            <div className="distance-value">{Number.isFinite(selected.escuelaDistanciaM) ? formatDistance(selected.escuelaDistanciaM) : "Sin cálculo"}</div>
            <div className={`compliance-result ${selected.escuelaDistanciaM < LOTTERY_SCHOOL_LIMIT_M ? "alert" : "ok"}`}>
              <b>{selected.escuelaDistanciaM < LOTTERY_SCHOOL_LIMIT_M ? "Posible incumplimiento" : "Fuera del radio restringido"}</b>
              <em>Referencia activa: banca de lotería · mínimo {LOTTERY_SCHOOL_LIMIT_M} m lineales</em>
              <small>{selected.escuelaDistanciaM < LOTTERY_SCHOOL_LIMIT_M ? `Faltan aproximadamente ${Math.ceil(LOTTERY_SCHOOL_LIMIT_M - selected.escuelaDistanciaM)} m para alcanzar la distancia mínima.` : `Supera la referencia por aproximadamente ${Math.floor(selected.escuelaDistanciaM - LOTTERY_SCHOOL_LIMIT_M)} m.`}</small>
            </div>
            <small>Distancia geodésica en línea recta entre las coordenadas disponibles. Debe confirmarse mediante inspección y medición oficial.</small>
            <button onClick={openNearestSchool}>Ver escuela y línea de distancia</button>
          </div>
          <div className="detail-actions"><button>Ver expediente</button><button className="primary-button">Inspeccionar</button></div>
        </aside>}

        {selectedSchool && <aside className="detail-card school-card">
          <div className="detail-top"><div><span className="record-code">CENTRO {selectedSchool.codigo}</span><h2>{selectedSchool.nombre}</h2></div><button onClick={() => setSelectedSchool(null)}>×</button></div>
          <div className="status-row"><span className="school-badge">Centro educativo</span><span className="risk-badge">{selectedSchool.sector || "Sin sector"}</span></div>
          <dl><div><dt>Provincia</dt><dd>{selectedSchool.provincia}</dd></div><div><dt>Municipio</dt><dd>{selectedSchool.municipio}</dd></div><div><dt>Nivel</dt><dd>{selectedSchool.nivel}</dd></div><div><dt>Matrícula</dt><dd>{selectedSchool.matricula.toLocaleString("es-DO")}</dd></div><div><dt>Regional</dt><dd>{selectedSchool.regional}</dd></div><div><dt>Distrito</dt><dd>{selectedSchool.distrito}</dd></div></dl>
          <div className="proximity-box"><span>Fuente</span><strong>{schoolMeta.source}</strong><small>Registro cargado desde el archivo oficial suministrado.</small></div>
        </aside>}

        <div className="map-status"><span className={`pulse ${loadError ? "offline" : ""}`} />{loadError ? "Datos no disponibles" : loading ? "Cargando capas nacionales…" : `Mapa conectado · ${filtered.length.toLocaleString("es-DO")} bancas · ${showSchools ? `${filteredSchools.length.toLocaleString("es-DO")} escuelas` : "escuelas ocultas"}`}</div>
      </section>
    </main>
  );
}
