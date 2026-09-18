#!/usr/bin/env python3
"""Genera capas de lugares protegidos de República Dominicana usando OpenStreetMap.

Fuentes geográficas: OpenStreetMap / Overpass API (ODbL 1.0).
El objetivo es obtener candidatos geográficos para Cumplimiento RD. Cuando una
categoría exige una condición jurídica/administrativa (privado, incorporada,
reconocida, sede principal, etc.), esa condición NO se presume a partir de OSM:
se conserva un campo explícito de validación pendiente.
"""

from __future__ import annotations

import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "public" / "data"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

RD_BOUNDS = (17.45, 20.15, -72.05, -68.20)
CAPITAL_BOUNDS = (18.38, 18.58, -70.08, -69.78)


def q(body: str) -> str:
    return f'''[out:json][timeout:240];
area["ISO3166-1"="DO"][admin_level=2]->.rd;
(
{body}
);
out center tags;'''


LAYERS: dict[str, dict] = {
    "colegios_privados": {
        "prefix": "COLP",
        "title": "Colegios privados",
        "query": q('''  nwr["amenity"="school"]["operator:type"="private"](area.rd);
  nwr["amenity"="school"]["ownership"="private"](area.rd);
  nwr["amenity"="school"]["access"="private"](area.rd);
  nwr["amenity"="school"]["name"~"colegio|academy|academia|school",i](area.rd);'''),
        "legal_notice": "OSM puede indicar gestión privada, pero los candidatos por nombre requieren validación contra MINERD/registro correspondiente.",
    },
    "universidades": {
        "prefix": "UNI",
        "title": "Universidades",
        "query": q('''  nwr["amenity"="university"](area.rd);
  nwr["name"~"universidad|university|UASD|PUCMM|INTEC|UNIBE|UNPHU|UTESA|UCE|UCSD|UNAPEC|O&M|UCATEBA|UCNE|UTECO|UAPA",i](area.rd);'''),
        "legal_notice": "La ubicación OSM no sustituye la validación de institución activa o recinto reconocido por MESCyT.",
    },
    "estancias_infantiles": {
        "prefix": "ESTI",
        "title": "Estancias infantiles / CAIPI / CAFI",
        "query": q('''  nwr["amenity"="kindergarten"](area.rd);
  nwr["amenity"="childcare"](area.rd);
  nwr["social_facility"="day_care"](area.rd);
  nwr["name"~"CAIPI|CAFI|estancia infantil|guarder[ií]a|centro infantil",i](area.rd);'''),
        "legal_notice": "Incluye candidatos OSM; la pertenencia a INAIPI u otra red oficial debe validarse con la fuente institucional.",
    },
    "centros_discapacidad": {
        "prefix": "DISC",
        "title": "CAID / centros de atención a personas con discapacidad",
        "query": q('''  nwr["name"~"CAID|Centro de Atenci[oó]n Integral para la Discapacidad",i](area.rd);
  nwr["social_facility:for"~"disabled|autism|mental_health",i](area.rd);
  nwr["name"~"discapacidad|autismo|rehabilitaci[oó]n|s[ií]ndrome de down",i](area.rd);'''),
        "legal_notice": "CAID y otros centros se identifican geográficamente; la condición institucional y el tipo de servicio deben validarse documentalmente.",
    },
    "clinicas_centros_salud": {
        "prefix": "SALC",
        "title": "Clínicas y centros de salud",
        "query": q('''  nwr["amenity"="clinic"](area.rd);
  nwr["amenity"="doctors"](area.rd);
  nwr["healthcare"="clinic"](area.rd);
  nwr["healthcare"="doctor"](area.rd);
  nwr["healthcare"="centre"](area.rd);
  nwr["healthcare"="health_centre"](area.rd);
  nwr["healthcare"="health_post"](area.rd);
  nwr["healthcare"="rehabilitation"](area.rd);'''),
        "legal_notice": "Capa geográfica OSM de clínicas y centros de salud; habilitación sanitaria debe validarse con Salud Pública/SNS según corresponda.",
    },
    "cuarteles_recintos_militares": {
        "prefix": "MIL",
        "title": "Cuarteles / recintos militares",
        "query": q('''  nwr["landuse"="military"](area.rd);
  nwr["military"](area.rd);
  nwr["office"="military"](area.rd);
  nwr["name"~"Ej[eé]rcito|Armada|Fuerza A[eé]rea|Ministerio de Defensa|Base A[eé]rea|Base Naval|cuartel militar|campamento militar",i](area.rd);'''),
        "legal_notice": "Los objetos OSM se tratan como candidatos de instalaciones militares; el carácter de recinto/cuarto militar protegido requiere validación institucional.",
    },
    "sedes_poderes_estado": {
        "prefix": "POD",
        "title": "Sedes principales de los poderes del Estado",
        "capital_only": True,
        "query": q('''  nwr["name"~"^(Palacio Nacional|Congreso Nacional|Suprema Corte de Justicia|Palacio de Justicia de la Suprema Corte de Justicia)$",i](area.rd);
  nwr["official_name"~"Presidencia de la Rep[uú]blica|Congreso Nacional|Suprema Corte de Justicia",i](area.rd);'''),
        "legal_notice": "Candidatos a sedes principales del Poder Ejecutivo, Legislativo y Judicial; deben contrastarse con las direcciones oficiales vigentes.",
    },
    "organos_extrapoder": {
        "prefix": "EXT",
        "title": "Órganos extrapoder / constitucionales autónomos",
        "capital_only": True,
        "query": q('''  nwr["name"~"^(Tribunal Constitucional|Tribunal Superior Electoral|Junta Central Electoral|Defensor del Pueblo|C[aá]mara de Cuentas|Banco Central de la Rep[uú]blica Dominicana|Junta Monetaria)$",i](area.rd);
  nwr["official_name"~"Tribunal Constitucional|Tribunal Superior Electoral|Junta Central Electoral|Defensor del Pueblo|C[aá]mara de Cuentas|Banco Central|Junta Monetaria",i](area.rd);'''),
        "legal_notice": "La capa busca sedes principales en el Gran Santo Domingo. La clasificación extrapoder y la sede deben validarse jurídicamente/institucionalmente.",
    },
}


