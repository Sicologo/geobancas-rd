#!/usr/bin/env python3
"""Extracción optimizada de lugares protegidos RD.

Hace una sola consulta Overpass y clasifica localmente los resultados. Genera
JSON + GeoJSON por capa. Las condiciones jurídicas/administrativas se mantienen
como pendientes salvo que OSM tenga una etiqueta explícita (que tampoco sustituye
la validación oficial).
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "public" / "data"
RD_BOUNDS = (17.45, 20.15, -72.05, -68.20)
CAPITAL_BOUNDS = (18.38, 18.58, -70.08, -69.78)
OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

QUERY = r'''[out:json][timeout:180];
area["ISO3166-1"="DO"][admin_level=2]->.rd;
(
  nwr["amenity"~"^(school|university|kindergarten|childcare|clinic|doctors)$"](area.rd);
  nwr["healthcare"~"^(clinic|doctor|centre|health_centre|health_post|rehabilitation)$"](area.rd);
  nwr["social_facility"="day_care"](area.rd);
  nwr["social_facility:for"~"disabled|autism|mental_health",i](area.rd);
  nwr["landuse"="military"](area.rd);
  nwr["military"](area.rd);
  nwr["office"="military"](area.rd);
  nwr["name"~"CAIPI|CAFI|CAID|estancia infantil|guarder[ií]a|centro infantil|discapacidad|autismo|rehabilitaci[oó]n|s[ií]ndrome de down|Palacio Nacional|Congreso Nacional|Suprema Corte de Justicia|Tribunal Constitucional|Tribunal Superior Electoral|Junta Central Electoral|Defensor del Pueblo|C[aá]mara de Cuentas|Banco Central de la Rep[uú]blica Dominicana|Junta Monetaria|Ej[eé]rcito|Armada|Fuerza A[eé]rea|Ministerio de Defensa|Base A[eé]rea|Base Naval|cuartel militar|campamento militar",i](area.rd);
);
out center tags;'''

LAYER_META = {
    "colegios_privados": ("COLP", "Colegios privados", "OSM puede indicar gestión privada; candidatos por nombre deben validarse contra MINERD/registro correspondiente."),
    "universidades": ("UNI", "Universidades", "La ubicación OSM no sustituye la validación de institución activa o recinto reconocido por MESCyT."),
    "estancias_infantiles": ("ESTI", "Estancias infantiles / CAIPI / CAFI", "Incluye candidatos OSM; la pertenencia a INAIPI u otra red oficial debe validarse institucionalmente."),
    "centros_discapacidad": ("DISC", "CAID / centros de atención a personas con discapacidad", "La condición institucional y el tipo de servicio requieren validación documental."),
    "clinicas_centros_salud": ("SALC", "Clínicas y centros de salud", "La habilitación sanitaria debe validarse con Salud Pública/SNS según corresponda."),
    "cuarteles_recintos_militares": ("MIL", "Cuarteles / recintos militares", "El carácter de recinto militar protegido requiere validación institucional."),
    "sedes_poderes_estado": ("POD", "Sedes principales de los poderes del Estado", "Candidatos a sedes principales de los poderes Ejecutivo, Legislativo y Judicial; contrastar con direcciones oficiales vigentes."),
    "organos_extrapoder": ("EXT", "Órganos extrapoder / constitucionales autónomos", "Busca sedes principales en Gran Santo Domingo; clasificación y sede deben validarse jurídica e institucionalmente."),
}


def clean(v: object) -> str:
    return str(v or "").strip()


def inside(bounds, lat: float, lon: float) -> bool:
    a, b, c, d = bounds
    return a <= lat <= b and c <= lon <= d


def coord(e: dict):
    if e.get("type") == "node":
        return e.get("lat"), e.get("lon")
    c = e.get("center") or {}
    return c.get("lat"), c.get("lon")


def address(t: dict) -> str:
    if clean(t.get("addr:full")):
        return clean(t["addr:full"])
    return " ".join(x for x in (clean(t.get("addr:street")), clean(t.get("addr:housenumber"))) if x)


def fetch() -> list[dict]:
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    last = None
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(1, 3):
            try:
                req = urllib.request.Request(endpoint, data=body, headers={
                    "User-Agent": "CumplimientoRD-Geobancas/2.0",
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                }, method="POST")
                with urllib.request.urlopen(req, timeout=210) as r:
                    data = json.load(r)
                elements = data.get("elements")
                if not isinstance(elements, list):
                    raise RuntimeError("Overpass sin elements")
                print(f"Overpass: {len(elements)} elementos")
                return elements
            except Exception as exc:
                last = exc
                print(f"[warn] {endpoint} intento {attempt}/2: {exc}", file=sys.stderr)
                time.sleep(attempt * 3)
    raise RuntimeError(f"No se pudo consultar Overpass: {last}")


def base_record(layer: str, e: dict, t: dict, name: str, lat: float, lon: float) -> dict:
    prefix, title, _ = LAYER_META[layer]
    typ, oid = clean(e.get("type")), e.get("id")
    rec = {
        "id": f"{prefix}-OSM-{typ.upper()}-{oid}", "nombre": name, "categoria": title,
        "direccion": address(t),
        "ciudad": clean(t.get("addr:city") or t.get("addr:town") or t.get("addr:village")),
        "provincia": clean(t.get("addr:province") or t.get("addr:state")),
        "telefono": clean(t.get("contact:phone") or t.get("phone")),
        "website": clean(t.get("contact:website") or t.get("website")),
        "lat": round(lat, 7), "lon": round(lon, 7),
        "osm_type": typ, "osm_id": oid,
        "osm_url": f"https://www.openstreetmap.org/{typ}/{oid}",
        "fuente": "OpenStreetMap", "validada": False,
    }
    if layer == "colegios_privados":
        explicit = any(clean(t.get(k)).casefold() == "private" for k in ("operator:type", "ownership", "access"))
        rec.update(privado_confirmado_osm=explicit, criterio_privado="confirmado_por_etiqueta_osm" if explicit else "candidato_por_nombre", validacion_minerd="pendiente")
    elif layer == "universidades": rec["reconocida_mescyt"] = "pendiente"
    elif layer == "estancias_infantiles": rec.update(red_institucional="INAIPI-candidata" if re.search(r"\b(CAIPI|CAFI)\b", name, re.I) else "pendiente", validacion_inaipi="pendiente")
    elif layer == "centros_discapacidad": rec.update(caid_candidato=bool(re.search(r"\bCAID\b|Centro de Atención Integral para la Discapacidad", name, re.I)), validacion_institucional="pendiente")
    elif layer == "clinicas_centros_salud": rec["habilitacion_sanitaria"] = "pendiente"
    elif layer == "cuarteles_recintos_militares": rec.update(recinto_militar_validado=False, validacion_mide="pendiente")
    elif layer in ("sedes_poderes_estado", "organos_extrapoder"): rec.update(sede_principal_validada=False, validacion_institucional="pendiente")
    if layer == "organos_extrapoder": rec["clasificacion_juridica"] = "candidato_extrapoder"
    return rec


def classify(e: dict) -> list[tuple[str, dict]]:
    t = e.get("tags") or {}
    lat, lon = coord(e)
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or not inside(RD_BOUNDS, float(lat), float(lon)):
        return []
    lat, lon = float(lat), float(lon)
    name = clean(t.get("name") or t.get("name:es") or t.get("official_name"))
    amenity = clean(t.get("amenity")).casefold()
    healthcare = clean(t.get("healthcare")).casefold()
    sf_for = clean(t.get("social_facility:for")).casefold()
    nl = name.casefold()
    layers: list[str] = []

    # Colegio privado: etiqueta explícita o nombre típicamente privado. No se presume privado por ser simplemente school.
    if amenity == "school":
        explicit = any(clean(t.get(k)).casefold() == "private" for k in ("operator:type", "ownership", "access"))
        heuristic = bool(re.search(r"\b(colegio|academy|academia|school)\b", name, re.I))
        if explicit or heuristic: layers.append("colegios_privados")
    if amenity == "university" or re.search(r"\buniversidad\b|\buniversity\b", name, re.I): layers.append("universidades")
    if amenity in {"kindergarten", "childcare"} or clean(t.get("social_facility")) == "day_care" or re.search(r"CAIPI|CAFI|estancia infantil|guarder[ií]a|centro infantil", name, re.I): layers.append("estancias_infantiles")
    if re.search(r"CAID|discapacidad|autismo|rehabilitaci[oó]n|s[ií]ndrome de down", name, re.I) or re.search(r"disabled|autism|mental_health", sf_for, re.I): layers.append("centros_discapacidad")
    if amenity in {"clinic", "doctors"} or healthcare in {"clinic", "doctor", "centre", "health_centre", "health_post", "rehabilitation"}: layers.append("clinicas_centros_salud")
    if clean(t.get("landuse")).casefold() == "military" or clean(t.get("military")) or clean(t.get("office")).casefold() == "military" or re.search(r"Ej[eé]rcito|Armada|Fuerza A[eé]rea|Ministerio de Defensa|Base A[eé]rea|Base Naval|cuartel militar|campamento militar", name, re.I): layers.append("cuarteles_recintos_militares")

    if inside(CAPITAL_BOUNDS, lat, lon):
        if re.search(r"^(Palacio Nacional|Congreso Nacional|Suprema Corte de Justicia|Palacio de Justicia de la Suprema Corte de Justicia)$", name, re.I): layers.append("sedes_poderes_estado")
        if re.search(r"^(Tribunal Constitucional|Tribunal Superior Electoral|Junta Central Electoral|Defensor del Pueblo|C[aá]mara de Cuentas|Banco Central de la Rep[uú]blica Dominicana|Junta Monetaria)$", name, re.I): layers.append("organos_extrapoder")

    return [(layer, base_record(layer, e, t, name or f"{LAYER_META[layer][1]} sin nombre", lat, lon)) for layer in dict.fromkeys(layers)]


def dedupe(records: list[dict]) -> list[dict]:
    seen_osm = set(); seen_spatial = set(); out = []
    for r in sorted(records, key=lambda x: (x["nombre"].casefold(), x["id"])):
        ok = (r["osm_type"], r["osm_id"])
        if ok in seen_osm: continue
        seen_osm.add(ok)
        if "sin nombre" not in r["nombre"].casefold():
            sk = (r["nombre"].casefold().strip(), round(r["lat"] * 10000), round(r["lon"] * 10000))
            if sk in seen_spatial: continue
            seen_spatial.add(sk)
        out.append(r)
    return out


def write_layer(layer: str, records: list[dict], generated: str) -> None:
    _, title, notice = LAYER_META[layer]
    records = dedupe(records)
    if not records: raise RuntimeError(f"{layer}: 0 registros")
    named = sum("sin nombre" not in r["nombre"].casefold() for r in records)
    payload = {"meta": {"total": len(records), "con_nombre": named, "sin_nombre": len(records)-named, "source": "OpenStreetMap via Overpass API", "license": "ODbL 1.0", "generated_at": generated, "country": "República Dominicana", "categoria": title, "legal_notice": notice}, "records": records}
    (DATA_DIR / f"{layer}.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    feats = [{"type":"Feature","geometry":{"type":"Point","coordinates":[r["lon"],r["lat"]]},"properties":{k:v for k,v in r.items() if k not in {"lat","lon"}}} for r in records]
    geo = {"type":"FeatureCollection","name":f"{layer}_rd_osm","attribution":"© OpenStreetMap contributors, ODbL 1.0","generated_at":generated,"features":feats}
    (DATA_DIR / f"{layer}.geojson").write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{layer}: {len(records)}")


def write_churches(generated: str) -> None:
    src = DATA_DIR / "iglesias.json"
    if not src.exists(): raise RuntimeError("Falta public/data/iglesias.json")
    old = json.loads(src.read_text(encoding="utf-8"))
    records = []
    for r in old.get("records", []):
        x = dict(r); x["categoria"] = "Iglesias debidamente incorporadas - candidatas"; x["incorporacion_verificada"] = False; x["validacion_pgr_dgii"] = "pendiente"; records.append(x)
    notice = "La presencia en OSM NO demuestra incorporación. La incorporación/registro debe verificarse documentalmente ante la autoridad competente (PGR/DGII según aplique)."
    payload = {"meta":{"total":len(records),"con_nombre":sum("sin nombre" not in r["nombre"].casefold() for r in records),"sin_nombre":sum("sin nombre" in r["nombre"].casefold() for r in records),"source":"OpenStreetMap + capa iglesias.json","license":"ODbL 1.0","generated_at":generated,"country":"República Dominicana","categoria":"Iglesias debidamente incorporadas - candidatas","legal_notice":notice},"records":records}
    (DATA_DIR/"iglesias_incorporadas_candidatas.json").write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    feats=[{"type":"Feature","geometry":{"type":"Point","coordinates":[r["lon"],r["lat"]]},"properties":{k:v for k,v in r.items() if k not in {"lat","lon"}}} for r in records]
    (DATA_DIR/"iglesias_incorporadas_candidatas.geojson").write_text(json.dumps({"type":"FeatureCollection","name":"iglesias_incorporadas_candidatas_rd","attribution":"© OpenStreetMap contributors, ODbL 1.0","generated_at":generated,"features":feats},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"iglesias_incorporadas_candidatas: {len(records)}")


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    buckets = {k: [] for k in LAYER_META}
    for e in fetch():
        for layer, rec in classify(e): buckets[layer].append(rec)
    for layer, recs in buckets.items(): write_layer(layer, recs, generated)
    write_churches(generated)
    return 0

if __name__ == "__main__": raise SystemExit(main())
