#!/usr/bin/env python3
"""Completa sedes críticas que pueden faltar por etiquetado incompleto en OSM.

Las coordenadas del Congreso se apoyan en el inventario arquitectónico del
Centro de los Héroes (2022) y la dirección oficial de Cámara/Senado.
La Cámara de Cuentas usa el objeto OSM way/176728114, contrastado con su
dirección institucional. La Junta Monetaria comparte sede con la oficina
principal del Banco Central, por lo que se registra como órgano alojado en
esa misma sede física en vez de duplicar el punto.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data"


def write_layer(stem: str, data: dict) -> None:
    records = data["records"]
    data["meta"]["total"] = len(records)
    data["meta"]["con_nombre"] = sum(bool(r.get("nombre")) for r in records)
    data["meta"]["sin_nombre"] = len(records) - data["meta"]["con_nombre"]
    (DATA / f"{stem}.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    features = []
    for r in records:
        props = {k: v for k, v in r.items() if k not in {"lat", "lon"}}
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": props,
        })
    geo = {
        "type": "FeatureCollection",
        "name": f"{stem}_rd",
        "attribution": "© OpenStreetMap contributors, ODbL 1.0; sedes institucionales contrastadas con fuentes oficiales",
        "generated_at": data["meta"].get("generated_at"),
        "features": features,
    }
    (DATA / f"{stem}.geojson").write_text(
        json.dumps(geo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


def add_congreso() -> None:
    stem = "sedes_poderes_estado"
    p = DATA / f"{stem}.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    records = data.get("records", [])
    if not any("congreso nacional" in r.get("nombre", "").casefold() for r in records):
        records.append({
            "id": "POD-OFFICIAL-CONGRESO-NACIONAL",
            "nombre": "Congreso Nacional",
            "categoria": "Sedes principales de los poderes del Estado",
            "direccion": "Av. Enrique Jiménez Moya esq. Juan de Dios Ventura Simó, Centro de los Héroes, Distrito Nacional",
            "ciudad": "Santo Domingo de Guzmán",
            "provincia": "Distrito Nacional",
            "telefono": "809-532-5561",
            "website": "https://www.senadord.gob.do/",
            "lat": 18.44850,
            "lon": -69.92666,
            "osm_type": "",
            "osm_id": None,
            "osm_url": "",
            "fuente": "Cámara de Diputados / Senado RD + inventario arquitectónico Centro de los Héroes 2022",
            "fuente_institucional": "https://www.senadord.gob.do/contacto/",
            "fuente_coordenada": "Inventario arquitectónico Centro de los Héroes 2022",
            "validada": True,
            "sede_principal_validada": True,
            "validacion_institucional": "dirección_oficial_verificada",
        })
    order = {"Palacio Nacional": 0, "Congreso Nacional": 1, "Suprema Corte de Justicia": 2}
    records.sort(key=lambda r: (order.get(r.get("nombre", ""), 9), r.get("nombre", "")))
    data["records"] = records
    data["meta"]["legal_notice"] = (
        "Incluye las sedes principales de los poderes Ejecutivo, Legislativo y Judicial. "
        "Congreso Nacional se completa con dirección institucional oficial y coordenada de inventario arquitectónico."
    )
    write_layer(stem, data)


def add_camara_cuentas_and_jm() -> None:
    stem = "organos_extrapoder"
    p = DATA / f"{stem}.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    records = data.get("records", [])

    # La Junta Monetaria tiene domicilio en la oficina principal del Banco Central.
    for r in records:
        if "banco central" in r.get("nombre", "").casefold():
            r["organos_en_sede"] = ["Banco Central de la República Dominicana", "Junta Monetaria"]
            r["fuente_junta_monetaria"] = "Reglamento Interno de la Junta Monetaria / domicilio en oficina principal del Banco Central"
            r["validacion_institucional"] = "sede_compartida_verificada"

    if not any("cámara de cuentas" in r.get("nombre", "").casefold() or "camara de cuentas" in r.get("nombre", "").casefold() for r in records):
        records.append({
            "id": "EXT-OSM-WAY-176728114",
            "nombre": "Cámara de Cuentas de la República Dominicana",
            "categoria": "Órganos extrapoder / constitucionales autónomos",
            "direccion": "Ave. 27 de Febrero esq. Abreu, Edificio Gubernamental Manuel Fernández Mármol, San Carlos, Santo Domingo",
            "ciudad": "Santo Domingo de Guzmán",
            "provincia": "Distrito Nacional",
            "telefono": "809-682-3290",
            "website": "https://www.camaradecuentas.gob.do/",
            "lat": 18.48315,
            "lon": -69.89378,
            "osm_type": "way",
            "osm_id": 176728114,
            "osm_url": "https://www.openstreetmap.org/way/176728114",
            "fuente": "OpenStreetMap + Cámara de Cuentas RD",
            "fuente_institucional": "https://camaradecuentas.gob.do/",
            "validada": True,
            "sede_principal_validada": True,
            "clasificacion_juridica": "candidato_extrapoder",
            "validacion_institucional": "dirección_oficial_y_objeto_osm_contrastados",
        })

    records.sort(key=lambda r: r.get("nombre", "").casefold())
    data["records"] = records
    data["meta"]["legal_notice"] = (
        "Capa de sedes de órganos constitucionales/autónomos tratadas como candidatos de la categoría reglamentaria 'órganos extrapoder'. "
        "La Cámara de Cuentas se contrasta con dirección oficial; la Junta Monetaria comparte sede física con el Banco Central."
    )
    write_layer(stem, data)


def main() -> None:
    add_congreso()
    add_camara_cuentas_and_jm()
    print("sedes oficiales críticas completadas")


if __name__ == "__main__":
    main()