def clean(value: object) -> str:
    return str(value or "").strip()


def coord(element: dict) -> tuple[float | None, float | None]:
    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")
    center = element.get("center") or {}
    return center.get("lat"), center.get("lon")


def address(tags: dict) -> str:
    full = clean(tags.get("addr:full"))
    if full:
        return full
    street = clean(tags.get("addr:street"))
    number = clean(tags.get("addr:housenumber"))
    return " ".join(x for x in (street, number) if x)


def inside(bounds: tuple[float, float, float, float], lat: float, lon: float) -> bool:
    min_lat, max_lat, min_lon, max_lon = bounds
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def fetch_overpass(query: str, label: str) -> dict:
    body = urllib.parse.urlencode({"data": query}).encode("utf-8")
    last_error: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=body,
                    headers={
                        "User-Agent": "CumplimientoRD-Geobancas/1.1 (protected places generator)",
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=270) as response:
                    payload = json.load(response)
                if not isinstance(payload.get("elements"), list):
                    raise RuntimeError("Overpass respondió sin elements")
                print(f"[{label}] Overpass OK: {len(payload['elements'])} elementos")
                return payload
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                print(f"[warn] [{label}] {endpoint} intento {attempt}/3: {exc}", file=sys.stderr)
                time.sleep(attempt * 4)
    raise RuntimeError(f"[{label}] no se pudo consultar Overpass: {last_error}")


def normalize_name(s: str) -> str:
    s = s.casefold().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def private_status(tags: dict, name: str) -> tuple[bool, str]:
    explicit = any(
        clean(tags.get(k)).casefold() == "private"
        for k in ("operator:type", "ownership", "access")
    )
    if explicit:
        return True, "confirmado_por_etiqueta_osm"
    if re.search(r"\b(colegio|academy|academia|school)\b", name, re.I):
        return False, "candidato_por_nombre"
    return False, "pendiente"


def record_extra(layer: str, tags: dict, name: str) -> dict:
    if layer == "colegios_privados":
        confirmed, method = private_status(tags, name)
        return {"privado_confirmado_osm": confirmed, "criterio_privado": method, "validacion_minerd": "pendiente"}
    if layer == "universidades":
        return {"reconocida_mescyt": "pendiente"}
    if layer == "estancias_infantiles":
        network = "INAIPI-candidata" if re.search(r"\b(CAIPI|CAFI)\b", name, re.I) else "pendiente"
        return {"red_institucional": network, "validacion_inaipi": "pendiente"}
    if layer == "centros_discapacidad":
        is_caid = bool(re.search(r"\bCAID\b|Centro de Atención Integral para la Discapacidad", name, re.I))
        return {"caid_candidato": is_caid, "validacion_institucional": "pendiente"}
    if layer == "clinicas_centros_salud":
        return {"habilitacion_sanitaria": "pendiente"}
    if layer == "cuarteles_recintos_militares":
        return {"recinto_militar_validado": False, "validacion_mide": "pendiente"}
    if layer == "sedes_poderes_estado":
        return {"sede_principal_validada": False, "validacion_institucional": "pendiente"}
    if layer == "organos_extrapoder":
        return {"sede_principal_validada": False, "clasificacion_juridica": "candidato_extrapoder", "validacion_institucional": "pendiente"}
    return {}


