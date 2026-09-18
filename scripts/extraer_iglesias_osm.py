#!/usr/bin/env python3
"""Extrae lugares de culto de República Dominicana desde OpenStreetMap/Overpass.

Genera:
  public/data/iglesias.json
  public/data/iglesias.geojson

Los datos OSM están sujetos a ODbL 1.0. Un punto detectado NO implica que la
entidad esté legalmente incorporada en República Dominicana.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

QUERY = r'''[out:json][timeout:240];
area["ISO3166-1"="DO"][admin_level=2]->.rd;
(
  nwr["amenity"="place_of_worship"](area.rd);
  nwr["building"="church"](area.rd);
  nwr["building"="chapel"](area.rd);
);
out center tags;'''

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "public" / "data"
JSON_PATH = DATA_DIR / "iglesias.json"
GEOJSON_PATH = DATA_DIR / "iglesias.geojson"


def fetch_overpass() -> dict:
    body = urllib.parse.urlencode({"data": QUERY}).encode("utf-8")
    last_error: Exception | None = None

    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=body,
                    headers={
                        "User-Agent": "CumplimientoRD-Geobancas/1.0 (OSM layer generator)",
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=270) as response:
                    payload = json.load(response)
                if not isinstance(payload.get("elements"), list):
                    raise RuntimeError("Overpass respondió sin elements")
                return payload
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                print(f"[warn] {endpoint} intento {attempt}/3: {exc}", file=sys.stderr)
                time.sleep(attempt * 4)

    raise RuntimeError(f"No se pudo consultar Overpass: {last_error}")


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
    parts = [p for p in [street, number] if p]
    return " ".join(parts)


def category(tags: dict) -> str:
    building = clean(tags.get("building")).lower()
    religion = clean(tags.get("religion")).lower()
    if building == "chapel":
        return "Capilla"
    if building == "church":
        return "Iglesia"
    if religion == "christian":
        return "Iglesia cristiana"
    if religion:
        return "Lugar de culto"
    return "Lugar de culto"


def normalize(elements: list[dict]) -> list[dict]:
    seen: set[str] = set()
    records: list[dict] = []

    for element in elements:
        osm_type = clean(element.get("type"))
        osm_id = element.get("id")
        uid = f"{osm_type}/{osm_id}"
        if uid in seen:
            continue
        seen.add(uid)

        lat, lon = coord(element)
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue

        # Cinturón de seguridad geográfico; el filtro principal es el área OSM DO.
        if not (17.45 <= lat <= 20.15 and -72.05 <= lon <= -68.20):
            continue

        tags = element.get("tags") or {}
        name = (
            clean(tags.get("name"))
            or clean(tags.get("name:es"))
            or clean(tags.get("official_name"))
            or "Lugar de culto sin nombre"
        )

        religion = clean(tags.get("religion"))
        denomination = clean(tags.get("denomination"))
        city = clean(tags.get("addr:city") or tags.get("addr:town") or tags.get("addr:village"))
        municipality = clean(tags.get("addr:municipality"))
        province = clean(tags.get("addr:province") or tags.get("addr:state"))
        phone = clean(tags.get("contact:phone") or tags.get("phone"))
        website = clean(tags.get("contact:website") or tags.get("website"))

        records.append(
            {
                "id": f"IGL-OSM-{osm_type.upper()}-{osm_id}",
                "nombre": name,
                "categoria": category(tags),
                "religion": religion,
                "denominacion": denomination,
                "direccion": address(tags),
                "ciudad": city,
                "municipio": municipality,
                "provincia": province,
                "telefono": phone,
                "website": website,
                "lat": round(float(lat), 7),
                "lon": round(float(lon), 7),
                "osm_type": osm_type,
                "osm_id": osm_id,
                "osm_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
                "fuente": "OpenStreetMap",
                "validada": False,
                "incorporada": "pendiente",
            }
        )

    # Orden estable para evitar commits ruidosos.
    records.sort(key=lambda r: (r["nombre"].casefold(), r["id"]))
    return records


def write_files(records: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    religions: dict[str, int] = {}
    categories: dict[str, int] = {}
    named = 0
    for r in records:
        rel = r["religion"] or "sin_especificar"
        religions[rel] = religions.get(rel, 0) + 1
        cat = r["categoria"]
        categories[cat] = categories.get(cat, 0) + 1
        if r["nombre"] != "Lugar de culto sin nombre":
            named += 1

    output = {
        "meta": {
            "total": len(records),
            "con_nombre": named,
            "sin_nombre": len(records) - named,
            "source": "OpenStreetMap via Overpass API",
            "license": "ODbL 1.0",
            "generated_at": generated_at,
            "country": "República Dominicana",
            "legal_notice": "Detectada geográficamente; incorporada legalmente requiere validación documental.",
            "religiones": dict(sorted(religions.items())),
            "categorias": dict(sorted(categories.items())),
        },
        "records": records,
    }
    JSON_PATH.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    features = []
    for r in records:
        props = {k: v for k, v in r.items() if k not in {"lat", "lon"}}
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                "properties": props,
            }
        )
    geojson = {
        "type": "FeatureCollection",
        "name": "iglesias_rd_osm",
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        "generated_at": generated_at,
        "features": features,
    }
    GEOJSON_PATH.write_text(json.dumps(geojson, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"Generados {len(records)} lugares de culto")
    print(JSON_PATH)
    print(GEOJSON_PATH)


def main() -> int:
    payload = fetch_overpass()
    records = normalize(payload["elements"])
    if not records:
        raise RuntimeError("La extracción devolvió 0 registros; se cancela para no reemplazar datos válidos.")
    write_files(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
