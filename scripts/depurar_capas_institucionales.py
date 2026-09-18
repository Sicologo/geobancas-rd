#!/usr/bin/env python3
"""Depura las capas institucionales generadas desde OSM.

- Recupera variantes de nombre del Palacio/Congreso Nacional.
- Completa candidatos de Cámara de Cuentas / Junta Monetaria si OSM los tiene.
- Reduce órganos extrapoder a una sede candidata por institución, prefiriendo
  el objeto con mejor información de contacto/dirección.

No convierte un candidato OSM en validación jurídica oficial.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data"
CAPITAL = (18.38, 18.58, -70.08, -69.78)
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

QUERY = r'''[out:json][timeout:60];
area["ISO3166-1"="DO"][admin_level=2]->.rd;
(
  nwr["name"~"Congreso Nacional",i](area.rd);
  nwr["official_name"~"Congreso Nacional",i](area.rd);
  nwr["name"~"C.mara de Cuentas|Junta Monetaria",i](area.rd);
  nwr["official_name"~"C.mara de Cuentas|Junta Monetaria",i](area.rd);
);
out center tags;'''


def clean(v):
    return str(v or "").strip()


def coord(e):
    if e.get("type") == "node":
        return e.get("lat"), e.get("lon")
    c = e.get("center") or {}
    return c.get("lat"), c.get("lon")


def inside(lat, lon):
    a,b,c,d = CAPITAL
    return a <= lat <= b and c <= lon <= d


def address(t):
    if clean(t.get("addr:full")):
        return clean(t.get("addr:full"))
    return " ".join(x for x in [clean(t.get("addr:street")), clean(t.get("addr:housenumber"))] if x)


def fetch():
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    last = None
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(ep, data=body, headers={
                "User-Agent":"CumplimientoRD-Geobancas/2.1 institutional-cleanup",
                "Accept":"application/json",
                "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            }, method="POST")
            with urllib.request.urlopen(req, timeout=75) as r:
                return json.load(r).get("elements", [])
        except Exception as exc:
            last = exc
            time.sleep(2)
    print(f"[warn] no se pudo consultar OSM para depuración: {last}")
    return []


def record(e, prefix, category):
    t = e.get("tags") or {}
    lat, lon = coord(e)
    if not isinstance(lat,(int,float)) or not isinstance(lon,(int,float)):
        return None
    lat,lon=float(lat),float(lon)
    if not inside(lat,lon):
        return None
    typ, oid = clean(e.get("type")), e.get("id")
    name = clean(t.get("name") or t.get("name:es") or t.get("official_name"))
    return {
        "id":f"{prefix}-OSM-{typ.upper()}-{oid}",
        "nombre":name,
        "categoria":category,
        "direccion":address(t),
        "ciudad":clean(t.get("addr:city") or t.get("addr:town") or t.get("addr:village")),
        "provincia":clean(t.get("addr:province") or t.get("addr:state")),
        "telefono":clean(t.get("contact:phone") or t.get("phone")),
        "website":clean(t.get("contact:website") or t.get("website")),
        "lat":round(lat,7),"lon":round(lon,7),
        "osm_type":typ,"osm_id":oid,
        "osm_url":f"https://www.openstreetmap.org/{typ}/{oid}",
        "fuente":"OpenStreetMap","validada":False,
        "sede_principal_validada":False,"validacion_institucional":"pendiente",
    }


def richness(r):
    return 4*bool(r.get("website")) + 3*bool(r.get("direccion")) + 2*bool(r.get("telefono")) + bool(r.get("ciudad"))


def canonical(name):
    n=name.casefold()
    if "cámara de cuentas" in n or "camara de cuentas" in n: return "Cámara de Cuentas"
    if "junta monetaria" in n: return "Junta Monetaria"
    if "banco central" in n: return "Banco Central de la República Dominicana"
    if "defensor del pueblo" in n: return "Defensor del Pueblo"
    if "junta central electoral" in n: return "Junta Central Electoral"
    if "tribunal constitucional" in n: return "Tribunal Constitucional"
    if "tribunal superior electoral" in n: return "Tribunal Superior Electoral"
    return name.strip()


def write(path, meta, records, geo_name):
    meta=dict(meta)
    meta["total"]=len(records)
    meta["con_nombre"]=sum(bool(r.get("nombre")) for r in records)
    meta["sin_nombre"]=len(records)-meta["con_nombre"]
    path.write_text(json.dumps({"meta":meta,"records":records},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    feats=[{"type":"Feature","geometry":{"type":"Point","coordinates":[r["lon"],r["lat"]]},"properties":{k:v for k,v in r.items() if k not in {"lat","lon"}}} for r in records]
    (path.with_suffix(".geojson")).write_text(json.dumps({"type":"FeatureCollection","name":geo_name,"attribution":"© OpenStreetMap contributors, ODbL 1.0","generated_at":meta.get("generated_at"),"features":feats},ensure_ascii=False,separators=(",",":")),encoding="utf-8")


def main():
    elements=fetch()

    # Poderes del Estado: preservar Ejecutivo/Judicial y recuperar Congreso con cualquier variante de nombre.
    p=DATA/"sedes_poderes_estado.json"
    d=json.loads(p.read_text(encoding="utf-8"))
    records=list(d.get("records",[]))
    if not any("congreso nacional" in r.get("nombre","").casefold() for r in records):
        candidates=[]
        for e in elements:
            t=e.get("tags") or {}
            nm=clean(t.get("name") or t.get("official_name"))
            if "congreso nacional" not in nm.casefold():
                continue
            r=record(e,"POD","Sedes principales de los poderes del Estado")
            if r: candidates.append(r)
        if candidates:
            best=max(candidates,key=richness)
            best["nombre"]="Congreso Nacional"
            records.append(best)
    # una sede física por los tres poderes, orden estable
    def power_key(r):
        n=r.get("nombre","").casefold()
        if "palacio nacional" in n: return 0
        if "congreso nacional" in n: return 1
        if "suprema corte" in n: return 2
        return 9
    records=sorted(records,key=lambda r:(power_key(r),r.get("nombre","")))
    write(p,d.get("meta",{}),records,"sedes_poderes_estado_rd")

    # Extrapoder: agregar variantes recuperadas y quedarse con una sede candidata por institución.
    p=DATA/"organos_extrapoder.json"
    d=json.loads(p.read_text(encoding="utf-8"))
    records=list(d.get("records",[]))
    for e in elements:
        t=e.get("tags") or {}
        nm=clean(t.get("name") or t.get("official_name"))
        canon=canonical(nm)
        if canon not in {"Cámara de Cuentas","Junta Monetaria"}:
            continue
        r=record(e,"EXT","Órganos extrapoder / constitucionales autónomos")
        if not r: continue
        r["nombre"]=canon
        r["clasificacion_juridica"]="candidato_extrapoder"
        records.append(r)

    grouped={}
    for r in records:
        canon=canonical(r.get("nombre",""))
        if not canon: continue
        rr=dict(r); rr["nombre"]=canon
        old=grouped.get(canon)
        if old is None or richness(rr)>richness(old):
            grouped[canon]=rr
    records=sorted(grouped.values(),key=lambda r:r["nombre"].casefold())
    write(p,d.get("meta",{}),records,"organos_extrapoder_rd")
    print("sedes_poderes_estado:", len(json.loads((DATA/"sedes_poderes_estado.json").read_text(encoding="utf-8"))["records"]))
    print("organos_extrapoder:", len(records))

if __name__=="__main__":
    main()