def normalize(layer: str, cfg: dict, elements: list[dict]) -> list[dict]:
    raw: list[dict] = []
    seen_osm: set[str] = set()
    for element in elements:
        osm_type = clean(element.get("type"))
        osm_id = element.get("id")
        uid = f"{osm_type}/{osm_id}"
        if uid in seen_osm:
            continue
        seen_osm.add(uid)
        lat, lon = coord(element)
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        lat = float(lat)
        lon = float(lon)
        if not inside(RD_BOUNDS, lat, lon):
            continue
        if cfg.get("capital_only") and not inside(CAPITAL_BOUNDS, lat, lon):
            continue

        tags = element.get("tags") or {}
        name = clean(tags.get("name") or tags.get("name:es") or tags.get("official_name"))
        if not name:
            name = f"{cfg['title']} sin nombre"

        city = clean(tags.get("addr:city") or tags.get("addr:town") or tags.get("addr:village"))
        province = clean(tags.get("addr:province") or tags.get("addr:state"))
        phone = clean(tags.get("contact:phone") or tags.get("phone"))
        website = clean(tags.get("contact:website") or tags.get("website"))

        rec = {
            "id": f"{cfg['prefix']}-OSM-{osm_type.upper()}-{osm_id}",
            "nombre": name,
            "categoria": cfg["title"],
            "direccion": address(tags),
            "ciudad": city,
            "provincia": province,
            "telefono": phone,
            "website": website,
            "lat": round(lat, 7),
            "lon": round(lon, 7),
            "osm_type": osm_type,
            "osm_id": osm_id,
            "osm_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
            "fuente": "OpenStreetMap",
            "validada": False,
        }
        rec.update(record_extra(layer, tags, name))
        raw.append(rec)

    # Deduplicación pragmática: mismo nombre casi en el mismo punto. Conservamos
    # elementos sin nombre porque pueden representar instalaciones distintas.
    out: list[dict] = []
    seen_spatial: set[tuple[str, int, int]] = set()
    unnamed_token = f"{cfg['title']} sin nombre".casefold()
    for rec in sorted(raw, key=lambda r: (r["nombre"].casefold(), r["id"])):
        nn = normalize_name(rec["nombre"])
        if nn != unnamed_token:
            key = (nn, round(rec["lat"] * 10000), round(rec["lon"] * 10000))
            if key in seen_spatial:
                continue
            seen_spatial.add(key)
        out.append(rec)
    return out


def write_layer(layer: str, cfg: dict, records: list[dict], generated_at: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DATA_DIR / f"{layer}.json"
    geojson_path = DATA_DIR / f"{layer}.geojson"
    named = sum(1 for r in records if " sin nombre" not in r["nombre"].casefold())
    output = {
        "meta": {
            "total": len(records),
            "con_nombre": named,
            "sin_nombre": len(records) - named,
            "source": "OpenStreetMap via Overpass API",
            "license": "ODbL 1.0",
            "generated_at": generated_at,
            "country": "República Dominicana",
            "categoria": cfg["title"],
            "legal_notice": cfg["legal_notice"],
        },
        "records": records,
    }
    json_path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    features = []
    for rec in records:
        props = {k: v for k, v in rec.items() if k not in {"lat", "lon"}}
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [rec["lon"], rec["lat"]]},
            "properties": props,
        })
    geo = {
        "type": "FeatureCollection",
        "name": f"{layer}_rd_osm",
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        "generated_at": generated_at,
        "features": features,
    }
    geojson_path.write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[{layer}] {len(records)} registros -> {json_path.name}, {geojson_path.name}")


def write_church_candidates(generated_at: str) -> int:
    source = DATA_DIR / "iglesias.json"
    if not source.exists():
        print("[warn] iglesias.json no existe; se omite iglesias_incorporadas_candidatas", file=sys.stderr)
        return 0
    data = json.loads(source.read_text(encoding="utf-8"))
    records = []
    for item in data.get("records", []):
        rec = dict(item)
        rec["categoria"] = "Iglesias debidamente incorporadas - candidatas"
        rec["incorporacion_verificada"] = False
        rec["validacion_pgr_dgii"] = "pendiente"
        records.append(rec)
    cfg = {
        "title": "Iglesias debidamente incorporadas - candidatas",
        "legal_notice": "La ubicación de una iglesia en OSM NO demuestra incorporación. Para iglesias no católicas, la incorporación/registro debe verificarse documentalmente ante las autoridades competentes (p. ej., PGR/DGII según aplique).",
    }
    write_layer("iglesias_incorporadas_candidatas", cfg, records, generated_at)
    return len(records)


def main() -> int:
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    totals: dict[str, int] = {}
    for layer, cfg in LAYERS.items():
        payload = fetch_overpass(cfg["query"], layer)
        records = normalize(layer, cfg, payload["elements"])
        if not records:
            raise RuntimeError(f"{layer}: la extracción devolvió 0 registros; se cancela para evitar datos vacíos.")
        write_layer(layer, cfg, records, generated_at)
        totals[layer] = len(records)
        time.sleep(2)

    totals["iglesias_incorporadas_candidatas"] = write_church_candidates(generated_at)
    print("RESUMEN", json.dumps(totals, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
